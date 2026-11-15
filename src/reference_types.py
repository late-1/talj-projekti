"""Supported BibTeX entry types and their fields"""

ENTRY_TYPES = {
    "article": {
        "required": ["author", "title", "journal", "year"],
        "optional": ["volume", "number", "pages", "doi"],
    },
    "book": {
        "required": ["author", "title", "publisher", "year"],
        "optional": ["address", "edition", "isbn"],
    },
    "inproceedings": {
        "required": ["author", "title", "booktitle", "year"],
        "optional": ["pages", "publisher", "doi"],
    },
}

DEFAULT_ENTRY_TYPE = "article"

# All fields in the order they are shown in the form and written to BibTeX
FIELDS = {
    "author": "author(s)",
    "title": "title",
    "journal": "journal",
    "booktitle": "book title (name of the proceedings)",
    "publisher": "publisher",
    "year": "year",
    "volume": "volume",
    "number": "number",
    "pages": "pages",
    "address": "address",
    "edition": "edition",
    "isbn": "ISBN",
    "doi": "DOI",
}

FIELD_HINTS = {
    "author": "Separate several authors with the word and, "
              "for example: Martin, Robert and Fowler, Martin",
    "pages": "For example 12-34",
}

LONG_FIELDS = ["author", "title", "journal", "booktitle"]


def fields_of(entry_type):
    """Returns the names of the fields of the entry type in the form order"""
    entry = ENTRY_TYPES[entry_type]
    used = entry["required"] + entry["optional"]
    return [name for name in FIELDS if name in used]


def types_requiring(name):
    """Returns the entry types where the field is required"""
    return [t for t, entry in ENTRY_TYPES.items() if name in entry["required"]]


def types_with_optional(name):
    """Returns the entry types where the field is optional"""
    return [t for t, entry in ENTRY_TYPES.items() if name in entry["optional"]]
