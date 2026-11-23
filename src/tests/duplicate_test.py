import re

import pytest

from repositories import reference_repository
from tests.conftest import ARTICLE, BOOK

DIALOG = '<dialog class="dialog" id="duplicate-dialog"'


@pytest.fixture
def logged_in(actions):
    actions.register("maija")


@pytest.fixture
def existing(actions, logged_in):
    """An article of maija with some optional fields"""
    actions.add_reference(volume="12", pages="12-34")
    return own_references(actions)[0]


def own_references(actions):
    return reference_repository.get_references(actions.session()["user_id"])


def text_of(response):
    return response.get_data(as_text=True)


def fields_of(reference):
    return dict(reference.fields)


def edit(client, actions, reference_id, confirm=False, **fields):
    """Posts the edit form; the defaults make the same article as the fixture"""
    data = dict(ARTICLE, volume="12", pages="12-34")
    data.update(fields)
    data["csrf_token"] = actions.csrf_token()
    if confirm:
        data["confirm_duplicate"] = "yes"
    return client.post(f"/references/{reference_id}/edit", data=data)


def dialog_of(page):
    return re.search(r"<dialog.*?</dialog>", page, re.S).group(0)


# finding a duplicate in the repository

def test_same_type_and_fields_is_a_duplicate(actions, existing):
    user_id = actions.session()["user_id"]
    duplicate = reference_repository.find_duplicate(user_id, "article", fields_of(existing))
    assert duplicate.id == existing.id


def test_key_does_not_matter(client, actions, existing):
    actions.add_reference(volume="12", pages="12-34", cite_key="other-key",
                          confirm_duplicate="yes")
    user_id = actions.session()["user_id"]
    references = own_references(actions)
    assert {reference.cite_key for reference in references} == {"martin2008", "other-key"}
    # the oldest one is reported
    duplicate = reference_repository.find_duplicate(user_id, "article", fields_of(existing))
    assert duplicate.cite_key == "martin2008"


@pytest.mark.parametrize("changes", [
    {"title": "Clean Code 2"},
    {"title": "clean code"},
    {"volume": "13"},
    {"volume": None},
    {"number": "1"},
    {"pages": "12--34"},
])
def test_one_different_field_is_not_a_duplicate(actions, existing, changes):
    fields = fields_of(existing)
    fields.update(changes)
    fields = {name: value for name, value in fields.items() if value is not None}
    user_id = actions.session()["user_id"]
    assert reference_repository.find_duplicate(user_id, "article", fields) is None


def test_different_type_is_not_a_duplicate(actions, logged_in):
    actions.add_reference(**BOOK)
    user_id = actions.session()["user_id"]
    fields = {name: value for name, value in BOOK.items() if name != "entry_type"}
    assert reference_repository.find_duplicate(user_id, "book", fields) is not None
    assert reference_repository.find_duplicate(user_id, "inproceedings", fields) is None


def test_reference_of_another_user_is_not_a_duplicate(actions, existing):
    user_id = actions.session()["user_id"]
    assert reference_repository.find_duplicate(user_id + 1, "article", fields_of(existing)) is None


def test_the_edited_reference_itself_is_not_a_duplicate(actions, existing):
    user_id = actions.session()["user_id"]
    fields = fields_of(existing)
    assert reference_repository.find_duplicate(
        user_id, "article", fields, exclude_id=existing.id
    ) is None


# adding

def test_adding_the_same_reference_shows_the_dialog(client, actions, existing):
    response = actions.add_reference(volume="12", pages="12-34")
    assert response.status_code == 200
    dialog = dialog_of(text_of(response))
    assert "The same reference already exists (martin2008). Add it anyway?" in dialog
    assert re.search(r'<button type="submit" class="button" id="duplicate-confirm"'
                     r' form="reference-form"\s+name="confirm_duplicate" value="yes">add</button>',
                     dialog)
    assert '<form method="dialog">' in dialog
    assert 'id="duplicate-cancel">cancel</button>' in dialog
    assert 'src="/static/dialog.js"' in text_of(response)
    # nothing was stored
    assert len(own_references(actions)) == 1


def test_form_keeps_the_values_under_the_dialog(client, actions, existing):
    page = text_of(actions.add_reference(volume="12", pages="12-34", cite_key="my-key"))
    form = page[page.index('id="reference-form"'):page.index("<dialog")]
    for value in ["Martin, Robert", "Clean Code", "Journal of Software", "2008", "12", "12-34",
                  "my-key"]:
        assert f'value="{value}"' in form


def test_add_in_the_dialog_stores_the_reference(client, actions, existing):
    response = actions.add_reference(volume="12", pages="12-34", confirm_duplicate="yes")
    assert response.status_code == 302
    keys = [reference.cite_key for reference in own_references(actions)]
    assert keys == ["martin2008a", "martin2008"]
    assert "Reference added with the key martin2008a" in text_of(client.get("/add"))


def test_different_reference_is_added_without_the_dialog(client, actions, existing):
    response = actions.add_reference(volume="13", pages="12-34")
    assert response.status_code == 302
    assert len(own_references(actions)) == 2


def test_add_page_has_no_dialog_normally(client, logged_in):
    page = text_of(client.get("/add"))
    assert DIALOG not in page
    assert "dialog.js" not in page


def test_invalid_reference_shows_the_error_and_no_dialog(client, actions, existing):
    page = text_of(actions.add_reference(volume="12", pages="12-34", year="20x8"))
    assert DIALOG not in page
    assert len(own_references(actions)) == 1


# editing

def test_editing_into_the_same_reference_shows_the_dialog(client, actions, existing):
    actions.add_reference(**BOOK)
    book = own_references(actions)[0]
    response = edit(client, actions, book.id)
    assert response.status_code == 200
    page = text_of(response)
    dialog = dialog_of(page)
    assert "The same reference already exists (martin2008). Save it anyway?" in dialog
    assert 'value="yes">save</button>' in dialog
    # the edit form stays open with the given values, the book is unchanged
    assert 'id="reference-form"' in page
    assert own_references(actions)[0].entry_type == "book"


def test_save_in_the_dialog_stores_the_changes(client, actions, existing):
    actions.add_reference(**BOOK)
    book = own_references(actions)[0]
    response = edit(client, actions, book.id, confirm=True)
    assert response.status_code == 302
    edited = reference_repository.get_reference(actions.session()["user_id"], book.id)
    assert edited.entry_type == "article"
    assert edited.fields == existing.fields
    assert edited.cite_key == "martin2008a"


def test_saving_a_reference_without_changes_shows_no_dialog(client, actions, existing):
    response = edit(client, actions, existing.id)
    assert response.status_code == 302
    assert DIALOG not in text_of(client.get(f"/references/{existing.id}"))


def test_bibtex_page_has_no_dialog_normally(client, actions, existing):
    page = text_of(client.get(f"/references/{existing.id}/edit"))
    assert DIALOG not in page
    assert "dialog.js" not in page


def test_dialog_script_is_served(client):
    response = client.get("/static/dialog.js")
    assert response.status_code == 200
    assert "showModal" in text_of(response)
