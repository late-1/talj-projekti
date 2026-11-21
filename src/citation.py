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


def _article(fields):
    source = italic(fields["journal"])
    if fields.get("volume"):
        source += Markup(", ") + italic(fields["volume"])
    if fields.get("number"):
        source += escape(f"({fields['number']})")
    if fields.get("pages"):
        source += escape(f", {page_range(fields['pages'])}")
    return [escape(end_sentence(fields["title"])), source + Markup(".")]


def _book(fields):
    title = fields["title"].rstrip()
    if fields.get("edition"):
        parts = [italic(title) + escape(f" ({fields['edition']} ed.).")]
    else:
        # the full stop is not added after a title that ends with ? or !
        parts = [italic(title) + escape(end_sentence(title)[len(title):])]
    publisher = fields["publisher"]
    if fields.get("address"):
        publisher = f"{fields['address']}: {publisher}"
    parts.append(escape(end_sentence(publisher)))
    if fields.get("isbn"):
        parts.append(escape(f"ISBN {fields['isbn']}."))
    return parts


def _inproceedings(fields):
    source = Markup("In ") + italic(fields["booktitle"])
    if fields.get("pages"):
        source += escape(f" (pp. {page_range(fields['pages'])})")
    parts = [escape(end_sentence(fields["title"])), source + Markup(".")]
    if fields.get("publisher"):
        parts.append(escape(end_sentence(fields["publisher"])))
    return parts


# what follows the authors and the year, for each entry type
_FORMATS = {"article": _article, "book": _book, "inproceedings": _inproceedings}


def to_citation(reference):
    """
    Returns the reference as one citation, for example
    Martin, Robert (2008). Clean Code. Journal of Software, 12(3), 12–34.
    The values are escaped, and the names of journals, books and proceedings
    are in italics, so the result can be put on the page as such.
    """
    fields = reference.fields
    parts = [escape(f"{join_authors(fields['author'])} ({fields['year']}).")]
    parts += _FORMATS[reference.entry_type](fields)
    if fields.get("doi"):
        parts.append(escape(doi_address(fields["doi"])))
    return Markup(" ").join(parts)
