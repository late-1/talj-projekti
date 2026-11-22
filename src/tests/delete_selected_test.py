import re

import pytest

import util
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


def titles(actions):
    return [reference.title for reference in own_references(actions)]


def text_of(response):
    return response.get_data(as_text=True)


def delete_selected(client, actions, ids, csrf_token=None, back=None):
    data = {"reference_id": [str(value) for value in ids]}
    data["csrf_token"] = actions.csrf_token() if csrf_token is None else csrf_token
    if back is not None:
        data["back"] = back
    return client.post("/references/delete", data=data)


# the ids of the selected references

@pytest.mark.parametrize("values,expected", [
    ([], []),
    (["3", "1"], [3, 1]),
    (["2", "2", "5", "2"], [2, 5]),
    (["", "x", "-1", "0", "1.5", " 4", "1e3", "٣"], []),
    (["7", "abc", "8"], [7, 8]),
])
def test_selected_ids(values, expected):
    assert util.selected_ids(values) == expected


def test_selected_ids_are_limited():
    values = [str(number) for number in range(1, util.SELECTED_MAX + 10)]
    assert util.selected_ids(values) == list(range(1, util.SELECTED_MAX + 1))


# the list page

def test_list_has_delete_button_below_advanced(client, references):
    page = text_of(client.get("/references"))
    button = re.search(r'<button[^>]*id="delete-selected"[^>]*>delete</button>', page).group(0)
    assert 'form="delete-selected-form"' in button
    # disabled until a reference is selected
    assert "disabled" in button
    order = [page.index(text) for text in
             ['id="search"', 'id="advanced"', 'id="advanced-fields"', 'id="delete-selected"']]
    assert order == sorted(order)


def test_list_has_select_all_button_on_the_left_of_delete(client, references):
    page = text_of(client.get("/references"))
    # a plain button: it does not send the search or the delete form
    assert '<button type="button" class="button" id="select-all">select all</button>' in page
    assert page.index('id="select-all"') < page.index('id="delete-selected"')


def test_delete_form_has_csrf_token_and_list_address(client, actions, references):
    page = text_of(client.get("/references?query=clean"))
    form = re.search(r'<form action="/references/delete" method="post" id="delete-selected-form">'
                     r'(.*?)</form>', page, re.S).group(1)
    assert f'name="csrf_token" value="{actions.csrf_token()}"' in form
    assert 'name="back" value="/references?query=clean"' in form
    assert 'src="/static/select.js"' in page


def test_every_reference_has_a_checkbox(client, references):
    page = text_of(client.get("/references"))
    checkboxes = re.findall(r'<input type="checkbox" class="reference-select" name="reference_id"'
                            r' value="(\d+)"\s+id="select-\1" form="delete-selected-form"', page)
    assert [int(value) for value in checkboxes] == [reference.id for reference in references]
    assert 'aria-label="select Clean Code"' in page
    # the checkbox is not inside the link of the box
    for card in re.findall(r'<a [^>]*class="reference-card">(.*?)</a>', page, re.S):
        assert "checkbox" not in card


def test_checkbox_label_is_escaped(client, actions, logged_in):
    actions.add_reference(title='"><script>alert(1)</script>')
    page = text_of(client.get("/references"))
    assert "<script>alert(1)</script>" not in page
    assert 'aria-label="select &#34;&gt;&lt;script&gt;' in page


def test_empty_list_has_no_delete_button(client, logged_in):
    page = text_of(client.get("/references"))
    assert "delete-selected" not in page
    assert "select-all" not in page
    assert "select.js" not in page


def test_select_script_is_served(client):
    response = client.get("/static/select.js")
    assert response.status_code == 200
    assert "delete-selected" in text_of(response)


# deleting

def test_selected_references_are_deleted(client, actions, references):
    response = delete_selected(client, actions, [references[0].id, references[2].id])
    assert response.status_code == 302
    assert response.headers["Location"] == "/references"
    assert titles(actions) == ["Refactoring"]


def test_notice_tells_how_many_were_deleted(client, actions, references):
    delete_selected(client, actions, [references[0].id, references[1].id])
    assert "2 references deleted" in text_of(client.get("/references"))
    delete_selected(client, actions, [references[2].id])
    page = text_of(client.get("/references"))
    assert "1 reference deleted" in page
    assert "No references yet" in page


def test_all_references_can_be_deleted(client, actions, references):
    delete_selected(client, actions, [reference.id for reference in references])
    assert not own_references(actions)


def test_delete_returns_to_the_list_the_user_came_from(client, actions, references):
    response = delete_selected(client, actions, [references[0].id],
                               back="/references?query=a&type=book")
    assert response.headers["Location"] == "/references?query=a&type=book"


def test_delete_does_not_follow_other_back_addresses(client, actions, references):
    for back in ["https://evil.example/", "//evil.example/references", "/logout"]:
        response = delete_selected(client, actions, [], back=back)
        assert response.headers["Location"] == "/references"


def test_nothing_selected(client, actions, references):
    for ids in [[], ["x"], ["0"]]:
        response = delete_selected(client, actions, ids)
        assert response.status_code == 302
        assert "No references selected" in text_of(client.get("/references"))
    assert len(own_references(actions)) == 3


def test_unknown_ids_delete_nothing(client, actions, references):
    delete_selected(client, actions, [9999])
    assert "No references deleted" in text_of(client.get("/references"))
    assert len(own_references(actions)) == 3


def test_delete_requires_csrf_token(client, actions, references):
    for token in ["", "wrong"]:
        response = delete_selected(client, actions, [references[0].id], csrf_token=token)
        assert response.status_code == 403
    assert len(own_references(actions)) == 3


def test_delete_is_not_possible_with_get(client, actions, references):
    response = client.get(f"/references/delete?reference_id={references[0].id}")
    assert response.status_code == 405
    assert len(own_references(actions)) == 3


def test_delete_requires_login(client, actions, references):
    actions.logout()
    response = client.post("/references/delete", data={"reference_id": [references[0].id]})
    assert response.status_code == 302
    assert response.headers["Location"] == "/login"
    actions.login("maija")
    assert len(own_references(actions)) == 3


def test_references_of_another_user_are_not_deleted(client, actions, references):
    actions.logout()
    actions.register("uolevi")
    actions.add_reference(title="Own Reference")
    own = own_references(actions)[0]

    # the ids of maija's references are ignored, only uolevi's own one is deleted
    delete_selected(client, actions, [reference.id for reference in references] + [own.id])
    assert "1 reference deleted" in text_of(client.get("/references"))
    assert not own_references(actions)

    actions.logout()
    actions.login("maija")
    assert len(own_references(actions)) == 3


# repository

def test_delete_references_returns_the_number_deleted(actions, references):
    user_id = actions.session()["user_id"]
    ids = [reference.id for reference in references]
    assert reference_repository.delete_references(user_id, []) == 0
    assert reference_repository.delete_references(user_id + 1, ids) == 0
    assert reference_repository.delete_references(user_id, ids[:2]) == 2
    assert reference_repository.delete_references(user_id, ids) == 1
    assert reference_repository.delete_references(user_id, ids) == 0
