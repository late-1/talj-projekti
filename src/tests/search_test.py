import html
import re

import pytest

from repositories import reference_repository, user_repository
from tests.conftest import BOOK, INPROCEEDINGS
from util import SEARCH_MAX_LENGTH, SEARCH_MAX_WORDS, search_words

ARTICLE_FIELDS = {
    "author": "Dijkstra, Edsger W.", "title": "Go To Statement Considered Harmful",
    "journal": "Communications of the ACM", "year": "1968", "volume": "11",
    "number": "3", "pages": "147-148", "doi": "10.1145/362929.362947",
}
BOOK_FIELDS = {
    "author": "Martin, Robert C.", "title": "Clean Code", "publisher": "Prentice Hall",
    "year": "2008", "address": "Upper Saddle River", "isbn": "978-0132350884",
}
PAPER_FIELDS = {
    "author": "Vihavainen, Arto and Mäkelä, Äänis", "title": "Extreme Apprenticeship Method",
    "booktitle": "Proceedings of SIGCSE", "year": "2011", "publisher": "ACM",
}


# splitting the search into words

@pytest.mark.parametrize("query,words", [
    ("", []),
    ("   ", []),
    ("clean", ["clean"]),
    ("Clean CODE", ["clean", "code"]),
    ("  clean \t code\n", ["clean", "code"]),
    ("clean clean Clean", ["clean"]),
    ("MÄKELÄ", ["mäkelä"]),
])
def test_search_words(query, words):
    assert search_words(query) == words


def test_search_words_are_limited():
    many = " ".join(f"word{number}" for number in range(100))
    assert len(search_words(many)) <= SEARCH_MAX_WORDS
    assert search_words("a" * 500) == ["a" * SEARCH_MAX_LENGTH]


# searching in the repository

@pytest.fixture
def user():
    user = user_repository.create_user("maija", "secret-password")
    reference_repository.create_reference(user.id, "article", ARTICLE_FIELDS)
    reference_repository.create_reference(user.id, "book", BOOK_FIELDS)
    reference_repository.create_reference(user.id, "inproceedings", PAPER_FIELDS, "xp-method")
    return user


def found(user, query):
    references = reference_repository.get_references(user.id, query)
    return [reference.cite_key for reference in references]


def test_empty_search_returns_everything(user):
    assert found(user, "") == ["xp-method", "martin2008", "dijkstra1968"]
    assert found(user, "   ") == ["xp-method", "martin2008", "dijkstra1968"]


@pytest.mark.parametrize("query,keys", [
    # every field is searched
    ("dijkstra", ["dijkstra1968"]),                 # author
    ("harmful", ["dijkstra1968"]),                  # title
    ("communications", ["dijkstra1968"]),           # journal
    ("sigcse", ["xp-method"]),                      # booktitle
    ("hall", ["martin2008"]),                       # publisher
    ("2011", ["xp-method"]),                        # year
    ("147", ["dijkstra1968"]),                      # pages
    ("saddle", ["martin2008"]),                     # address
    ("978-0132350884", ["martin2008"]),             # isbn
    ("10.1145/362929", ["dijkstra1968"]),           # doi
    ("xp-method", ["xp-method"]),                   # key given by the user
    ("martin2008", ["martin2008"]),                 # generated key
    ("inproceedings", ["xp-method"]),               # type
    ("book", ["martin2008"]),                       # type
    # case does not matter
    ("DIJKSTRA", ["dijkstra1968"]),
    ("cLeAn", ["martin2008"]),
    ("mäkelä", ["xp-method"]),
    ("MÄKELÄ", ["xp-method"]),
    ("äänis", ["xp-method"]),
    # a part of a word is enough
    ("appren", ["xp-method"]),
    ("196", ["dijkstra1968"]),
    # several references can match
    ("acm", ["xp-method", "dijkstra1968"]),
    ("e", ["xp-method", "martin2008", "dijkstra1968"]),
    # every word has to be found, in any field and in any order
    ("clean martin", ["martin2008"]),
    ("martin clean", ["martin2008"]),
    ("2008 hall code", ["martin2008"]),
    ("acm 2011", ["xp-method"]),
    ("acm 1968 harmful", ["dijkstra1968"]),
    ("clean dijkstra", []),
    ("acm 2008", []),
    # nothing matches
    ("zzz", []),
    ("makela", []),
])
def test_search(user, query, keys):
    assert found(user, query) == keys


def test_word_does_not_match_over_two_fields(user):
    # the end of the author and the start of the title
    assert found(user, "c.clean") == []
    assert found(user, "c. clean") == ["martin2008"]


@pytest.mark.parametrize(
    "query", ["%", "_", "c_ean", "cl%n", "'", '"', "\\", "'; DROP TABLE users;--"]
)
def test_special_characters_have_no_special_meaning(user, query):
    assert found(user, query) == []
    assert len(found(user, "")) == 3


def test_special_characters_can_be_searched(user):
    fields = dict(ARTICLE_FIELDS, title="100% _Coverage_ of O'Reilly")
    reference_repository.create_reference(user.id, "article", fields, "special")
    assert found(user, "100%") == ["special"]
    assert found(user, "_coverage_") == ["special"]
    assert found(user, "o'reilly") == ["special"]


def test_search_returns_only_own_references(user):
    other = user_repository.create_user("uolevi", "secret-password")
    reference_repository.create_reference(other.id, "book", BOOK_FIELDS, "others-book")

    assert found(user, "clean") == ["martin2008"]
    assert found(other, "clean") == ["others-book"]
    assert found(other, "dijkstra") == []


def test_count_references(user):
    other = user_repository.create_user("uolevi", "secret-password")
    assert reference_repository.count_references(user.id) == 3
    assert reference_repository.count_references(other.id) == 0


# the list page

@pytest.fixture
def logged_in(client, actions):
    actions.register("maija")
    actions.add_reference()                      # Martin, Robert: Clean Code, 2008
    actions.add_reference(**BOOK)                # Fowler, Martin: Refactoring, 1999
    actions.add_reference(**INPROCEEDINGS)       # Vihavainen: Extreme Apprenticeship Method, 2011


def page_of(client, url):
    response = client.get(url)
    assert response.status_code == 200
    return response.get_data(as_text=True)


def titles(page):
    return re.findall(r'<span class="reference-title">(.*?)</span>', page)


def test_list_has_search_form(client, logged_in):
    page = page_of(client, "/references")
    assert '<form action="/references" method="get" class="search-form"' in page
    assert page.count('<input type="text"') == 1
    assert 'name="query"' in page
    assert "3 references" in page
    assert "show all" not in page


def test_search_filters_the_list(client, logged_in):
    page = page_of(client, "/references?query=refactoring")
    assert titles(page) == ["Refactoring"]
    assert "1 of 3 references" in page
    assert 'value="refactoring"' in page
    assert '<a href="/references" id="clear-search">show all</a>' in page


def test_search_with_several_words(client, logged_in):
    assert titles(page_of(client, "/references?query=martin")) == ["Refactoring", "Clean Code"]
    assert titles(page_of(client, "/references?query=martin+1999")) == ["Refactoring"]
    assert titles(page_of(client, "/references?query=1999+MARTIN")) == ["Refactoring"]


def test_empty_search_shows_everything(client, logged_in):
    for url in ["/references?query=", "/references?query=+++"]:
        page = page_of(client, url)
        assert len(titles(page)) == 3
        assert "3 references" in page
        assert "show all" not in page


def test_search_without_results(client, logged_in):
    page = page_of(client, "/references?query=zzz")
    assert titles(page) == []
    assert "No references found" in page
    assert "No references yet" not in page
    # the search can be changed or removed
    assert 'value="zzz"' in page
    assert 'id="clear-search"' in page


def test_user_without_references_has_no_search_form(client, actions):
    actions.register("maija")
    for url in ["/references", "/references?query=clean"]:
        page = page_of(client, url)
        assert "No references yet" in page
        assert "search-form" not in page


def test_search_is_limited_to_own_references(client, actions, logged_in):
    actions.logout()
    actions.register("uolevi")
    actions.add_reference(title="Clean Architecture")

    page = page_of(client, "/references?query=clean")
    assert titles(page) == ["Clean Architecture"]
    assert "1 of 1 reference<" in page.replace("\n", "<")


def test_search_is_escaped_on_the_page(client, logged_in):
    page = page_of(client, '/references?query="><script>alert(1)</script>')
    assert "<script>alert(1)</script>" not in page
    assert "&lt;script&gt;" in page


def test_search_is_shortened_when_too_long(client, logged_in):
    page = page_of(client, "/references?query=" + "a" * 500)
    assert f'value="{"a" * SEARCH_MAX_LENGTH}"' in page


def test_search_requires_login(client):
    response = client.get("/references?query=clean")
    assert response.headers["Location"] == "/login"


def test_back_returns_to_the_search(client, logged_in):
    page = page_of(client, "/references?query=martin+1999")
    link = html.unescape(re.search(r'<a href="([^"]*)" class="reference-card"', page).group(1))

    page = page_of(client, link)
    assert '<a href="/references?query=martin+1999" class="button" id="back">back</a>' in page

    page = page_of(client, "/references?query=martin+1999")
    assert titles(page) == ["Refactoring"]
