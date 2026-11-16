"""Writing references in BibTeX format"""
import re

# Fields that are written as such: the characters have no special meaning there
VERBATIM_FIELDS = ["doi", "isbn"]

# LaTeX special characters that people commonly type as plain text.
# A character that is already escaped with a backslash is left alone.
UNESCAPED_SPECIAL = re.compile(r"(?<!\\)([&%#])")

PAGE_RANGE = re.compile(r"(?<=\d)\s*[-–—]\s*(?=\d)")


def format_value(name, value):
    if name in VERBATIM_FIELDS:
        return value

    if name == "pages":
        # BibTeX page ranges use a double hyphen: 12--34
        return PAGE_RANGE.sub("--", value)

    return UNESCAPED_SPECIAL.sub(r"\\\1", value)


def to_bibtex(reference):
    """Returns the reference as a BibTeX entry"""
    width = max(len(name) for name in reference.fields)
    lines = [
        f"  {name.ljust(width)} = {{{format_value(name, value)}}}"
        for name, value in reference.fields.items()
    ]
    return f"@{reference.entry_type}{{{reference.cite_key},\n" + ",\n".join(lines) + "\n}"
