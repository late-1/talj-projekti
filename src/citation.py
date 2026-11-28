"""Writing references as a citation for a list of references (APA-like style)"""
import re

from markupsafe import Markup, escape

AUTHOR_SEPARATOR = re.compile(r"\s+and\s+")
PAGE_RANGE = re.compile(r"(?<=\d)\s*-+\s*(?=\d)")


def join_authors(author):
    """Martin, Robert and Fowler, Martin -> Martin, Robert & Fowler, Martin"""
    names = [name for name in AUTHOR_SEPARATOR.split(author.strip()) if name]
    if len(names) <= 2:
        return " & ".join(names)
    return ", ".join(names[:-1]) + ", & " + names[-1]


def end_sentence(text):
    """Adds a full stop, unless the text already ends with a punctuation mark"""
    text = str(text).rstrip()
    return text if text.endswith((".", "?", "!")) else text + "."


def page_range(pages):
    return PAGE_RANGE.sub("–", pages)


def doi_address(doi):
    return doi if doi.startswith(("http://", "https://")) else f"https://doi.org/{doi}"


def italic(text):
    return Markup("<i>{}</i>").format(text)


def _title(fields, in_italics=False, details=""):
    """The title as the first part: 'Title.' or 'Title (details).' """
    if not fields.get("title"):
        return []
    title = fields["title"].rstrip()
    shown = italic(title) if in_italics else escape(title)
    if details:
        return [shown + escape(f" ({details}).")]
    # the full stop is not added after a title that ends with ? or !
    return [shown + escape(end_sentence(title)[len(title):])]


def _publisher(fields, name="publisher"):
    """'Address: Publisher.' or 'Publisher.'; empty when there is no such field"""
    if not fields.get(name):
        return []
    publisher = fields[name]
    if fields.get("address"):
        publisher = f"{fields['address']}: {publisher}"
    return [escape(end_sentence(publisher))]


def _editors(editor):
    """Martin, Robert -> Martin, Robert (Ed.); several -> (Eds.)"""
    names = [name for name in AUTHOR_SEPARATOR.split(editor.strip()) if name]
    return f"{join_authors(editor)} ({'Eds.' if len(names) > 1 else 'Ed.'})"


def _pages(fields):
    return f"pp. {page_range(fields['pages'])}" if fields.get("pages") else ""


def _article(fields):
    source = italic(fields["journal"])
    if fields.get("volume"):
        source += Markup(", ") + italic(fields["volume"])
    if fields.get("number"):
        source += escape(f"({fields['number']})")
    if fields.get("pages"):
        source += escape(f", {page_range(fields['pages'])}")
    return _title(fields) + [source + Markup(".")]


def _book(fields):
    edition = f"{fields['edition']} ed." if fields.get("edition") else ""
    parts = _title(fields, in_italics=True, details=edition) + _publisher(fields)
    if fields.get("isbn"):
        parts.append(escape(f"ISBN {fields['isbn']}."))
    return parts


def _in_book(fields, book):
    """'In Editor (Ed.), Book (pp. 1–2).' for a part of a book or proceedings"""
    source = Markup("In ")
    if fields.get("editor"):
        source += escape(_editors(fields["editor"]) + ", ")
    source += italic(book)
    if fields.get("pages"):
        source += escape(f" ({_pages(fields)})")
    return source + Markup(".")


def _inproceedings(fields):
    parts = _title(fields) + [_in_book(fields, fields["booktitle"])]
    return parts + _publisher(fields) + _publisher(fields, "organization")


def _incollection(fields):
    chapter = f"Chapter {fields['chapter']}" if fields.get("chapter") else ""
    return _title(fields, details=chapter) + [_in_book(fields, fields["booktitle"])] \
        + _publisher(fields)


def _inbook(fields):
    details = [f"Chapter {fields['chapter']}"]
    if fields.get("pages"):
        details.append(_pages(fields))
    if fields.get("edition"):
        details.append(f"{fields['edition']} ed.")
    return _title(fields, in_italics=True, details=", ".join(details)) + _publisher(fields)


def _booklet(fields):
    parts = _title(fields, in_italics=True)
    if fields.get("howpublished"):
        parts.append(escape(end_sentence(fields["howpublished"])))
    if fields.get("address"):
        parts.append(escape(end_sentence(fields["address"])))
    return parts


def _manual(fields):
    edition = f"{fields['edition']} ed." if fields.get("edition") else ""
    return _title(fields, in_italics=True, details=edition) + _publisher(fields, "organization")


def _thesis(kind):
    def format_thesis(fields):
        parts = _title(fields, in_italics=True)
        parts.append(escape(f"[{kind}, {fields['school']}]."))
        if fields.get("address"):
            parts.append(escape(end_sentence(fields["address"])))
        return parts
    return format_thesis


def _misc(fields):
    parts = _title(fields, in_italics=True)
    if fields.get("howpublished"):
        parts.append(escape(end_sentence(fields["howpublished"])))
    return parts


def _proceedings(fields):
    volume = f"Vol. {fields['volume']}" if fields.get("volume") else ""
    parts = _title(fields, in_italics=True, details=volume)
    if fields.get("series"):
        parts.append(escape(end_sentence(fields["series"])))
    return parts + _publisher(fields) + _publisher(fields, "organization")


def _techreport(fields):
    number = f"Report No. {fields['number']}" if fields.get("number") else ""
    return _title(fields, in_italics=True, details=number) + _publisher(fields, "institution")


def _unpublished(fields):
    return _title(fields, in_italics=True) + [escape("[Unpublished manuscript].")]


# what follows the authors and the year, for each entry type
_FORMATS = {
    "article": _article,
    "book": _book,
    "inproceedings": _inproceedings,
    "booklet": _booklet,
    "conference": _inproceedings,
    "inbook": _inbook,
    "incollection": _incollection,
    "manual": _manual,
    "mastersthesis": _thesis("Master's thesis"),
    "misc": _misc,
    "phdthesis": _thesis("Doctoral dissertation"),
    "proceedings": _proceedings,
    "techreport": _techreport,
    "unpublished": _unpublished,
}


def to_citation(reference):
    """
    Returns the reference as one citation, for example
    Martin, Robert (2008). Clean Code. Journal of Software, 12(3), 12–34.
    The values are escaped, and the names of journals, books and proceedings
    are in italics, so the result can be put on the page as such.

    Without authors, the editors are used. Without either, the title comes
    first and the year after it: Clean Code. (2008). ... A missing year is
    written n.d. (no date).
    """
    fields = reference.fields
    year = fields.get("year") or "n.d."
    parts = _FORMATS[reference.entry_type](fields)

    if fields.get("author"):
        parts.insert(0, escape(f"{join_authors(fields['author'])} ({year})."))
    elif fields.get("editor"):
        parts.insert(0, escape(f"{_editors(fields['editor'])} ({year})."))
    else:
        parts.insert(1 if fields.get("title") else 0, escape(f"({year})."))

    if fields.get("note"):
        parts.append(escape(end_sentence(fields["note"])))
    if fields.get("doi"):
        parts.append(escape(doi_address(fields["doi"])))
    if fields.get("url"):
        parts.append(escape(fields["url"]))
    return Markup(" ").join(parts)
