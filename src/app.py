import secrets
from functools import wraps

from flask import abort, flash, jsonify, redirect, render_template, request, session

import util
from config import app, test_env
from db_helper import reset_db
from repositories import user_repository
from util import UserInputError


def login_required(view):
    """Redirects users who are not logged in to the login page"""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect("/login")
        return view(*args, **kwargs)
    return wrapped


def check_csrf():
    token = request.form.get("csrf_token")
    if not token or token != session.get("csrf_token"):
        abort(403)


def start_session(user):
    session.clear()
    session["user_id"] = user.id
    session["username"] = user.username
    session["csrf_token"] = secrets.token_hex(16)


@app.context_processor
def template_constants():
    return {"limits": util}


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


@app.route("/add")
@login_required
def add_reference():
    return render_template("add_reference.html")


@app.route("/references")
@login_required
def list_references():
    return render_template("references.html")


# route for tests only
if test_env:
    @app.route("/reset_db")
    def reset_database():
        reset_db()
        session.clear()
        return jsonify({"message": "db reset"})
