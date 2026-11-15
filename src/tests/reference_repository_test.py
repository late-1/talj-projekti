import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from config import db
from repositories import reference_repository, user_repository
from util import UserInputError

FIELDS = {
    "author": "Martin, Robert",
    "title": "Clean Code",
    "journal": "Journal of Software",
    "year": "2008",
}


@pytest.fixture
def user():
    return user_repository.create_user("maija", "secret-password")


@pytest.fixture
def other_user():
    return user_repository.create_user("uolevi", "secret-password")


def test_create_reference_stores_reference(user):
    fields = dict(FIELDS, volume="12", pages="12-34")
    created = reference_repository.create_reference(user.id, "article", fields)

    references = reference_repository.get_references(user.id)
    assert len(references) == 1

    reference = references[0]
    assert reference.id == created.id
    assert reference.user_id == user.id
    assert reference.entry_type == "article"
    assert reference.cite_key == "martin2008"
    assert reference.fields == fields
    assert reference.author == "Martin, Robert"
    assert reference.volume == "12"
    assert reference.doi is None


def test_create_reference_returns_reference(user):
    reference = reference_repository.create_reference(user.id, "article", FIELDS)
    assert reference.id is not None
    assert reference.cite_key == "martin2008"
    assert reference.title == "Clean Code"


def test_given_key_is_used(user):
    reference = reference_repository.create_reference(user.id, "article", FIELDS, "cleancode")
    assert reference.cite_key == "cleancode"
    assert reference_repository.get_references(user.id)[0].cite_key == "cleancode"


def test_generated_keys_get_a_letter_when_key_is_in_use(user):
    keys = [
        reference_repository.create_reference(user.id, "article", FIELDS).cite_key
        for _ in range(4)
    ]
    assert keys == ["martin2008", "martin2008a", "martin2008b", "martin2008c"]


def test_generated_key_skips_keys_given_by_the_user(user):
    reference_repository.create_reference(user.id, "article", FIELDS, "martin2008a")
    first = reference_repository.create_reference(user.id, "article", FIELDS)
    second = reference_repository.create_reference(user.id, "article", FIELDS)
    assert first.cite_key == "martin2008"
    assert second.cite_key == "martin2008b"


def test_given_key_must_be_unique_for_the_user(user):
    reference_repository.create_reference(user.id, "article", FIELDS, "cleancode")
    with pytest.raises(UserInputError, match="Key cleancode is already in use"):
        reference_repository.create_reference(user.id, "article", FIELDS, "cleancode")
    assert len(reference_repository.get_references(user.id)) == 1


def test_database_can_be_used_after_a_key_conflict(user):
    reference_repository.create_reference(user.id, "article", FIELDS, "cleancode")
    with pytest.raises(UserInputError):
        reference_repository.create_reference(user.id, "article", FIELDS, "cleancode")
    reference_repository.create_reference(user.id, "article", FIELDS, "other")
    assert len(reference_repository.get_references(user.id)) == 2


def test_different_users_can_have_the_same_key(user, other_user):
    first = reference_repository.create_reference(user.id, "article", FIELDS)
    second = reference_repository.create_reference(other_user.id, "article", FIELDS)
    assert first.cite_key == second.cite_key == "martin2008"

    reference_repository.create_reference(user.id, "article", FIELDS, "same")
    reference_repository.create_reference(other_user.id, "article", FIELDS, "same")


def test_user_gets_only_own_references(user, other_user):
    reference_repository.create_reference(user.id, "article", FIELDS)
    reference_repository.create_reference(other_user.id, "article", dict(FIELDS, title="Other"))

    references = reference_repository.get_references(user.id)
    assert [reference.title for reference in references] == ["Clean Code"]
    assert reference_repository.get_cite_keys(other_user.id) == {"martin2008"}


def test_references_are_returned_newest_first(user):
    for title in ["First", "Second", "Third"]:
        reference_repository.create_reference(user.id, "article", dict(FIELDS, title=title))
    titles = [reference.title for reference in reference_repository.get_references(user.id)]
    assert titles == ["Third", "Second", "First"]


def test_user_without_references(user):
    assert reference_repository.get_references(user.id) == []
    assert reference_repository.get_cite_keys(user.id) == set()


def test_book_and_inproceedings_fields_are_stored(user):
    book = {
        "author": "Fowler, Martin", "title": "Refactoring", "publisher": "Addison-Wesley",
        "year": "1999", "address": "Boston", "edition": "2", "isbn": "978-0201485677",
    }
    paper = {
        "author": "Vihavainen, Arto", "title": "Extreme Apprenticeship Method",
        "booktitle": "SIGCSE '11", "year": "2011", "pages": "93-98",
        "publisher": "ACM", "doi": "10.1145/1953163.1953196",
    }
    reference_repository.create_reference(user.id, "book", book)
    reference_repository.create_reference(user.id, "inproceedings", paper)

    stored_paper, stored_book = reference_repository.get_references(user.id)
    assert stored_book.entry_type == "book"
    assert stored_book.fields == book
    assert stored_paper.entry_type == "inproceedings"
    assert stored_paper.fields == paper


def test_special_characters_are_stored_as_such(user):
    title = "Robert'); DROP TABLE bib_references;-- <b>{\\\"a}</b> & ääkköset"
    reference_repository.create_reference(user.id, "article", dict(FIELDS, title=title))
    assert reference_repository.get_references(user.id)[0].title == title


def test_unknown_field_names_are_ignored(user):
    fields = dict(FIELDS, **{"title) VALUES (1); --": "x"})
    reference_repository.create_reference(user.id, "article", fields)
    assert reference_repository.get_references(user.id)[0].fields == FIELDS


def test_reference_needs_an_existing_user():
    with pytest.raises(IntegrityError):
        reference_repository.create_reference(123, "article", FIELDS, "key")
    db.session.rollback()
    assert db.session.execute(text("SELECT COUNT(*) FROM bib_references")).scalar() == 0
