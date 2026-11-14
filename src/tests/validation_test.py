import pytest

from util import UserInputError, validate_password, validate_username


@pytest.mark.parametrize("username", ["abc", "a" * 30, "maija", "Maija_M-1.2"])
def test_valid_username_is_accepted(username):
    validate_username(username)


@pytest.mark.parametrize("username", ["", "ab", "a" * 31])
def test_username_with_wrong_length_is_rejected(username):
    with pytest.raises(UserInputError, match="3-30 characters"):
        validate_username(username)


@pytest.mark.parametrize("username", ["maija m", "maija!", "<b>maija</b>", "mäijä"])
def test_username_with_invalid_characters_is_rejected(username):
    with pytest.raises(UserInputError, match="can only contain"):
        validate_username(username)


@pytest.mark.parametrize("password", ["a" * 8, "a" * 100, "pass word 123!"])
def test_valid_password_is_accepted(password):
    validate_password(password, password)


@pytest.mark.parametrize("password", ["", "a" * 7, "a" * 101])
def test_password_with_wrong_length_is_rejected(password):
    with pytest.raises(UserInputError, match="8-100 characters"):
        validate_password(password, password)


def test_passwords_must_match():
    with pytest.raises(UserInputError, match="do not match"):
        validate_password("secret-password", "secret-passwore")
