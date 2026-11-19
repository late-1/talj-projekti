import re
import unicodedata

from reference_types import ENTRY_TYPES, FIELDS, LONG_FIELDS, fields_of

USERNAME_MIN_LENGTH = 3
USERNAME_MAX_LENGTH = 30
PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 100

USERNAME_PATTERN = re.compile(r"[A-Za-z0-9_.-]+")

FIELD_MAX_LENGTH = 200
LONG_FIELD_MAX_LENGTH = 1000
CITE_KEY_MAX_LENGTH = 50
SEARCH_MAX_LENGTH = 200
SEARCH_MAX_WORDS = 20

YEAR_PATTERN = re.compile(r"[0-9]{4}")
CITE_KEY_PATTERN = re.compile(r"[A-Za-z0-9_:.+/-]+")


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


def search_words(query):
    """
    Splits the search into words. Every word has to be found in the reference.
    Upper and lower case letters are equal, and the same word is used only once.
    """
    words = []
    for word in query[:SEARCH_MAX_LENGTH].casefold().split():
        if word not in words:
            words.append(word)
    return words[:SEARCH_MAX_WORDS]


def field_max_length(name):
    return LONG_FIELD_MAX_LENGTH if name in LONG_FIELDS else FIELD_MAX_LENGTH


def field_name(name):
    """Name of the field for error messages, for example 'Book title'"""
    label = FIELDS[name].split(" (")[0].replace("(s)", "")
    return label[0].upper() + label[1:]


def validate_reference(entry_type, form):
    """
    Checks the fields of a new reference.
    Returns the values of the fields that belong to the entry type,
    whitespace removed and empty values left out.
    """
    if entry_type not in ENTRY_TYPES:
        raise UserInputError("Unknown reference type")

    required = ENTRY_TYPES[entry_type]["required"]
    fields = {}

    for name in fields_of(entry_type):
        value = " ".join((form.get(name) or "").split())

        if not value:
            if name in required:
                raise UserInputError(f"{field_name(name)} is required")
            continue

        if len(value) > field_max_length(name):
            raise UserInputError(
                f"{field_name(name)} can be at most {field_max_length(name)} characters long"
            )

        if not has_balanced_braces(value):
            raise UserInputError(
                f"{field_name(name)} has curly braces {{ }} that do not match"
            )

        fields[name] = value

    if not YEAR_PATTERN.fullmatch(fields["year"]):
        raise UserInputError("Year must be a four-digit number")

    return fields


def has_balanced_braces(value):
    """
    Checks that every { has a matching }. Unmatched braces would break the
    BibTeX entry. Braces escaped with a backslash are not counted.
    """
    depth = 0
    for character in re.sub(r"\\.", "", value):
        if character == "{":
            depth += 1
        elif character == "}":
            depth -= 1
            if depth < 0:
                return False
    return depth == 0


def validate_cite_key(cite_key):
    if len(cite_key) > CITE_KEY_MAX_LENGTH:
        raise UserInputError(f"Key can be at most {CITE_KEY_MAX_LENGTH} characters long")

    if not CITE_KEY_PATTERN.fullmatch(cite_key):
        raise UserInputError(
            "Key can only contain letters a-z, numbers and the characters _ - : . + /"
        )


def first_author_last_name(author):
    """
    Returns the last name of the first author. Understands the BibTeX name
    formats 'Last, First' and 'First Last' and several authors joined with 'and'.
    """
    first_author = re.split(r"\s+and\s+", author.strip(), maxsplit=1, flags=re.IGNORECASE)[0]

    if "," in first_author:
        return first_author.split(",")[0].strip()

    words = first_author.split()
    return words[-1] if words else ""


def cite_key_base(author, year):
    """Returns the start of a generated key, for example 'martin2008'"""
    name = first_author_last_name(author)
    name = unicodedata.normalize("NFKD", name)
    name = re.sub(r"[^a-z0-9]", "", name.lower())
    return (name or "ref") + year


def cite_key_candidates(author, year):
    """Generates martin2008, martin2008a, ..., martin2008z, martin2008aa, ..."""
    base = cite_key_base(author, year)
    yield base

    length = 1
    while True:
        for number in range(26 ** length):
            suffix = ""
            for _ in range(length):
                number, letter = divmod(number, 26)
                suffix = chr(ord("a") + letter) + suffix
            yield base + suffix
        length += 1
