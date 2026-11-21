import html
import re
from urllib.parse import quote

import pytest

from repositories import reference_repository
from tests.conftest import ARTICLE, BOOK


@pytest.fixture
def logged_in(actions):
    actions.register("maija")


@pytest.fixture
def reference(actions, logged_in):
    actions.add_reference(volume="12", pages="12-34")
    return own_references(actions)[0]


def own_references(actions):
    return reference_repository.get_references(actions.session()["user_id"])


def text_of(response):
    return response.get_data(as_text=True)


def bibtex_on_page(page):
    match = re.search(r'<pre class="bibtex" id="bibtex">(.*?)</pre>', page, re.S)
    return html.unescape(match.group(1))


def edit(client, actions, reference_id, csrf_token=None, back=None, **fields):
    """Posts the edit form; the defaults make a valid article"""
    data = dict(ARTICLE)
    data.update(fields)
    data["csrf_token"] = actions.csrf_token() if csrf_token is None else csrf_token
    url = f"/references/{reference_id}/edit"
    if back:
        url += "?back=" + quote(back, safe="")
    return client.post(url, data=data)


def delete(client, actions, reference_id, csrf_token=None, back=None):
    url = f"/references/{reference_id}/delete"
    if back:
        url += "?back=" + quote(back, safe="")
    token = actions.csrf_token() if csrf_token is None else csrf_token
    return client.post(url, data={"csrf_token": token})


# buttons of the BibTeX page

def test_bibtex_page_has_edit_and_delete_buttons(client, actions, reference):
    page = text_of(client.get(f"/references/{reference.id}"))
    assert f'<a href="/references/{reference.id}/edit" class="button" id="edit">edit</a>' in page
    delete_form = f'<form action="/references/{reference.id}/delete" method="post" id="delete-form"'
    assert delete_form in page
    assert '<button type="submit" class="button" id="delete">delete</button>' in page
    # copy, edit and delete are in this order from left to right
    assert page.index('id="copy"') < page.index('id="edit"') < page.index('id="delete"')


def test_bibtex_page_has_no_edit_form_by_default(client, actions, reference):
    page = text_of(client.get(f"/references/{reference.id}"))
    assert 'id="reference-form"' not in page
    assert 'id="save"' not in page
    assert 'id="cancel"' not in page


def test_buttons_keep_the_list_the_user_came_from(client, actions, reference):
    back = "/references?query=clean"
    page = text_of(client.get(f"/references/{reference.id}?back={quote(back, safe='')}"))
    encoded = "back=%2Freferences%3Fquery%3Dclean"
    assert f'href="/references/{reference.id}/edit?{encoded}"' in page
    assert f'action="/references/{reference.id}/delete?{encoded}"' in page


# the edit form

def test_edit_page_shows_form_above_the_bibtex(client, actions, reference):
    response = client.get(f"/references/{reference.id}/edit")
    assert response.status_code == 200
    page = text_of(response)

    assert f'<form action="/references/{reference.id}/edit" method="post"' in page
    # the buttons stay above the form, and the form is above the BibTeX
    order = [page.index(f'id="{name}"') for name in ["delete", "reference-form", "bibtex"]]
    assert order == sorted(order)
    assert '<input type="submit" value="save" id="save" />' in page
    assert f'<a href="/references/{reference.id}" class="button" id="cancel">cancel</a>' in page
    # save and cancel are below the fields
    assert page.index('id="cite_key"') < page.index('id="save"') < page.index('id="cancel"')
    assert 'src="/static/reference_form.js"' in page
    assert "@article{martin2008," in bibtex_on_page(page)


def test_edit_form_has_the_current_values(client, actions, reference):
    page = text_of(client.get(f"/references/{reference.id}/edit"))
    assert 'id="type-article" value="article"\n               checked' in page
    for name, value in [
        ("author", "Martin, Robert"), ("title", "Clean Code"),
        ("journal", "Journal of Software"), ("year", "2008"),
        ("volume", "12"), ("pages", "12-34"), ("cite_key", "martin2008"),
    ]:
        assert f'name="{name}" id="{name}" value="{value}"' in page
    assert 'name="doi" id="doi" value=""' in page


def test_edit_form_of_a_book_has_book_chosen(client, actions, logged_in):
    actions.add_reference(**BOOK)
    reference = own_references(actions)[0]
    page = text_of(client.get(f"/references/{reference.id}/edit"))
    assert 'id="type-book" value="book"\n               checked' in page
    assert 'name="publisher" id="publisher" value="Addison-Wesley"' in page


def test_edit_page_marks_edit_button_and_view_link(client, actions, reference):
    page = text_of(client.get(f"/references/{reference.id}/edit"))
    assert 'class="button current" id="edit"' in page
    assert '<a href="/references" class="active"' in page


def test_edit_page_keeps_the_list_the_user_came_from(client, actions, reference):
    back = "/references?query=clean"
    page = text_of(client.get(f"/references/{reference.id}/edit?back={quote(back, safe='')}"))
    encoded = "back=%2Freferences%3Fquery%3Dclean"
    assert f'<form action="/references/{reference.id}/edit?{encoded}" method="post"' in page
    assert f'<a href="/references/{reference.id}?{encoded}" class="button" id="cancel">' in page
    assert '<a href="/references?query=clean" class="button" id="back">' in page


def test_edit_page_escapes_content(client, actions, logged_in):
    actions.add_reference(title='"><script>alert(1)</script>')
    reference = own_references(actions)[0]
    page = text_of(client.get(f"/references/{reference.id}/edit"))
    assert "<script>alert(1)</script>" not in page


# saving

def test_save_updates_the_reference(client, actions, reference):
    response = edit(client, actions, reference.id, title="Cleaner Code", year="2009",
                    volume="13", cite_key="martin2008")
    assert response.status_code == 302
    assert response.headers["Location"] == f"/references/{reference.id}"

    references = own_references(actions)
    assert len(references) == 1
    assert references[0].id == reference.id
    assert references[0].cite_key == "martin2008"
    assert references[0].fields == {
        "author": "Martin, Robert", "title": "Cleaner Code",
        "journal": "Journal of Software", "year": "2009", "volume": "13",
    }


def test_after_save_the_bibtex_is_updated_and_the_form_is_gone(client, actions, reference):
    response = edit(client, actions, reference.id, title="Cleaner Code", cite_key="martin2008")
    page = text_of(client.get(response.headers["Location"]))
    assert "title   = {Cleaner Code}" in bibtex_on_page(page)
    assert "pages" not in bibtex_on_page(page)
    assert 'id="reference-form"' not in page


def test_save_returns_to_the_page_with_the_same_back_address(client, actions, reference):
    response = edit(client, actions, reference.id, back="/references?query=clean",
                    cite_key="martin2008")
    assert response.headers["Location"] == \
        f"/references/{reference.id}?back=%2Freferences%3Fquery%3Dclean"


def test_save_can_change_the_key(client, actions, reference):
    edit(client, actions, reference.id, cite_key="cleancode")
    assert own_references(actions)[0].cite_key == "cleancode"


def test_save_with_empty_key_generates_the_key_again(client, actions, reference):
    edit(client, actions, reference.id, author="Fowler, Martin", year="1999", cite_key="")
    assert own_references(actions)[0].cite_key == "fowler1999"


def test_save_with_empty_key_can_reuse_the_own_key(client, actions, reference):
    edit(client, actions, reference.id, title="Cleaner Code", cite_key="")
    assert own_references(actions)[0].cite_key == "martin2008"


def test_generated_key_avoids_keys_of_other_references(client, actions, reference):
    actions.add_reference(**BOOK)
    edit(client, actions, reference.id, author="Fowler, Martin", year="1999", cite_key="")
    keys = sorted(r.cite_key for r in own_references(actions))
    assert keys == ["fowler1999", "fowler1999a"]


def test_save_can_change_the_type_and_empties_old_fields(client, actions, reference):
    response = edit(client, actions, reference.id, **BOOK, cite_key="martin2008")
    assert response.status_code == 302

    updated = own_references(actions)[0]
    assert updated.entry_type == "book"
    assert updated.fields == {
        "author": "Fowler, Martin", "title": "Refactoring",
        "publisher": "Addison-Wesley", "year": "1999",
    }
    # fields of the old type do not come back with the old type
    edit(client, actions, reference.id, cite_key="martin2008")
    assert "volume" not in own_references(actions)[0].fields


def test_save_does_not_change_other_references(client, actions, reference):
    actions.add_reference(**BOOK)
    edit(client, actions, reference.id, title="Cleaner Code", cite_key="martin2008")
    titles = sorted(r.title for r in own_references(actions))
    assert titles == ["Cleaner Code", "Refactoring"]


@pytest.mark.parametrize("fields,message", [
    ({"title": ""}, "Title is required"),
    ({"year": "08"}, "Year must be a four-digit number"),
    ({"title": "Clean {Code"}, "braces"),
    ({"cite_key": "bad key"}, "Key"),
    ({"entry_type": "thesis"}, "reference type"),
])
def test_invalid_values_are_not_saved(client, actions, reference, fields, message):
    response = edit(client, actions, reference.id, **fields)
    assert response.status_code == 200
    page = text_of(response)
    assert message in page
    # the form stays open and the reference is unchanged
    assert 'id="reference-form"' in page
    assert "title   = {Clean Code}" in bibtex_on_page(page)
    unchanged = own_references(actions)[0]
    assert unchanged.title == "Clean Code"
    assert unchanged.year == "2008"
    assert unchanged.cite_key == "martin2008"


def test_form_keeps_given_values_after_an_error(client, actions, reference):
    page = text_of(edit(client, actions, reference.id, title="Changed Title", year="08",
                        cite_key="newkey"))
    assert 'name="title" id="title" value="Changed Title"' in page
    assert 'name="year" id="year" value="08"' in page
    assert 'name="cite_key" id="cite_key" value="newkey"' in page


def test_key_of_another_own_reference_is_rejected(client, actions, reference):
    actions.add_reference(**BOOK)
    response = edit(client, actions, reference.id, cite_key="fowler1999")
    assert response.status_code == 200
    assert "Key fowler1999 is already in use" in text_of(response)
    assert sorted(r.cite_key for r in own_references(actions)) == ["fowler1999", "martin2008"]


def test_key_of_another_user_can_be_used(client, actions, logged_in):
    actions.add_reference(cite_key="shared")
    actions.logout()
    actions.register("uolevi")
    actions.add_reference()
    reference = own_references(actions)[0]
    assert edit(client, actions, reference.id, cite_key="shared").status_code == 302
    assert own_references(actions)[0].cite_key == "shared"


def test_save_requires_csrf_token(client, actions, reference):
    for token in ["", "wrong"]:
        response = edit(client, actions, reference.id, csrf_token=token, title="Changed")
        assert response.status_code == 403
    assert own_references(actions)[0].title == "Clean Code"


# deleting

def test_delete_removes_the_reference(client, actions, reference):
    response = delete(client, actions, reference.id)
    assert response.status_code == 302
    assert response.headers["Location"] == "/references"
    assert own_references(actions) == []
    assert client.get(f"/references/{reference.id}").status_code == 404


def test_delete_shows_a_notice_on_the_list(client, actions, reference):
    delete(client, actions, reference.id)
    page = text_of(client.get("/references"))
    assert "Reference martin2008 deleted" in page
    assert "No references yet" in page


def test_delete_returns_to_the_list_the_user_came_from(client, actions, reference):
    response = delete(client, actions, reference.id, back="/references?query=clean")
    assert response.headers["Location"] == "/references?query=clean"


def test_delete_does_not_follow_other_back_addresses(client, actions, reference):
    response = delete(client, actions, reference.id, back="https://evil.example/")
    assert response.headers["Location"] == "/references"


def test_delete_removes_only_that_reference(client, actions, reference):
    actions.add_reference(**BOOK)
    delete(client, actions, reference.id)
    assert [r.title for r in own_references(actions)] == ["Refactoring"]


def test_deleted_key_can_be_used_again(client, actions, reference):
    delete(client, actions, reference.id)
    actions.add_reference()
    assert own_references(actions)[0].cite_key == "martin2008"


def test_delete_requires_csrf_token(client, actions, reference):
    for token in ["", "wrong"]:
        assert delete(client, actions, reference.id, csrf_token=token).status_code == 403
    assert len(own_references(actions)) == 1


def test_delete_is_not_possible_with_get(client, actions, reference):
    assert client.get(f"/references/{reference.id}/delete").status_code == 405
    assert len(own_references(actions)) == 1


def test_unknown_reference_cannot_be_edited_or_deleted(client, actions, logged_in):
    assert client.get("/references/123/edit").status_code == 404
    assert edit(client, actions, 123).status_code == 404
    assert delete(client, actions, 123).status_code == 404


# other users and logged out users

def test_reference_of_another_user_cannot_be_edited_or_deleted(client, actions, reference):
    actions.logout()
    actions.register("uolevi")

    response = client.get(f"/references/{reference.id}/edit")
    assert response.status_code == 404
    assert "Clean Code" not in text_of(response)
    assert edit(client, actions, reference.id, title="Stolen").status_code == 404
    assert delete(client, actions, reference.id).status_code == 404

    actions.logout()
    actions.login("maija")
    references = own_references(actions)
    assert len(references) == 1
    assert references[0].title == "Clean Code"


def test_editing_and_deleting_require_login(client, actions, reference):
    actions.logout()
    for response in [
        client.get(f"/references/{reference.id}/edit"),
        client.post(f"/references/{reference.id}/edit", data=ARTICLE),
        client.post(f"/references/{reference.id}/delete"),
    ]:
        assert response.status_code == 302
        assert response.headers["Location"] == "/login"

    actions.login("maija")
    assert own_references(actions)[0].title == "Clean Code"


# repository

def test_update_reference_returns_none_for_missing_reference(actions, logged_in):
    user_id = actions.session()["user_id"]
    fields = {key: value for key, value in ARTICLE.items() if key != "entry_type"}
    assert reference_repository.update_reference(user_id, 123, "article", fields, "key") is None


def test_delete_reference_tells_whether_something_was_deleted(actions, reference):
    user_id = actions.session()["user_id"]
    assert reference_repository.delete_reference(user_id + 1, reference.id) is False
    assert reference_repository.delete_reference(user_id, reference.id) is True
    assert reference_repository.delete_reference(user_id, reference.id) is False


def test_get_cite_keys_can_leave_out_a_reference(actions, reference):
    user_id = actions.session()["user_id"]
    actions.add_reference(**BOOK)
    assert reference_repository.get_cite_keys(user_id) == {"martin2008", "fowler1999"}
    assert reference_repository.get_cite_keys(user_id, exclude_id=reference.id) == {"fowler1999"}
