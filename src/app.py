import secrets
from functools import wraps
from urllib.parse import urlencode

from flask import (
    Response, abort, flash, jsonify, redirect, render_template, request, session,
)

import bibtex
import citation
import reference_types
import util
from config import app, test_env
from db_helper import reset_db
from repositories import reference_repository, user_repository
from util import UserInputError


def login_required(view):
    """Redirects users who are not logged in to the login page"""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect("/login")
        # the account may have been removed after the session was started
        if not user_repository.get_user(session["user_id"]):
            session.clear()
            return redirect("/login")
        return view(*args, **kwargs)
    return wrapped


def check_csrf():
    token = request.form.get("csrf_token")
    if not token or token != session.get("csrf_token"):
        abort(403)


def get_back_url(back):
    """
    Address of the list the user came from, including the search.
    Only addresses of the list page are accepted.
    """
    if back.endswith("?"):
        back = back[:-1]
    if back == "/references" or back.startswith("/references?"):
        return back
    return "/references"


def start_session(user):
    session.clear()
    session["user_id"] = user.id
    session["username"] = user.username
    session["csrf_token"] = secrets.token_hex(16)


@app.context_processor
def template_constants():
    return {"limits": util, "reference_types": reference_types}


@app.route("/")
def index():
    if "user_id" not in session:
        return redirect("/login")
    return redirect("/references")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        if "user_id" in session:
            return redirect("/")
        return render_template("login.html", username="")

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    user = user_repository.check_login(username, password)
    if not user:
        flash("Wrong username or password")
        return render_template("login.html", username=username)

    start_session(user)
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        if "user_id" in session:
            return redirect("/")
        return render_template("register.html", username="")

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    password_confirmation = request.form.get("password_confirmation", "")

    try:
        util.validate_username(username)
        util.validate_password(password, password_confirmation)
        user = user_repository.create_user(username, password)
    except UserInputError as error:
        flash(str(error))
        return render_template("register.html", username=username)

    start_session(user)
    return redirect("/")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


def find_unconfirmed_duplicate(entry_type, fields, exclude_id=None):
    """
    An existing reference with the same content, unless the user has already
    answered add (or save) in the dialog about it
    """
    if request.form.get("confirm_duplicate") == "yes":
        return None
    return reference_repository.find_duplicate(
        session["user_id"], entry_type, fields, exclude_id
    )


@app.route("/add", methods=["GET", "POST"])
@login_required
def add_reference():
    if request.method == "GET":
        entry_type = request.args.get("type")
        if entry_type not in reference_types.ENTRY_TYPES:
            entry_type = reference_types.DEFAULT_ENTRY_TYPE
        return render_template(
            "add_reference.html", entry_type=entry_type, values={}, cite_key="",
        )

    check_csrf()

    entry_type = request.form.get("entry_type", "")
    cite_key = request.form.get("cite_key", "").strip()

    try:
        fields = util.validate_reference(entry_type, request.form)
        if cite_key:
            util.validate_cite_key(cite_key)
        duplicate = find_unconfirmed_duplicate(entry_type, fields)
        if duplicate:
            # the form is shown again with a dialog that asks whether to add it anyway
            return render_template(
                "add_reference.html", entry_type=entry_type, values=request.form,
                cite_key=cite_key, duplicate=duplicate,
            )
        reference = reference_repository.create_reference(
            session["user_id"], entry_type, fields, cite_key
        )
    except UserInputError as error:
        flash(str(error))
        if entry_type not in reference_types.ENTRY_TYPES:
            entry_type = reference_types.DEFAULT_ENTRY_TYPE
        return render_template(
            "add_reference.html",
            entry_type=entry_type, values=request.form, cite_key=cite_key,
        )

    flash(f"Reference added with the key {reference.cite_key}", "notice")
    # the form stays on the same type, which helps when adding several references
    return redirect(f"/add?type={entry_type}")


@app.route("/references")
@login_required
def list_references():
    search = util.clean_search_params(request.args)

    # empty search fields are dropped from the address
    if search != request.args.to_dict():
        return redirect("/references?" + urlencode(search) if search else "/references")

    filters, errors = util.search_filters(search)
    for error in errors:
        flash(error)

    query = search.get("query", "")
    references = reference_repository.get_references(session["user_id"], query, filters)
    total = reference_repository.count_references(session["user_id"])

    return render_template(
        "references.html",
        references=references,
        total=total,
        search=search,
        searching=bool(search),
        advanced_open=any(name in search for name in util.ADVANCED_SEARCH_PARAMS),
    )


def reference_url(reference_id, back, action=""):
    """Address of a page of one reference; remembers the list the user came from"""
    url = f"/references/{reference_id}{action}"
    if back != "/references":
        url += "?" + urlencode({"back": back})
    return url


def get_own_reference(reference_id):
    # other users' references look the same as missing ones
    reference = reference_repository.get_reference(session["user_id"], reference_id)
    if not reference:
        abort(404)
    return reference


def render_reference(reference, back, edit_form=None):
    """
    The BibTeX page: the BibTeX and below it the citation and the fields of the
    reference. With edit_form, the edit form is shown above the BibTeX.
    """
    return render_template(
        "show_reference.html",
        reference=reference,
        bibtex=bibtex.to_bibtex(reference),
        citation=citation.to_citation(reference),
        labels=reference_types.SHORT_LABELS,
        back=back,
        show_url=reference_url(reference.id, back),
        edit_url=reference_url(reference.id, back, "/edit"),
        delete_url=reference_url(reference.id, back, "/delete"),
        editing=edit_form is not None,
        **(edit_form or {}),
    )


@app.route("/references/<int:reference_id>")
@login_required
def show_reference(reference_id):
    reference = get_own_reference(reference_id)
    return render_reference(reference, get_back_url(request.args.get("back", "")))


@app.route("/references/<int:reference_id>/edit", methods=["GET", "POST"])
@login_required
def edit_reference(reference_id):
    reference = get_own_reference(reference_id)
    back = get_back_url(request.args.get("back", ""))

    if request.method == "GET":
        return render_reference(reference, back, {
            "entry_type": reference.entry_type,
            "values": reference.fields,
            "cite_key": reference.cite_key,
        })

    check_csrf()

    entry_type = request.form.get("entry_type", "")
    cite_key = request.form.get("cite_key", "").strip()

    try:
        fields = util.validate_reference(entry_type, request.form)
        if cite_key:
            util.validate_cite_key(cite_key)
        duplicate = find_unconfirmed_duplicate(entry_type, fields, exclude_id=reference_id)
        if duplicate:
            return render_reference(reference, back, {
                "entry_type": entry_type, "values": request.form, "cite_key": cite_key,
                "duplicate": duplicate,
            })
        reference_repository.update_reference(
            session["user_id"], reference_id, entry_type, fields, cite_key
        )
    except UserInputError as error:
        flash(str(error))
        if entry_type not in reference_types.ENTRY_TYPES:
            entry_type = reference.entry_type
        # the form stays open with the values the user gave
        return render_reference(reference, back, {
            "entry_type": entry_type, "values": request.form, "cite_key": cite_key,
        })

    return redirect(reference_url(reference_id, back))


@app.route("/references/<int:reference_id>/delete", methods=["POST"])
@login_required
def delete_reference(reference_id):
    check_csrf()
    reference = get_own_reference(reference_id)
    reference_repository.delete_reference(session["user_id"], reference_id)

    flash(f"Reference {reference.cite_key} deleted", "notice")
    return redirect(get_back_url(request.args.get("back", "")))


@app.route("/references/delete", methods=["POST"])
@login_required
def delete_selected_references():
    """Deletes the references selected on the list and returns to the same list"""
    check_csrf()
    back = get_back_url(request.form.get("back", ""))

    ids = util.selected_ids(request.form.getlist("reference_id"))
    if not ids:
        flash("No references selected")
        return redirect(back)

    count = reference_repository.delete_references(session["user_id"], ids)
    if count == 0:
        flash("No references deleted")
    else:
        flash(f"{count} {'reference' if count == 1 else 'references'} deleted", "notice")
    return redirect(back)


@app.route("/references/bib", methods=["POST"])
@login_required
def create_bib_file():
    """Returns the references selected on the list as a .bib file to download"""
    check_csrf()
    back = get_back_url(request.form.get("back", ""))

    ids = util.selected_ids(request.form.getlist("reference_id"))
    references = reference_repository.get_references_by_ids(session["user_id"], ids)
    if not references:
        flash("No references selected")
        return redirect(back)

    content = "\n\n".join(bibtex.to_bibtex(reference) for reference in references) + "\n"
    return Response(
        content,
        mimetype="application/x-bibtex",
        headers={"Content-Disposition": 'attachment; filename="references.bib"'},
    )


# route for tests only
if test_env:
    @app.route("/reset_db")
    def reset_database():
        reset_db()
        session.clear()
        return jsonify({"message": "db reset"})
