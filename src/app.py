import secrets
from functools import wraps

from flask import abort, flash, jsonify, redirect, render_template, request, session

import bibtex
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
    query = " ".join(request.args.get("query", "").split())[:util.SEARCH_MAX_LENGTH]
    references = reference_repository.get_references(session["user_id"], query)
    total = len(references) if not query \
        else reference_repository.count_references(session["user_id"])
    return render_template(
        "references.html", references=references, query=query, total=total,
    )


@app.route("/references/<int:reference_id>")
@login_required
def show_reference(reference_id):
    # other users' references look the same as missing ones
    reference = reference_repository.get_reference(session["user_id"], reference_id)
    if not reference:
        abort(404)

    return render_template(
        "show_reference.html",
        reference=reference,
        bibtex=bibtex.to_bibtex(reference),
        back=get_back_url(request.args.get("back", "")),
    )


# route for tests only
if test_env:
    @app.route("/reset_db")
    def reset_database():
        reset_db()
        session.clear()
        return jsonify({"message": "db reset"})
