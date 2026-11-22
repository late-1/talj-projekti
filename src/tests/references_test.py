import html
import re
from urllib.parse import quote

import pytest

from app import get_back_url
from repositories import reference_repository
from tests.conftest import BOOK, INPROCEEDINGS


@pytest.fixture
def logged_in(actions):
    actions.register("maija")


def own_references(actions):
    return reference_repository.get_references(actions.session()["user_id"])


def text_of(response):
    return response.get_data(as_text=True)


def bibtex_on_page(page):
    match = re.search(r'<pre class="bibtex" id="bibtex">(.*?)</pre>', page, re.S)
    return html.unescape(match.group(1))


# the list

def test_empty_list(client, logged_in):
    page = text_of(client.get("/references"))
    assert "No references yet" in page
    assert 'href="/add"' in page
    assert "reference-card" not in page


def test_list_shows_references(client, actions, logged_in):
    actions.add_reference()
    actions.add_reference(**BOOK)
    actions.add_reference(**INPROCEEDINGS)

    page = text_of(client.get("/references"))
    assert page.count('class="reference-card"') == 3
    assert "3 references" in page
    assert "No references yet" not in page

    for expected in [
        "Clean Code", "Martin, Robert (2008)", "Journal of Software", "article",
        "Refactoring", "Fowler, Martin (1999)", "Addison-Wesley", "book",
        "Extreme Apprenticeship Method", "Vihavainen, Arto and Luukkainen, Matti (2011)",
        "SIGCSE &#39;11", "inproceedings",
    ]:
        assert expected in page


def test_list_with_one_reference_uses_singular(client, actions, logged_in):
    actions.add_reference()
    assert "1 reference<" in text_of(client.get("/references"))


def test_list_is_newest_first(client, actions, logged_in):
    for title in ["First title", "Second title", "Third title"]:
        actions.add_reference(title=title)
    page = text_of(client.get("/references"))
    assert page.index("Third title") < page.index("Second title") < page.index("First title")


def test_list_does_not_show_every_field(client, actions, logged_in):
    actions.add_reference(volume="987", doi="10.1000/hidden")
    page = text_of(client.get("/references"))
    assert "987" not in page
    assert "10.1000/hidden" not in page


def test_each_box_links_to_the_bibtex_page(client, actions, logged_in):
    actions.add_reference()
    actions.add_reference(**BOOK)
    page = text_of(client.get("/references"))
    for reference in own_references(actions):
        assert f'<a href="/references/{reference.id}?back=' in page


def test_list_shows_only_own_references(client, actions, logged_in):
    actions.add_reference(title="Secret of Maija")
    actions.logout()

    actions.register("uolevi")
    actions.add_reference(title="Paper of Uolevi")
    page = text_of(client.get("/references"))
    assert "Paper of Uolevi" in page
    assert "Secret of Maija" not in page
    assert "1 reference<" in page


def test_list_escapes_content(client, actions, logged_in):
    actions.add_reference(title="<script>alert(1)</script>")
    page = text_of(client.get("/references"))
    assert "<script>alert(1)</script>" not in page
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in page


# the BibTeX page

def test_bibtex_page_shows_bibtex(client, actions, logged_in):
    actions.add_reference(volume="12", pages="12-34")
    reference = own_references(actions)[0]

    response = client.get(f"/references/{reference.id}")
    assert response.status_code == 200
    assert bibtex_on_page(text_of(response)) == (
        "@article{martin2008,\n"
        "  author  = {Martin, Robert},\n"
        "  title   = {Clean Code},\n"
        "  journal = {Journal of Software},\n"
        "  year    = {2008},\n"
        "  volume  = {12},\n"
        "  pages   = {12--34}\n"
        "}"
    )


def test_bibtex_page_has_copy_and_back_buttons(client, actions, logged_in):
    actions.add_reference()
    reference = own_references(actions)[0]
    page = text_of(client.get(f"/references/{reference.id}"))

    copy_button = r'<button[^>]*id="copy"[^>]*data-copy-target="bibtex"[^>]*>copy</button>'
    assert re.search(copy_button, page)
    assert '<a href="/references" class="button" id="back">back</a>' in page
    assert 'src="/static/copy.js"' in page
    # back is before copy, so it is on the left
    assert page.index('id="back"') < page.index('id="copy"')


def test_bibtex_page_marks_view_as_current_page(client, actions, logged_in):
    actions.add_reference()
    reference = own_references(actions)[0]
    page = text_of(client.get(f"/references/{reference.id}"))
    assert '<a href="/references" class="active"' in page


def test_bibtex_page_escapes_content(client, actions, logged_in):
    actions.add_reference(title="</pre><script>alert(1)</script>")
    reference = own_references(actions)[0]
    page = text_of(client.get(f"/references/{reference.id}"))
    assert "<script>alert(1)</script>" not in page
    assert "</pre><script>alert(1)</script>" in bibtex_on_page(page)


def page_of_reference(client, actions, **fields):
    actions.add_reference(**fields)
    reference = own_references(actions)[0]
    return text_of(client.get(f"/references/{reference.id}"))


def citation_on_page(page):
    match = re.search(r'<p class="reference-box citation" id="citation">(.*?)</p>', page, re.S)
    return match.group(1)


def details_on_page(page):
    match = re.search(r'<dl class="reference-box reference-data" id="details">(.*?)</dl>',
                      page, re.S)
    return match.group(1)


def test_bibtex_page_has_buttons_above_the_bibtex(client, actions, logged_in):
    page = page_of_reference(client, actions)
    toolbar = page.index('class="bibtex-toolbar"')
    # back on the left, then copy, edit and delete on the right
    assert toolbar < page.index('id="back"') < page.index('id="copy"') \
        < page.index('id="edit"') < page.index('id="delete"') < page.index('id="bibtex"')


def test_bibtex_page_shows_citation_and_details_below_the_bibtex(client, actions, logged_in):
    page = page_of_reference(client, actions, pages="12-34", volume="12")
    # three separate boxes: BibTeX, citation and fields
    assert page.index('id="bibtex"') < page.index('id="citation"') < page.index('id="details"')

    assert citation_on_page(page) == "Martin, Robert (2008). Clean Code. " \
        "<i>Journal of Software</i>, <i>12</i>, 12–34."
    details = details_on_page(page)
    assert "citation" not in details
    for name, label, value in [
        ("type", "type", "article"), ("key", "key", "martin2008"),
        ("author", "author(s)", "Martin, Robert"), ("title", "title", "Clean Code"),
        ("journal", "journal", "Journal of Software"), ("year", "year", "2008"),
        ("volume", "volume", "12"), ("pages", "pages", "12-34"),
    ]:
        assert re.search(rf"<dt>{re.escape(label)}</dt>\s*<dd id=\"data-{name}\">"
                         rf"{re.escape(value)}</dd>", details)


def test_details_show_only_filled_fields_in_form_order(client, actions, logged_in):
    page = page_of_reference(client, actions, **BOOK, edition="2nd")
    details = details_on_page(page)
    names = re.findall(r'<dd id="data-(\w+)">', details)
    assert names == ["type", "key", "author", "title", "publisher", "year", "edition"]
    assert "<dt>isbn</dt>" not in details.lower()


def test_details_use_short_labels(client, actions, logged_in):
    page = page_of_reference(client, actions, **INPROCEEDINGS)
    details = details_on_page(page)
    assert "<dt>book title</dt>" in details
    assert "name of the proceedings" not in details
    assert "In <i>SIGCSE &#39;11</i>." in citation_on_page(page)


def test_details_escape_content(client, actions, logged_in):
    page = page_of_reference(client, actions, title="<script>alert(1)</script>",
                             journal="<b>Journal</b>")
    assert "<script>alert(1)</script>" not in page
    assert "<b>Journal</b>" not in page
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in details_on_page(page)
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in citation_on_page(page)
    assert "<i>&lt;b&gt;Journal&lt;/b&gt;</i>" in citation_on_page(page)


def test_copy_script_is_served(client):
    assert client.get("/static/copy.js").status_code == 200


def test_unknown_reference_is_not_found(client, logged_in):
    assert client.get("/references/123").status_code == 404
    assert client.get("/references/abc").status_code == 404


def test_reference_of_another_user_is_not_found(client, actions, logged_in):
    actions.add_reference(title="Secret of Maija")
    reference = own_references(actions)[0]
    actions.logout()

    actions.register("uolevi")
    response = client.get(f"/references/{reference.id}")
    assert response.status_code == 404
    assert "Secret of Maija" not in text_of(response)


def test_bibtex_page_requires_login(client, actions, logged_in):
    actions.add_reference()
    reference = own_references(actions)[0]
    actions.logout()

    response = client.get(f"/references/{reference.id}")
    assert response.status_code == 302
    assert response.headers["Location"] == "/login"


# going back to the list

def test_back_leads_to_the_list_the_user_came_from(client, actions, logged_in):
    actions.add_reference()
    reference = own_references(actions)[0]

    back = "/references?query=clean&year=2008"
    page = text_of(client.get(f"/references/{reference.id}?back={quote(back, safe='')}"))
    assert '<a href="/references?query=clean&amp;year=2008" class="button" id="back">' in page


def test_list_links_remember_the_current_address(client, actions, logged_in):
    actions.add_reference()
    reference = own_references(actions)[0]

    page = text_of(client.get("/references?query=clean"))
    card = r'<a href="(/references/\d+\?back=[^"]*)" class="reference-card"'
    link = re.search(card, page).group(1)
    assert link == f"/references/{reference.id}?back=/references%3Fquery%3Dclean"

    page = text_of(client.get(html.unescape(link)))
    assert '<a href="/references?query=clean" class="button" id="back">' in page


@pytest.mark.parametrize("back,expected", [
    ("", "/references"),
    ("/references", "/references"),
    ("/references?", "/references"),
    ("/references?query=a&year=2008", "/references?query=a&year=2008"),
    ("https://evil.example/references", "/references"),
    ("//evil.example/references", "/references"),
    ("/referencesevil", "/references"),
    ("/references/../logout", "/references"),
    ("/logout", "/references"),
    ("javascript:alert(1)", "/references"),
    ("/add", "/references"),
])
def test_back_address_is_limited_to_the_list_page(back, expected):
    assert get_back_url(back) == expected
