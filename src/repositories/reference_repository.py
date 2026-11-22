from sqlalchemy import bindparam, text
from sqlalchemy.exc import IntegrityError

from config import db
from entities.reference import Reference
from reference_types import FIELDS
from util import UserInputError, cite_key_candidates, search_words

COLUMNS = ["id", "user_id", "entry_type", "cite_key"] + list(FIELDS)

# Everything that the search looks at: the type, the key and all the fields.
# The values are joined with line breaks, so a word cannot match over two fields.
def _search_text(columns):
    joined = " || char(10) || ".join(f"coalesce({column}, '')" for column in columns)
    return f"casefold({joined})"


SEARCH_TEXT = _search_text(["entry_type", "cite_key"] + list(FIELDS))

# What the text fields of the advanced search look at
FILTER_TEXTS = {
    "author": _search_text(["author"]),
    "title": _search_text(["title"]),
    "venue": _search_text(["journal", "booktitle", "publisher"]),
    "key": _search_text(["cite_key"]),
}


def _to_reference(row):
    values = dict(zip(COLUMNS, row))
    return Reference(
        values["id"], values["user_id"], values["entry_type"], values["cite_key"], values
    )


def get_cite_keys(user_id, exclude_id=None):
    """Keys of the user; the reference that is being edited can be left out"""
    sql = text(
        "SELECT cite_key FROM bib_references "
        "WHERE user_id = :user_id AND (:exclude_id IS NULL OR id != :exclude_id)"
    )
    result = db.session.execute(sql, {"user_id": user_id, "exclude_id": exclude_id})
    return {row[0] for row in result.fetchall()}


def generate_cite_key(user_id, author, year, exclude_id=None):
    """Returns a key such as martin2008 that the user does not have yet"""
    used_keys = get_cite_keys(user_id, exclude_id)
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


def update_reference(user_id, reference_id, entry_type, fields, cite_key=None):
    """
    Replaces the content of a reference of the user with validated values.
    Fields that are not given are emptied. When the key is not given, it is
    generated again. Returns None when the user has no such reference.
    """
    if not cite_key:
        cite_key = generate_cite_key(
            user_id, fields["author"], fields["year"], exclude_id=reference_id
        )

    assignments = ", ".join(
        ["entry_type = :entry_type", "cite_key = :cite_key"] + [f"{n} = :{n}" for n in FIELDS]
    )
    sql = text(
        f"UPDATE bib_references SET {assignments} WHERE id = :id AND user_id = :user_id"
    )

    params = {name: fields.get(name) for name in FIELDS}
    params.update({
        "id": reference_id, "user_id": user_id,
        "entry_type": entry_type, "cite_key": cite_key,
    })

    try:
        result = db.session.execute(sql, params)
        db.session.commit()
    except IntegrityError as error:
        db.session.rollback()
        if "UNIQUE" not in str(error.orig):
            raise
        raise UserInputError(f"Key {cite_key} is already in use, pick another one") from error

    if result.rowcount == 0:
        return None
    return Reference(reference_id, user_id, entry_type, cite_key, fields)


def delete_reference(user_id, reference_id):
    """Deletes a reference of the user. Returns False when there is no such reference."""
    sql = text("DELETE FROM bib_references WHERE id = :id AND user_id = :user_id")
    result = db.session.execute(sql, {"id": reference_id, "user_id": user_id})
    db.session.commit()
    return result.rowcount > 0


def delete_references(user_id, reference_ids):
    """Deletes the given references of the user. Returns how many were deleted."""
    if not reference_ids:
        return 0
    sql = text(
        "DELETE FROM bib_references WHERE user_id = :user_id AND id IN :ids"
    ).bindparams(bindparam("ids", expanding=True))
    result = db.session.execute(sql, {"user_id": user_id, "ids": list(reference_ids)})
    db.session.commit()
    return result.rowcount


def get_references(user_id, query="", filters=None):
    """
    Returns the references of the user, newest first.

    With a search, returns the references that contain every word of the
    search in any of their fields. The filters of the advanced search limit
    the result further, and a reference has to match all of them:
      author, title, venue, key: every word has to be found in that field
      year_from, year_to: the first and the last year that are included
      type: the entry type
    """
    filters = filters or {}
    conditions = ["user_id = :user_id"]
    params = {"user_id": user_id}

    for index, word in enumerate(search_words(query)):
        conditions.append(f"instr({SEARCH_TEXT}, :word{index}) > 0")
        params[f"word{index}"] = word

    for name, searched_text in FILTER_TEXTS.items():
        for index, word in enumerate(search_words(filters.get(name, ""))):
            conditions.append(f"instr({searched_text}, :{name}{index}) > 0")
            params[f"{name}{index}"] = word

    # years are stored as four digits, so they can be compared as text
    if filters.get("year_from"):
        conditions.append("year >= :year_from")
        params["year_from"] = filters["year_from"]

    if filters.get("year_to"):
        conditions.append("year <= :year_to")
        params["year_to"] = filters["year_to"]

    if filters.get("type"):
        conditions.append("entry_type = :type")
        params["type"] = filters["type"]

    sql = text(
        f"SELECT {', '.join(COLUMNS)} FROM bib_references "
        f"WHERE {' AND '.join(conditions)} ORDER BY id DESC"
    )
    result = db.session.execute(sql, params)
    return [_to_reference(row) for row in result.fetchall()]


def count_references(user_id):
    sql = text("SELECT COUNT(*) FROM bib_references WHERE user_id = :user_id")
    return db.session.execute(sql, {"user_id": user_id}).scalar()


def get_reference(user_id, reference_id):
    """Returns the reference only when it belongs to the user, otherwise None"""
    sql = text(
        f"SELECT {', '.join(COLUMNS)} FROM bib_references "
        "WHERE id = :id AND user_id = :user_id"
    )
    row = db.session.execute(sql, {"id": reference_id, "user_id": user_id}).fetchone()
    return _to_reference(row) if row else None
