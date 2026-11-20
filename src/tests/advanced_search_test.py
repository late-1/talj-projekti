import html
import re

import pytest

from repositories import reference_repository, user_repository
from tests.conftest import BOOK, INPROCEEDINGS
from util import SEARCH_MAX_LENGTH, clean_search_params, search_filters

ARTICLE_FIELDS = {
    "author": "Dijkstra, Edsger W.", "title": "Go To Statement Considered Harmful",
    "journal": "Communications of the ACM", "year": "1968", "pages": "147-148",
}
BOOK_FIELDS = {
    "author": "Martin, Robert C.", "title": "Clean Code", "publisher": "Prentice Hall",
    "year": "2008", "address": "Dijkstra Street",
}
PAPER_FIELDS = {
    "author": "Vihavainen, Arto and Mäkelä, Äänis", "title": "Extreme Apprenticeship Method",
    "booktitle": "Proceedings of SIGCSE", "year": "2011", "publisher": "ACM",
}
SECOND_BOOK_FIELDS = {
    "author": "Fowler, Martin", "title": "Refactoring: Improving the Design of Existing Code",
    "publisher": "Addison-Wesley", "year": "1999",
}


# cleaning the search fields of the address

def test_clean_search_params_keeps_fields_with_values():
    args = {"query": "clean", "author": "martin", "title": "code", "venue": "hall",
            "key": "martin2008", "year_from": "2000", "year_to": "2010", "type": "book"}
    assert clean_search_params(args) == args


def test_clean_search_params_drops_empty_and_unknown_fields():
    args = {"query": "", "author": "   ", "title": "code", "type": "", "page": "2", "back": "/x"}
    assert clean_search_params(args) == {"title": "code"}
    assert not clean_search_params({})


def test_clean_search_params_cleans_whitespace_and_length():
    assert clean_search_params({"author": "  robert \t martin "}) == {"author": "robert martin"}
    assert clean_search_params({"title": "a" * 500}) == {"title": "a" * SEARCH_MAX_LENGTH}
    cleaned = clean_search_params({"title": "a" * (SEARCH_MAX_LENGTH - 1) + " b"})
    assert cleaned == {"title": "a" * (SEARCH_MAX_LENGTH - 1)}


# picking the valid filters

def test_search_filters_with_valid_fields():
    params = {"query": "clean", "author": "martin", "title": "code", "venue": "hall",
              "key": "martin2008", "year_from": "2000", "year_to": "2010", "type": "book"}
    filters, errors = search_filters(params)
    assert filters == {name: value for name, value in params.items() if name != "query"}
    assert not errors


def test_search_filters_without_fields():
    assert search_filters({}) == ({}, [])
    assert search_filters({"query": "clean"}) == ({}, [])


@pytest.mark.parametrize("year", ["20", "20000", "abcd", "2008a", "-200"])
def test_search_filters_rejects_invalid_years(year):
    filters, errors = search_filters({"year_from": year, "author": "martin"})
    assert filters == {"author": "martin"}
    assert errors == ["Years must be four-digit numbers"]

    filters, errors = search_filters({"year_from": year, "year_to": year})
    assert not filters
    assert errors == ["Years must be four-digit numbers"]


def test_search_filters_rejects_unknown_type():
    filters, errors = search_filters({"type": "phdthesis", "year_to": "2010"})
    assert filters == {"year_to": "2010"}
    assert errors == ["Unknown reference type"]


# filtering in the repository

@pytest.fixture
def user():
    user = user_repository.create_user("maija", "secret-password")
    reference_repository.create_reference(user.id, "article", ARTICLE_FIELDS)
    reference_repository.create_reference(user.id, "book", BOOK_FIELDS)
    reference_repository.create_reference(user.id, "inproceedings", PAPER_FIELDS, "xp-method")
    reference_repository.create_reference(user.id, "book", SECOND_BOOK_FIELDS)
    return user


ALL = ["fowler1999", "xp-method", "martin2008", "dijkstra1968"]


def found(user, query="", **filters):
    references = reference_repository.get_references(user.id, query, filters)
    return [reference.cite_key for reference in references]


def test_no_filters_returns_everything(user):
    assert found(user) == ALL
    assert reference_repository.get_references(user.id, "", None)[0].cite_key == "fowler1999"
    names = ["author", "title", "venue", "key", "year_from", "year_to", "type"]
    assert found(user, **dict.fromkeys(names, "")) == ALL


@pytest.mark.parametrize("filters,keys", [
    # author looks only at the author
    ({"author": "martin"}, ["fowler1999", "martin2008"]),
    ({"author": "dijkstra"}, ["dijkstra1968"]),
    ({"author": "MARTIN robert"}, ["martin2008"]),
    ({"author": "robert martin"}, ["martin2008"]),
    ({"author": "mäkelä"}, ["xp-method"]),
    ({"author": "ÄÄNIS"}, ["xp-method"]),
    ({"author": "clean"}, []),
    # title looks only at the title
    ({"title": "code"}, ["fowler1999", "martin2008"]),
    ({"title": "clean code"}, ["martin2008"]),
    ({"title": "code clean"}, ["martin2008"]),
    ({"title": "martin"}, []),
    ({"title": "appren"}, ["xp-method"]),
    # venue looks at the journal, the proceedings and the publisher
    ({"venue": "communications"}, ["dijkstra1968"]),
    ({"venue": "sigcse"}, ["xp-method"]),
    ({"venue": "addison"}, ["fowler1999"]),
    ({"venue": "acm"}, ["xp-method", "dijkstra1968"]),
    ({"venue": "proceedings acm"}, ["xp-method"]),
    ({"venue": "street"}, []),
    ({"venue": "code"}, []),
    # key
    ({"key": "martin2008"}, ["martin2008"]),
    ({"key": "martin"}, ["martin2008"]),
    ({"key": "XP-"}, ["xp-method"]),
    ({"key": "19"}, ["fowler1999", "dijkstra1968"]),
    ({"key": "fowler dijkstra"}, []),
    # years, both ends are included
    ({"year_from": "2008"}, ["xp-method", "martin2008"]),
    ({"year_from": "2009"}, ["xp-method"]),
    ({"year_from": "2012"}, []),
    ({"year_to": "1999"}, ["fowler1999", "dijkstra1968"]),
    ({"year_to": "1998"}, ["dijkstra1968"]),
    ({"year_to": "1967"}, []),
    ({"year_from": "1999", "year_to": "2008"}, ["fowler1999", "martin2008"]),
    ({"year_from": "2008", "year_to": "2008"}, ["martin2008"]),
    ({"year_from": "2000", "year_to": "2007"}, []),
    ({"year_from": "2010", "year_to": "2000"}, []),
    # type
    ({"type": "book"}, ["fowler1999", "martin2008"]),
    ({"type": "article"}, ["dijkstra1968"]),
    ({"type": "inproceedings"}, ["xp-method"]),
    ({"type": "phdthesis"}, []),
    # every filter has to match
    ({"author": "martin", "type": "book", "year_from": "2000"}, ["martin2008"]),
    ({"author": "martin", "title": "refactoring"}, ["fowler1999"]),
    ({"venue": "acm", "year_to": "2000"}, ["dijkstra1968"]),
    ({"type": "book", "venue": "acm"}, []),
    ({"author": "martin", "title": "code", "venue": "hall", "key": "martin",
      "year_from": "2008", "year_to": "2008", "type": "book"}, ["martin2008"]),
])
def test_filters(user, filters, keys):
    assert found(user, **filters) == keys


def test_filter_differs_from_the_basic_search(user):
    # the basic search finds the word from any field
    assert found(user, "dijkstra") == ["martin2008", "dijkstra1968"]
    assert found(user, author="dijkstra") == ["dijkstra1968"]
    assert found(user, "acm") == ["xp-method", "dijkstra1968"]
    assert found(user, title="acm") == []


def test_filters_are_combined_with_the_basic_search(user):
    assert found(user, "code") == ["fowler1999", "martin2008"]
    assert found(user, "code", year_from="2000") == ["martin2008"]
    assert found(user, "code", author="fowler") == ["fowler1999"]
    assert found(user, "code", type="article") == []
    assert found(user, "dijkstra", type="book") == ["martin2008"]


@pytest.mark.parametrize("value", ["%", "_", "'", '"', "\\", "'; DROP TABLE users;--", "c_ean"])
def test_special_characters_have_no_special_meaning_in_filters(user, value):
    for name in ["author", "title", "venue", "key", "type"]:
        assert found(user, **{name: value}) == []
    assert found(user) == ALL


def test_filters_return_only_own_references(user):
    other = user_repository.create_user("uolevi", "secret-password")
    reference_repository.create_reference(other.id, "book", BOOK_FIELDS, "others-book")

    assert found(user, type="book") == ["fowler1999", "martin2008"]
    assert found(other, type="book") == ["others-book"]
    assert found(other, author="dijkstra") == []
    assert found(other, year_to="2000") == []


# the list page

@pytest.fixture
def logged_in(client, actions):
    actions.register("maija")
    # article: Martin, Robert: Clean Code, 2008, Journal of Software
    actions.add_reference()
    # book: Fowler, Martin: Refactoring, 1999, Addison-Wesley
    actions.add_reference(**BOOK)
    # inproceedings: Vihavainen...: Extreme Apprenticeship Method, 2011, SIGCSE '11
    actions.add_reference(**INPROCEEDINGS)


def page_of(client, url):
    response = client.get(url)
    assert response.status_code == 200
    return response.get_data(as_text=True)


def titles(page):
    return re.findall(r'<span class="reference-title">(.*?)</span>', page)


def test_advanced_part_is_closed_by_default(client, logged_in):
    for url in ["/references", "/references?query=clean"]:
        page = page_of(client, url)
        assert '<details class="advanced" id="advanced" >' in page
        assert '<summary class="button">advanced</summary>' in page


def test_advanced_part_is_below_the_search_field(client, logged_in):
    page = page_of(client, "/references")
    assert page.index('name="query"') < page.index("<details") < page.index("reference-card")


def test_advanced_part_has_fields(client, logged_in):
    page = page_of(client, "/references")
    advanced = page[page.index("<details"):page.index("</details>")]
    for name in ["author", "title", "venue", "key", "year_from", "year_to"]:
        assert f'<input type="text" name="{name}"' in advanced
    for value in ["", "article", "book", "inproceedings"]:
        assert re.search(
            rf'<input type="radio" name="type" id="type-\w+" value="{value}"', advanced
        )
    assert '<input type="radio" name="type" id="type-any" value="" checked />' in advanced
    # everything is in the same form with the basic search field
    assert page.count("<form") == 1
    positions = [page.index(tag) for tag in ["<form", "<details", "</details>", "</form>"]]
    assert positions == sorted(positions)


@pytest.mark.parametrize("url,expected", [
    ("/references?author=martin", ["Refactoring", "Clean Code"]),
    ("/references?author=fowler", ["Refactoring"]),
    ("/references?title=clean", ["Clean Code"]),
    ("/references?title=martin", []),
    ("/references?venue=addison", ["Refactoring"]),
    ("/references?venue=sigcse", ["Extreme Apprenticeship Method"]),
    ("/references?venue=journal", ["Clean Code"]),
    ("/references?key=vihavainen", ["Extreme Apprenticeship Method"]),
    ("/references?year_from=2008", ["Extreme Apprenticeship Method", "Clean Code"]),
    ("/references?year_to=2008", ["Refactoring", "Clean Code"]),
    ("/references?year_from=2000&year_to=2010", ["Clean Code"]),
    ("/references?type=book", ["Refactoring"]),
    ("/references?type=inproceedings", ["Extreme Apprenticeship Method"]),
    ("/references?author=martin&type=article", ["Clean Code"]),
    ("/references?author=martin&year_to=2000", ["Refactoring"]),
    ("/references?query=martin&title=refactoring", ["Refactoring"]),
    ("/references?query=martin&type=inproceedings", []),
    ("/references?query=code&author=martin&title=clean&venue=software&key=martin2008"
     "&year_from=2008&year_to=2008&type=article", ["Clean Code"]),
])
def test_advanced_search_filters_the_list(client, logged_in, url, expected):
    page = page_of(client, url)
    assert titles(page) == expected
    if expected:
        assert f"{len(expected)} of 3 references" in page
    else:
        assert "No references found" in page
    assert 'id="clear-search"' in page


def test_advanced_part_stays_open_and_keeps_its_values(client, logged_in):
    page = page_of(
        client,
        "/references?query=code&author=martin&title=clean&venue=software&key=martin2008"
        "&year_from=2008&year_to=2009&type=article",
    )
    assert '<details class="advanced" id="advanced" open>' in page
    for name, value in [("query", "code"), ("author", "martin"), ("title", "clean"),
                        ("venue", "software"), ("key", "martin2008"),
                        ("year_from", "2008"), ("year_to", "2009")]:
        assert re.search(rf'name="{name}" id="{name}" value="{value}"', page)
    assert '<input type="radio" name="type" id="type-article" value="article" checked />' in page
    assert '<input type="radio" name="type" id="type-any" value=""  />' in page


@pytest.mark.parametrize(
    "name", ["author", "title", "venue", "key", "year_from", "year_to", "type"]
)
def test_any_advanced_field_keeps_the_advanced_part_open(client, logged_in, name):
    value = {"year_from": "2000", "year_to": "2020", "type": "book"}.get(name, "a")
    page = page_of(client, f"/references?{name}={value}")
    assert '<details class="advanced" id="advanced" open>' in page


def test_empty_fields_are_dropped_from_the_address(client, logged_in):
    # this is what the browser sends when only the author is filled
    response = client.get(
        "/references?query=&author=martin&title=&venue=&key=&year_from=&year_to=&type="
    )
    assert response.status_code == 302
    assert response.headers["Location"] == "/references?author=martin"

    response = client.get("/references?query=&author=&title=&venue=&key=&year_from=&year_to=&type=")
    assert response.headers["Location"] == "/references"


def test_address_is_cleaned(client, logged_in):
    response = client.get("/references?author=++robert+++martin+&page=3")
    assert response.headers["Location"] == "/references?author=robert+martin"


def test_clean_address_is_not_redirected(client, logged_in):
    assert client.get("/references?author=robert+martin&type=book").status_code == 200


@pytest.mark.parametrize("url", [
    "/references?year_from=20",
    "/references?year_to=abcd",
    "/references?year_from=1&year_to=2",
])
def test_invalid_year_shows_an_error_and_is_not_used(client, logged_in, url):
    page = page_of(client, url)
    assert page.count("Years must be four-digit numbers") == 1
    assert len(titles(page)) == 3
    # the field keeps the value, so that it can be fixed
    assert '<details class="advanced" id="advanced" open>' in page


def test_invalid_year_does_not_remove_other_filters(client, logged_in):
    page = page_of(client, "/references?year_from=abcd&author=fowler")
    assert "Years must be four-digit numbers" in page
    assert titles(page) == ["Refactoring"]
    assert 'value="abcd"' in page


def test_unknown_type_shows_an_error_and_is_not_used(client, logged_in):
    page = page_of(client, "/references?type=phdthesis")
    assert "Unknown reference type" in page
    assert len(titles(page)) == 3
    assert '<input type="radio" name="type" id="type-any" value="" checked />' in page


def test_advanced_values_are_escaped(client, logged_in):
    page = page_of(client, '/references?author="><script>alert(1)</script>')
    assert "<script>alert(1)</script>" not in page
    assert "&lt;script&gt;" in page


def test_advanced_search_is_limited_to_own_references(client, actions, logged_in):
    actions.logout()
    actions.register("uolevi")
    actions.add_reference(title="Clean Architecture")

    page = page_of(client, "/references?author=martin")
    assert titles(page) == ["Clean Architecture"]
    assert titles(page_of(client, "/references?type=book")) == []


def test_advanced_search_requires_login(client):
    response = client.get("/references?author=martin")
    assert response.headers["Location"] == "/login"


def test_back_returns_to_the_advanced_search(client, logged_in):
    url = "/references?author=martin&year_to=2000&type=book"
    page = page_of(client, url)
    link = html.unescape(re.search(r'<a href="([^"]*)" class="reference-card"', page).group(1))

    page = page_of(client, link)
    back = html.unescape(re.search(r'<a href="([^"]*)" class="button" id="back">', page).group(1))
    assert back == url

    page = page_of(client, back)
    assert titles(page) == ["Refactoring"]
    assert '<details class="advanced" id="advanced" open>' in page
