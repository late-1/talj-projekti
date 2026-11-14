import pytest
from sqlalchemy import text

from config import db
from repositories import user_repository
from util import UserInputError


def test_create_user_returns_user():
    user = user_repository.create_user("maija", "secret-password")
    assert user.username == "maija"
    assert user.id is not None


def test_password_is_stored_as_hash():
    user_repository.create_user("maija", "secret-password")
    password_hash = db.session.execute(text("SELECT password_hash FROM users")).scalar()
    assert password_hash != "secret-password"
    assert "secret-password" not in password_hash


def test_username_must_be_unique():
    user_repository.create_user("maija", "secret-password")
    with pytest.raises(UserInputError, match="already in use"):
        user_repository.create_user("maija", "other-password")
    assert db.session.execute(text("SELECT COUNT(*) FROM users")).scalar() == 1


def test_users_get_different_ids():
    first = user_repository.create_user("maija", "secret-password")
    second = user_repository.create_user("uolevi", "secret-password")
    assert first.id != second.id


def test_get_user():
    created = user_repository.create_user("maija", "secret-password")
    user = user_repository.get_user(created.id)
    assert user.id == created.id
    assert user.username == "maija"


def test_get_unknown_user():
    assert user_repository.get_user(123) is None


def test_check_login_with_correct_credentials():
    created = user_repository.create_user("maija", "secret-password")
    user = user_repository.check_login("maija", "secret-password")
    assert user.id == created.id
    assert user.username == "maija"


def test_check_login_with_wrong_password():
    user_repository.create_user("maija", "secret-password")
    assert user_repository.check_login("maija", "wrong-password") is None


def test_check_login_with_unknown_user():
    assert user_repository.check_login("maija", "secret-password") is None


def test_check_login_uses_the_password_of_the_given_user():
    user_repository.create_user("maija", "secret-password")
    user_repository.create_user("uolevi", "other-password")
    assert user_repository.check_login("maija", "other-password") is None
