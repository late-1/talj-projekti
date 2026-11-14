from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from config import db
from entities.user import User
from util import UserInputError


def create_user(username, password):
    sql = text(
        "INSERT INTO users (username, password_hash) "
        "VALUES (:username, :password_hash)"
    )
    params = {
        "username": username,
        "password_hash": generate_password_hash(password),
    }

    try:
        result = db.session.execute(sql, params)
        db.session.commit()
    except IntegrityError as error:
        db.session.rollback()
        raise UserInputError("Username already in use, pick another one") from error

    return User(result.lastrowid, username)


def get_user(user_id):
    sql = text("SELECT id, username FROM users WHERE id = :id")
    row = db.session.execute(sql, {"id": user_id}).fetchone()
    return User(row[0], row[1]) if row else None


def check_login(username, password):
    """Returns the user when the credentials are correct, otherwise None"""
    sql = text("SELECT id, username, password_hash FROM users WHERE username = :username")
    row = db.session.execute(sql, {"username": username}).fetchone()

    if not row or not check_password_hash(row[2], password):
        return None

    return User(row[0], row[1])
