import itertools

import pytest

from reference_types import ENTRY_TYPES, FIELDS, fields_of
from tests.conftest import ARTICLE, BOOK, INPROCEEDINGS
from util import (
    UserInputError,
    cite_key_base,
    cite_key_candidates,
    first_author_last_name,
    validate_cite_key,
    validate_reference,
)


def fields_only(form):
    return {name: value for name, value in form.items() if name != "entry_type"}


# entry types

def test_every_field_of_every_type_is_known():
    for entry in ENTRY_TYPES.values():
        for name in entry["required"] + entry["optional"]:
            assert name in FIELDS
        assert not set(entry["required"]) & set(entry["optional"])


def test_every_type_requires_author_title_and_year():
    for entry in ENTRY_TYPES.values():
        assert {"author", "title", "year"} <= set(entry["required"])


def test_fields_of_returns_fields_in_form_order():
    assert fields_of("article") == [
        "author", "title", "journal", "year", "volume", "number", "pages", "doi",
    ]
    assert fields_of("book") == [
        "author", "title", "publisher", "year", "address", "edition", "isbn",
    ]
    assert fields_of("inproceedings") == [
        "author", "title", "booktitle", "publisher", "year", "pages", "doi",
    ]


# validate_reference

@pytest.mark.parametrize("form", [ARTICLE, BOOK, INPROCEEDINGS])
def test_valid_reference_is_accepted(form):
    assert validate_reference(form["entry_type"], form) == fields_only(form)


def test_optional_fields_are_returned():
    form = dict(ARTICLE, volume="12", number="3", pages="12-34", doi="10.1000/182")
    fields = validate_reference("article", form)
    assert fields["volume"] == "12"
    assert fields["number"] == "3"
    assert fields["pages"] == "12-34"
    assert fields["doi"] == "10.1000/182"


def test_empty_optional_fields_are_left_out():
    form = dict(ARTICLE, volume="", pages="   ")
    assert validate_reference("article", form) == fields_only(ARTICLE)


def test_fields_of_other_types_are_left_out():
    form = dict(ARTICLE, publisher="Prentice Hall", isbn="123", booktitle="Proceedings")
    assert validate_reference("article", form) == fields_only(ARTICLE)


def test_whitespace_is_cleaned():
    form = dict(ARTICLE, title="  Clean \n  Code  ")
    assert validate_reference("article", form)["title"] == "Clean Code"


def test_unknown_type_is_rejected():
    with pytest.raises(UserInputError, match="Unknown reference type"):
        validate_reference("phdthesis", ARTICLE)
    with pytest.raises(UserInputError, match="Unknown reference type"):
        validate_reference("", ARTICLE)


@pytest.mark.parametrize("form,name,message", [
    (ARTICLE, "author", "Author is required"),
    (ARTICLE, "title", "Title is required"),
    (ARTICLE, "journal", "Journal is required"),
    (ARTICLE, "year", "Year is required"),
    (BOOK, "publisher", "Publisher is required"),
    (INPROCEEDINGS, "booktitle", "Book title is required"),
])
def test_required_field_is_required(form, name, message):
    missing = {key: value for key, value in form.items() if key != name}
    with pytest.raises(UserInputError, match=message):
        validate_reference(form["entry_type"], missing)

    blank = dict(form, **{name: "   "})
    with pytest.raises(UserInputError, match=message):
        validate_reference(form["entry_type"], blank)


@pytest.mark.parametrize("year", ["08", "20081", "abcd", "2008a", "-200", "20 08"])
def test_invalid_year_is_rejected(year):
    with pytest.raises(UserInputError, match="four-digit"):
        validate_reference("article", dict(ARTICLE, year=year))


def test_field_lengths_are_limited():
    validate_reference("article", dict(ARTICLE, title="a" * 1000))
    with pytest.raises(UserInputError, match="Title can be at most 1000"):
        validate_reference("article", dict(ARTICLE, title="a" * 1001))

    validate_reference("article", dict(ARTICLE, volume="1" * 200))
    with pytest.raises(UserInputError, match="Volume can be at most 200"):
        validate_reference("article", dict(ARTICLE, volume="1" * 201))


# validate_cite_key

@pytest.mark.parametrize(
    "key", ["martin2008", "Martin:2008", "a", "DBLP:conf/sigcse/V11", "a_b-c.d+e"]
)
def test_valid_key_is_accepted(key):
    validate_cite_key(key)


@pytest.mark.parametrize(
    "key", ["martin 2008", "martin,2008", "{martin}", "mäki2008", "a#b", "a%b", "a\\b"]
)
def test_key_with_invalid_characters_is_rejected(key):
    with pytest.raises(UserInputError, match="can only contain"):
        validate_cite_key(key)


def test_too_long_key_is_rejected():
    validate_cite_key("a" * 50)
    with pytest.raises(UserInputError, match="at most 50"):
        validate_cite_key("a" * 51)


# generating keys

@pytest.mark.parametrize("author,last_name", [
    ("Martin, Robert", "Martin"),
    ("Robert Martin", "Martin"),
    ("Robert C. Martin", "Martin"),
    ("Martin", "Martin"),
    ("Martin, Robert and Fowler, Martin", "Martin"),
    ("Robert Martin and Martin Fowler", "Martin"),
    ("Robert Martin AND Martin Fowler", "Martin"),
    ("van der Berg, Anna", "van der Berg"),
    ("Anderson, Andy and Sandberg, Sandy", "Anderson"),
    ("  Martin ,  Robert  ", "Martin"),
    ("", ""),
])
def test_first_author_last_name(author, last_name):
    assert first_author_last_name(author) == last_name


@pytest.mark.parametrize("author,year,base", [
    ("Martin, Robert", "2008", "martin2008"),
    ("Robert Martin and Martin Fowler", "1999", "martin1999"),
    ("Mäkelä, Äänekoski", "2020", "makela2020"),
    ("van der Berg, Anna", "2001", "vanderberg2001"),
    ("O'Neil, Cathy", "2016", "oneil2016"),
    ("Łukasz", "2016", "ukasz2016"),
    ("李, 明", "2016", "ref2016"),
])
def test_cite_key_base(author, year, base):
    assert cite_key_base(author, year) == base


def test_cite_key_candidates():
    candidates = list(itertools.islice(cite_key_candidates("Martin, Robert", "2008"), 30))
    assert candidates[:4] == ["martin2008", "martin2008a", "martin2008b", "martin2008c"]
    assert candidates[26] == "martin2008z"
    assert candidates[27:30] == ["martin2008aa", "martin2008ab", "martin2008ac"]
    assert len(set(candidates)) == 30


def test_generated_keys_are_valid():
    for candidate in itertools.islice(cite_key_candidates("Mäkelä, Äänekoski", "2020"), 30):
        validate_cite_key(candidate)
