import pytest
from sqlalchemy import text

from config import db
from repositories import reference_repository
from tests.conftest import ARTICLE, BOOK, INPROCEEDINGS


def reference_count():
    return db.session.execute(text("SELECT COUNT(*) FROM bib_references")).scalar()


def own_references(actions):
    return reference_repository.get_references(actions.session()["user_id"])


@pytest.fixture
def logged_in(actions):
    actions.register("maija")


# the form

def test_add_page_has_form(client, logged_in):
    page = client.get("/add").get_data(as_text=True)
    assert 'action="/add"' in page
    assert 'name="csrf_token"' in page
    assert 'name="cite_key"' in page
    for entry_type in ["article", "book", "inproceedings"]:
        assert f'value="{entry_type}"' in page
    for name in ["author", "title", "journal", "booktitle", "publisher", "year",
                 "volume", "number", "pages", "address", "edition", "isbn", "doi"]:
        assert f'name="{name}"' in page


def test_add_page_has_article_chosen_by_default(client, logged_in):
    page = client.get("/add").get_data(as_text=True)
    assert 'id="type-article" value="article"\n               checked' in page
    assert 'id="type-book" value="book"\n               checked' not in page


def test_add_page_form_contains_csrf_token_of_the_session(client, actions, logged_in):
    page = client.get("/add").get_data(as_text=True)
    assert f'value="{actions.csrf_token()}"' in page


def test_script_is_served(client):
    assert client.get("/static/add_reference.js").status_code == 200


# adding

def test_add_article(client, actions, logged_in):
    response = actions.add_reference(volume="12", number="3", pages="12-34", doi="10.1000/182")
    assert response.status_code == 302
    assert response.headers["Location"] == "/add?type=article"

    references = own_references(actions)
    assert len(references) == 1
    assert references[0].entry_type == "article"
    assert references[0].cite_key == "martin2008"
    assert references[0].fields == {
        "author": "Martin, Robert", "title": "Clean Code", "journal": "Journal of Software",
        "year": "2008", "volume": "12", "number": "3", "pages": "12-34", "doi": "10.1000/182",
    }


def test_add_book(client, actions, logged_in):
    response = actions.add_reference(**BOOK, address="Boston", edition="2", isbn="978-0201485677")
    assert response.status_code == 302

    reference = own_references(actions)[0]
    assert reference.entry_type == "book"
    assert reference.cite_key == "fowler1999"
    assert reference.publisher == "Addison-Wesley"
    assert reference.address == "Boston"
    assert reference.edition == "2"
    assert reference.isbn == "978-0201485677"
    # the article fields of the default form data do not belong to a book
    assert reference.journal is None


def test_add_inproceedings(client, actions, logged_in):
    response = actions.add_reference(**INPROCEEDINGS, pages="93-98", publisher="ACM")
    assert response.status_code == 302

    reference = own_references(actions)[0]
    assert reference.entry_type == "inproceedings"
    assert reference.cite_key == "vihavainen2011"
    assert reference.booktitle == "SIGCSE '11"
    assert reference.pages == "93-98"
    assert reference.publisher == "ACM"


def test_success_message_shows_the_key(client, actions, logged_in):
    actions.add_reference()
    page = client.get("/add").get_data(as_text=True)
    assert "Reference added with the key martin2008" in page
    assert 'class="flash notice"' in page
    # the form is empty again
    assert 'value="Clean Code"' not in page


def test_form_stays_on_the_added_type(client, actions, logged_in):
    response = actions.add_reference(**BOOK)
    assert response.headers["Location"] == "/add?type=book"

    page = client.get("/add?type=book").get_data(as_text=True)
    assert 'id="type-book" value="book"\n               checked' in page


def test_unknown_type_in_address_shows_default_type(client, logged_in):
    page = client.get("/add?type=phdthesis").get_data(as_text=True)
    assert 'id="type-article" value="article"\n               checked' in page


def test_add_with_own_key(client, actions, logged_in):
    actions.add_reference(cite_key="  cleancode ")
    assert own_references(actions)[0].cite_key == "cleancode"


def test_generated_key_gets_a_letter_when_in_use(client, actions, logged_in):
    for _ in range(3):
        actions.add_reference()
    keys = [reference.cite_key for reference in own_references(actions)]
    assert keys == ["martin2008b", "martin2008a", "martin2008"]


def test_reference_belongs_to_the_logged_in_user(client, actions, logged_in):
    actions.add_reference()
    maija_id = actions.session()["user_id"]
    actions.logout()

    actions.register("uolevi")
    actions.add_reference(title="Other")
    uolevi_id = actions.session()["user_id"]

    assert [r.title for r in reference_repository.get_references(maija_id)] == ["Clean Code"]
    assert [r.title for r in reference_repository.get_references(uolevi_id)] == ["Other"]


# invalid input

@pytest.mark.parametrize("fields,message", [
    ({"author": ""}, "Author is required"),
    ({"title": "  "}, "Title is required"),
    ({"journal": ""}, "Journal is required"),
    ({"year": ""}, "Year is required"),
    ({"year": "abcd"}, "Year must be a four-digit number"),
    ({"title": "a" * 1001}, "Title can be at most 1000 characters long"),
    ({"entry_type": "phdthesis"}, "Unknown reference type"),
    ({"entry_type": "book"}, "Publisher is required"),
    ({"entry_type": "inproceedings"}, "Book title is required"),
    ({"cite_key": "clean code"}, "Key can only contain"),
    ({"cite_key": "a" * 51}, "Key can be at most 50 characters long"),
])
def test_invalid_reference_is_not_added(client, actions, logged_in, fields, message):
    response = actions.add_reference(**fields)
    assert response.status_code == 200
    assert message in response.get_data(as_text=True)
    assert reference_count() == 0


def test_key_in_use_is_rejected(client, actions, logged_in):
    actions.add_reference(cite_key="cleancode")
    response = actions.add_reference(cite_key="cleancode", title="Other")
    assert response.status_code == 200
    assert "Key cleancode is already in use" in response.get_data(as_text=True)
    assert reference_count() == 1


def test_failed_add_keeps_values_in_form(client, actions, logged_in):
    response = actions.add_reference(
        entry_type="book", author="Fowler, Martin", title="Refactoring", year="99",
        publisher="Addison-Wesley", cite_key="fowler",
    )
    page = response.get_data(as_text=True)
    assert 'id="type-book" value="book"\n               checked' in page
    assert 'value="Fowler, Martin"' in page
    assert 'value="Refactoring"' in page
    assert 'value="Addison-Wesley"' in page
    assert 'value="99"' in page
    assert 'value="fowler"' in page


def test_values_are_escaped_in_form(client, actions, logged_in):
    response = actions.add_reference(title='"><script>alert(1)</script>', year="x")
    page = response.get_data(as_text=True)
    assert "<script>alert(1)</script>" not in page
    assert "&lt;script&gt;" in page


def test_missing_fields_do_not_crash(client, actions, logged_in):
    response = client.post("/add", data={"csrf_token": actions.csrf_token()})
    assert response.status_code == 200
    assert "Unknown reference type" in response.get_data(as_text=True)
    assert reference_count() == 0


# access control

def test_add_requires_login(client):
    response = client.post("/add", data=ARTICLE)
    assert response.status_code == 302
    assert response.headers["Location"] == "/login"
    assert reference_count() == 0


@pytest.mark.parametrize("token", ["", "wrong-token"])
def test_add_requires_csrf_token(client, actions, logged_in, token):
    data = dict(ARTICLE)
    if token:
        data["csrf_token"] = token
    response = client.post("/add", data=data)
    assert response.status_code == 403
    assert reference_count() == 0


def test_session_of_removed_user_is_logged_out(client, actions, logged_in):
    db.session.execute(text("DELETE FROM users"))
    db.session.commit()

    response = actions.add_reference()
    assert response.headers["Location"] == "/login"
    assert actions.session() == {}
    assert reference_count() == 0
