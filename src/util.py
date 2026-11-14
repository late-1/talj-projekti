import re

USERNAME_MIN_LENGTH = 3
USERNAME_MAX_LENGTH = 30
PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 100

USERNAME_PATTERN = re.compile(r"[A-Za-z0-9_.-]+")


class UserInputError(Exception):
    pass


def validate_username(username):
    if not USERNAME_MIN_LENGTH <= len(username) <= USERNAME_MAX_LENGTH:
        raise UserInputError(
            f"Username must be {USERNAME_MIN_LENGTH}-{USERNAME_MAX_LENGTH} characters long"
        )

    if not USERNAME_PATTERN.fullmatch(username):
        raise UserInputError(
            "Username can only contain letters, numbers and the characters _ - ."
        )


def validate_password(password, password_confirmation):
    if not PASSWORD_MIN_LENGTH <= len(password) <= PASSWORD_MAX_LENGTH:
        raise UserInputError(
            f"Password must be {PASSWORD_MIN_LENGTH}-{PASSWORD_MAX_LENGTH} characters long"
        )

    if password != password_confirmation:
        raise UserInputError("Passwords do not match")
