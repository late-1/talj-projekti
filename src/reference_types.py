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
    # the less common types, in alphabetical order; shown behind "more"
    "booklet": {
        "required": ["title"],
        "optional": ["author", "howpublished", "address", "month", "year", "note"],
    },
    # an older name of inproceedings
    "conference": {
        "required": ["author", "title", "booktitle", "year"],
        "optional": ["editor", "pages", "series", "organization", "publisher", "doi"],
    },
    "inbook": {
        "required": ["author", "title", "chapter", "publisher", "year"],
        "optional": ["editor", "pages", "volume", "series", "address", "edition", "month",
                     "note"],
    },
    "incollection": {
        "required": ["author", "title", "booktitle", "publisher", "year"],
        "optional": ["editor", "chapter", "pages", "volume", "series", "address", "edition",
                     "month", "note"],
    },
    "manual": {
        "required": ["title"],
        "optional": ["author", "organization", "address", "edition", "month", "year", "note"],
    },
    "mastersthesis": {
        "required": ["author", "title", "school", "year"],
        "optional": ["address", "month", "note"],
    },
    "misc": {
        "required": [],
        "optional": ["author", "title", "howpublished", "month", "year", "note", "url"],
    },
    "phdthesis": {
        "required": ["author", "title", "school", "year"],
        "optional": ["address", "month", "note"],
    },
    "proceedings": {
        "required": ["title", "year"],
        "optional": ["editor", "volume", "series", "address", "month", "organization",
                     "publisher", "note"],
    },
    "techreport": {
        "required": ["author", "title", "institution", "year"],
        "optional": ["number", "address", "month", "note"],
    },
    "unpublished": {
        "required": ["author", "title", "note"],
        "optional": ["month", "year"],
    },
}

DEFAULT_ENTRY_TYPE = "article"

# The common types are shown as such, the others in the "more" menu
MAIN_TYPES = ["article", "book", "inproceedings"]
MORE_TYPES = [entry_type for entry_type in ENTRY_TYPES if entry_type not in MAIN_TYPES]

# All fields in the order they are shown in the form and written to BibTeX
FIELDS = {
    "author": "author(s)",
    "editor": "editor(s)",
    "title": "title",
    "journal": "journal",
    "booktitle": "book title (name of the book or the proceedings)",
    "chapter": "chapter",
    "school": "school (university)",
    "institution": "institution",
    "organization": "organization",
    "howpublished": "how published (for example a web site)",
    "publisher": "publisher",
    "year": "year",
    "month": "month",
    "volume": "volume",
    "number": "number",
    "series": "series",
    "pages": "pages",
    "address": "address",
    "edition": "edition",
    "isbn": "ISBN",
    "doi": "DOI",
    "url": "URL",
    "note": "note",
}

# Field names without the explanation in parentheses, for showing a reference
SHORT_LABELS = {name: label.split(" (", maxsplit=1)[0] for name, label in FIELDS.items()}

FIELD_HINTS = {
    "author": "Separate several authors with the word and, "
              "for example: Martin, Robert and Fowler, Martin",
    "editor": "Separate several editors with the word and",
    "pages": "For example 12-34",
}

LONG_FIELDS = ["author", "editor", "title", "journal", "booktitle", "howpublished", "url",
               "note"]

# Where a reference was published, in the order of preference
VENUE_FIELDS = ["journal", "booktitle", "school", "institution", "organization",
                "howpublished", "publisher"]


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
