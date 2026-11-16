from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from config import db
from entities.reference import Reference
from reference_types import FIELDS
from util import UserInputError, cite_key_candidates

COLUMNS = ["id", "user_id", "entry_type", "cite_key"] + list(FIELDS)


def _to_reference(row):
    values = dict(zip(COLUMNS, row))
    return Reference(
        values["id"], values["user_id"], values["entry_type"], values["cite_key"], values
    )


def get_cite_keys(user_id):
    sql = text("SELECT cite_key FROM bib_references WHERE user_id = :user_id")
    result = db.session.execute(sql, {"user_id": user_id})
    return {row[0] for row in result.fetchall()}


def generate_cite_key(user_id, author, year):
    """Returns a key such as martin2008 that the user does not have yet"""
    used_keys = get_cite_keys(user_id)
    for candidate in cite_key_candidates(author, year):
        if candidate not in used_keys:
            return candidate
    return None


def create_reference(user_id, entry_type, fields, cite_key=None):
    """
    Stores a validated reference. When the key is not given, it is generated
    from the first author and the year.
    """
    if not cite_key:
        cite_key = generate_cite_key(user_id, fields["author"], fields["year"])

    names = [name for name in FIELDS if name in fields]
    columns = ", ".join(["user_id", "entry_type", "cite_key"] + names)
    placeholders = ", ".join([":user_id", ":entry_type", ":cite_key"] + [f":{n}" for n in names])
    sql = text(f"INSERT INTO bib_references ({columns}) VALUES ({placeholders})")

    params = {name: fields[name] for name in names}
    params.update({"user_id": user_id, "entry_type": entry_type, "cite_key": cite_key})

    try:
        result = db.session.execute(sql, params)
        db.session.commit()
    except IntegrityError as error:
        db.session.rollback()
        if "UNIQUE" not in str(error.orig):
            raise
        raise UserInputError(f"Key {cite_key} is already in use, pick another one") from error

    return Reference(result.lastrowid, user_id, entry_type, cite_key, fields)


def get_references(user_id):
    """Returns the references of the user, newest first"""
    sql = text(
        f"SELECT {', '.join(COLUMNS)} FROM bib_references "
        "WHERE user_id = :user_id ORDER BY id DESC"
    )
    result = db.session.execute(sql, {"user_id": user_id})
    return [_to_reference(row) for row in result.fetchall()]


def get_reference(user_id, reference_id):
    """Returns the reference only when it belongs to the user, otherwise None"""
    sql = text(
        f"SELECT {', '.join(COLUMNS)} FROM bib_references "
        "WHERE id = :id AND user_id = :user_id"
    )
    row = db.session.execute(sql, {"id": reference_id, "user_id": user_id}).fetchone()
    return _to_reference(row) if row else None
