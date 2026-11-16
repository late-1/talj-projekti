import pytest

from bibtex import format_value, to_bibtex
from entities.reference import Reference


def reference(entry_type, cite_key, **fields):
    return Reference(1, 1, entry_type, cite_key, fields)


def test_article_as_bibtex():
    article = reference(
        "article", "martin2008",
        author="Martin, Robert", title="Clean Code", journal="Journal of Software",
        year="2008", volume="12", number="3", pages="12-34", doi="10.1000/182",
    )
    assert to_bibtex(article) == (
        "@article{martin2008,\n"
        "  author  = {Martin, Robert},\n"
        "  title   = {Clean Code},\n"
        "  journal = {Journal of Software},\n"
        "  year    = {2008},\n"
        "  volume  = {12},\n"
        "  number  = {3},\n"
        "  pages   = {12--34},\n"
        "  doi     = {10.1000/182}\n"
        "}"
    )


def test_book_as_bibtex():
    book = reference(
        "book", "fowler1999",
        author="Fowler, Martin", title="Refactoring", publisher="Addison-Wesley",
        year="1999", address="Boston", edition="2", isbn="978-0201485677",
    )
    assert to_bibtex(book) == (
        "@book{fowler1999,\n"
        "  author    = {Fowler, Martin},\n"
        "  title     = {Refactoring},\n"
        "  publisher = {Addison-Wesley},\n"
        "  year      = {1999},\n"
        "  address   = {Boston},\n"
        "  edition   = {2},\n"
        "  isbn      = {978-0201485677}\n"
        "}"
    )


def test_inproceedings_as_bibtex():
    paper = reference(
        "inproceedings", "vihavainen2011",
        author="Vihavainen, Arto and Luukkainen, Matti", title="Extreme Apprenticeship Method",
        booktitle="SIGCSE '11", year="2011", pages="93-98", publisher="ACM",
    )
    assert to_bibtex(paper) == (
        "@inproceedings{vihavainen2011,\n"
        "  author    = {Vihavainen, Arto and Luukkainen, Matti},\n"
        "  title     = {Extreme Apprenticeship Method},\n"
        "  booktitle = {SIGCSE '11},\n"
        "  publisher = {ACM},\n"
        "  year      = {2011},\n"
        "  pages     = {93--98}\n"
        "}"
    )


def test_only_required_fields():
    article = reference(
        "article", "key", author="A", title="T", journal="J", year="2000",
        volume="", pages=None,
    )
    assert to_bibtex(article) == (
        "@article{key,\n"
        "  author  = {A},\n"
        "  title   = {T},\n"
        "  journal = {J},\n"
        "  year    = {2000}\n"
        "}"
    )


def test_fields_of_other_types_are_not_written():
    article = reference(
        "article", "key", author="A", title="T", journal="J", year="2000", isbn="123",
    )
    assert "isbn" not in to_bibtex(article)


@pytest.mark.parametrize("value,expected", [
    ("Clean Code", "Clean Code"),
    ("Research & Development", r"Research \& Development"),
    ("100% Coverage", r"100\% Coverage"),
    ("C# in Depth", r"C\# in Depth"),
    (r"Research \& Development", r"Research \& Development"),
    ("A & B & C", r"A \& B \& C"),
    ("Mäkelä and Öström", "Mäkelä and Öström"),
    (r"M{\"a}kel{\"a}", r"M{\"a}kel{\"a}"),
    ("The {UNIX} System", "The {UNIX} System"),
    ("Complexity of $O(n_1)$", "Complexity of $O(n_1)$"),
])
def test_special_characters_in_text(value, expected):
    assert format_value("title", value) == expected


@pytest.mark.parametrize("value,expected", [
    ("12-34", "12--34"),
    ("12--34", "12--34"),
    ("12 - 34", "12--34"),
    ("12–34", "12--34"),
    ("12", "12"),
    ("12-34, 40-45", "12--34, 40--45"),
    ("e1023", "e1023"),
    ("A1-A9", "A1-A9"),
])
def test_page_ranges(value, expected):
    assert format_value("pages", value) == expected


def test_doi_and_isbn_are_written_as_such():
    assert format_value("doi", "10.1000/a_b%c#d&e") == "10.1000/a_b%c#d&e"
    assert format_value("isbn", "978-0-201-48567-7") == "978-0-201-48567-7"
