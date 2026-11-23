import re

import pytest

from bibtex import to_bibtex
from repositories import reference_repository
from tests.conftest import BOOK, INPROCEEDINGS


@pytest.fixture
def logged_in(actions):
    actions.register("maija")


@pytest.fixture
def references(actions, logged_in):
    """Three references of maija, newest first: inproceedings, book, article"""
    actions.add_reference()
    actions.add_reference(**BOOK)
    actions.add_reference(**INPROCEEDINGS)
    return own_references(actions)


def own_references(actions):
    return reference_repository.get_references(actions.session()["user_id"])


def text_of(response):
    return response.get_data(as_text=True)


def create_bib(client, actions, ids, csrf_token=None, back=None):
    data = {"reference_id": [str(value) for value in ids]}
    data["csrf_token"] = actions.csrf_token() if csrf_token is None else csrf_token
    if back is not None:
        data["back"] = back
    return client.post("/references/bib", data=data)


# the button on the list page

def test_create_bib_button_is_between_select_all_and_delete(client, references):
    page = text_of(client.get("/references"))
    button = re.search(r'<button[^>]*id="create-bib"[^>]*>create \.bib</button>', page).group(0)
    assert 'type="submit"' in button
    # sends the same selection as delete, but to another address
    assert 'form="delete-selected-form"' in button
    assert 'formaction="/references/bib"' in button
    # disabled until a reference is selected
    assert "disabled" in button
    assert page.index('id="select-all"') < page.index('id="create-bib"') \
        < page.index('id="delete-selected"')


def test_empty_list_has_no_create_bib_button(client, logged_in):
    assert "create-bib" not in text_of(client.get("/references"))


def test_select_script_handles_create_bib(client):
    assert "create-bib" in text_of(client.get("/static/select.js"))


# the file

def test_file_has_the_selected_references_as_bibtex(client, actions, references):
    response = create_bib(client, actions, [references[0].id, references[2].id])
    assert response.status_code == 200
    # newest first, as on the list, an empty line between the entries
    assert text_of(response) == to_bibtex(references[0]) + "\n\n" + to_bibtex(references[2]) + "\n"
    assert text_of(response).startswith("@inproceedings{vihavainen2011,\n")
    assert "@article{martin2008," in text_of(response)
    assert "@book{" not in text_of(response)


def test_file_order_does_not_depend_on_the_order_of_selecting(client, actions, references):
    ids = [reference.id for reference in references]
    first = text_of(create_bib(client, actions, ids))
    second = text_of(create_bib(client, actions, list(reversed(ids))))
    assert first == second
    assert first.count("\n@") == 2


def test_file_is_downloaded_as_references_bib(client, actions, references):
    response = create_bib(client, actions, [references[0].id])
    assert response.mimetype == "application/x-bibtex"
    assert response.headers["Content-Disposition"] == 'attachment; filename="references.bib"'


def test_file_keeps_special_characters(client, actions, logged_in):
    actions.add_reference(title="Mäkelä & <Co>", author="Ääkkönen, Öljy")
    reference = own_references(actions)[0]
    content = text_of(create_bib(client, actions, [reference.id]))
    # the same as on the BibTeX page: & is escaped for LaTeX, HTML is not escaped
    assert "title   = {Mäkelä \\& <Co>}" in content
    assert "author  = {Ääkkönen, Öljy}" in content


def test_creating_a_file_changes_nothing(client, actions, references):
    before = [(reference.id, reference.fields) for reference in references]
    create_bib(client, actions, [reference.id for reference in references])
    assert [(reference.id, reference.fields) for reference in own_references(actions)] == before


def test_nothing_selected(client, actions, references):
    for ids in [[], ["x"], [9999]]:
        response = create_bib(client, actions, ids, back="/references?query=clean")
        assert response.status_code == 302
        assert response.headers["Location"] == "/references?query=clean"
        assert "No references selected" in text_of(client.get("/references"))


def test_other_back_addresses_are_not_followed(client, actions, references):
    response = create_bib(client, actions, [], back="https://evil.example/")
    assert response.headers["Location"] == "/references"


def test_file_has_only_own_references(client, actions, references):
    actions.logout()
    actions.register("uolevi")
    actions.add_reference(title="Own Reference")
    own = own_references(actions)[0]

    ids = [reference.id for reference in references] + [own.id]
    content = text_of(create_bib(client, actions, ids))
    assert content == to_bibtex(own) + "\n"

    # only maija's references: nothing to put in the file
    response = create_bib(client, actions, [reference.id for reference in references])
    assert response.status_code == 302


def test_create_bib_requires_csrf_token(client, actions, references):
    for token in ["", "wrong"]:
        assert create_bib(client, actions, [references[0].id], csrf_token=token).status_code == 403


def test_create_bib_is_not_possible_with_get(client, references):
    assert client.get(f"/references/bib?reference_id={references[0].id}").status_code == 405


def test_create_bib_requires_login(client, actions, references):
    actions.logout()
    response = client.post("/references/bib", data={"reference_id": [references[0].id]})
    assert response.status_code == 302
    assert response.headers["Location"] == "/login"


# repository

def test_get_references_by_ids(actions, references):
    user_id = actions.session()["user_id"]
    ids = [reference.id for reference in references]
    assert reference_repository.get_references_by_ids(user_id, []) == []
    assert reference_repository.get_references_by_ids(user_id + 1, ids) == []
    found = reference_repository.get_references_by_ids(user_id, [ids[2], ids[0], 9999])
    assert [reference.id for reference in found] == [ids[0], ids[2]]
