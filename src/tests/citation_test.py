import pytest
from markupsafe import Markup

from citation import end_sentence, join_authors, page_range, to_citation
from entities.reference import Reference


def citation(entry_type, **fields):
    return to_citation(Reference(1, 1, entry_type, "key2008", fields))


ARTICLE = {
    "author": "Martin, Robert", "title": "Clean Code",
    "journal": "Journal of Software", "year": "2008",
}

BOOK = {
    "author": "Fowler, Martin", "title": "Refactoring",
    "publisher": "Addison-Wesley", "year": "1999",
}

INPROCEEDINGS = {
    "author": "Vihavainen, Arto and Paksula, Matti and Luukkainen, Matti",
    "title": "Extreme Apprenticeship Method in Teaching Programming for Beginners",
    "booktitle": "SIGCSE '11", "year": "2011",
}


# helpers

@pytest.mark.parametrize("author, expected", [
    ("Martin, Robert", "Martin, Robert"),
    ("Martin, Robert and Fowler, Martin", "Martin, Robert & Fowler, Martin"),
    ("A, B and C, D and E, F", "A, B, C, D, & E, F"),
    ("  Martin, Robert   and\nFowler, Martin ", "Martin, Robert & Fowler, Martin"),
    # "and" inside a name is not a separator
    ("Anderson, Sandra", "Anderson, Sandra"),
])
def test_join_authors(author, expected):
    assert join_authors(author) == expected


@pytest.mark.parametrize("text, expected", [
    ("Clean Code", "Clean Code."),
    ("Clean Code.", "Clean Code."),
    ("Why Code?", "Why Code?"),
    ("Code!", "Code!"),
    ("Clean Code  ", "Clean Code."),
])
def test_end_sentence(text, expected):
    assert end_sentence(text) == expected


@pytest.mark.parametrize("pages, expected", [
    ("12-34", "12–34"), ("12--34", "12–34"), ("12 - 34", "12–34"), ("e123", "e123"),
])
def test_page_range(pages, expected):
    assert page_range(pages) == expected


# the three types

def test_article_with_required_fields():
    assert citation("article", **ARTICLE) == (
        "Martin, Robert (2008). Clean Code. <i>Journal of Software</i>."
    )


def test_article_with_all_fields():
    assert citation(
        "article", **ARTICLE, volume="12", number="3", pages="12-34", doi="10.1000/182",
    ) == (
        "Martin, Robert (2008). Clean Code. <i>Journal of Software</i>, <i>12</i>(3), 12–34. "
        "https://doi.org/10.1000/182"
    )


def test_book_with_required_fields():
    assert citation("book", **BOOK) == (
        "Fowler, Martin (1999). <i>Refactoring</i>. Addison-Wesley."
    )


def test_book_with_all_fields():
    assert citation(
        "book", **BOOK, address="Boston", edition="2nd", isbn="978-0-201-48567-7",
    ) == (
        "Fowler, Martin (1999). <i>Refactoring</i> (2nd ed.). Boston: Addison-Wesley. "
        "ISBN 978-0-201-48567-7."
    )


def test_book_title_ending_with_question_mark_gets_no_full_stop():
    assert citation("book", **{**BOOK, "title": "Why Refactor?"}).startswith(
        "Fowler, Martin (1999). <i>Why Refactor?</i> Addison-Wesley."
    )


def test_inproceedings_with_required_fields():
    assert citation("inproceedings", **INPROCEEDINGS) == (
        "Vihavainen, Arto, Paksula, Matti, &amp; Luukkainen, Matti (2011). Extreme "
        "Apprenticeship Method in Teaching Programming for Beginners. "
        "In <i>SIGCSE &#39;11</i>."
    )


def test_inproceedings_with_all_fields():
    assert citation(
        "inproceedings", **INPROCEEDINGS, pages="93-98", publisher="ACM",
        doi="https://doi.org/10.1145/1953163.1953196",
    ).endswith(
        "In <i>SIGCSE &#39;11</i> (pp. 93–98). ACM. https://doi.org/10.1145/1953163.1953196"
    )


# safety

def test_citation_is_markup_and_values_are_escaped():
    result = citation("article", **{
        **ARTICLE, "author": "<b>Martin</b>", "journal": "<script>x</script> & co",
    })
    assert isinstance(result, Markup)
    assert "<b>" not in result
    assert "<script>" not in result
    assert "&lt;b&gt;Martin&lt;/b&gt;" in result
    assert "<i>&lt;script&gt;x&lt;/script&gt; &amp; co</i>" in result


def test_latex_is_left_as_it_is():
    author = "M{\\\"a}kel{\\\"a}, Matti"
    # striptags() returns the text as the browser shows it
    assert citation("article", **{**ARTICLE, "author": author}).striptags().startswith(author)
