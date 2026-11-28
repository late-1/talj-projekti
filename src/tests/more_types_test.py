import re

import pytest

from bibtex import to_bibtex
from citation import to_citation
from entities.reference import Reference
from reference_types import ENTRY_TYPES, MAIN_TYPES, MORE_TYPES, fields_of
from repositories import reference_repository
from util import UserInputError, cite_key_base, search_filters, validate_reference

# A reference of each new type with its required fields
EXAMPLES = {
    "booklet": {"title": "How to Cite"},
    "conference": {"author": "Doe, Jane", "title": "On Keys", "booktitle": "Proc. of Keys",
                   "year": "2019"},
    "inbook": {"author": "Doe, Jane", "title": "Big Book", "chapter": "3",
               "publisher": "Gaudeamus", "year": "2018"},
    "incollection": {"author": "Doe, Jane", "title": "A Part", "booktitle": "Collected Works",
                     "publisher": "Gaudeamus", "year": "2017"},
    "manual": {"title": "User Guide"},
    "mastersthesis": {"author": "Doe, Jane", "title": "Thesis", "school": "University of Helsinki",
                      "year": "2016"},
    "misc": {},
    "phdthesis": {"author": "Doe, Jane", "title": "Dissertation",
                  "school": "University of Helsinki", "year": "2015"},
    "proceedings": {"title": "Proceedings of Keys", "year": "2014"},
    "techreport": {"author": "Doe, Jane", "title": "Report",
                   "institution": "University of Helsinki", "year": "2013"},
    "unpublished": {"author": "Doe, Jane", "title": "Draft", "note": "Manuscript in preparation"},
}


def reference(entry_type, **fields):
    return Reference(1, 1, entry_type, "key", fields)


def page_of(client, url):
    return client.get(url).get_data(as_text=True)


@pytest.fixture
def logged_in(actions):
    actions.register("maija")


def own_references(actions):
    return reference_repository.get_references(actions.session()["user_id"])


def add(actions, entry_type, **fields):
    """Adds a reference with only the given fields (the article defaults are emptied)"""
    data = dict.fromkeys(["author", "title", "journal", "year"], "")
    data.update(fields)
    return actions.add_reference(entry_type=entry_type, **data)


# types and fields

def test_there_are_fourteen_types():
    assert MAIN_TYPES == ["article", "book", "inproceedings"]
    assert MORE_TYPES == ["booklet", "conference", "inbook", "incollection", "manual",
                          "mastersthesis", "misc", "phdthesis", "proceedings", "techreport",
                          "unpublished"]
    assert list(ENTRY_TYPES) == MAIN_TYPES + MORE_TYPES


@pytest.mark.parametrize("entry_type,required", [
    ("booklet", ["title"]),
    ("conference", ["author", "title", "booktitle", "year"]),
    ("inbook", ["author", "title", "chapter", "publisher", "year"]),
    ("incollection", ["author", "title", "booktitle", "publisher", "year"]),
    ("manual", ["title"]),
    ("mastersthesis", ["author", "title", "school", "year"]),
    ("misc", []),
    ("phdthesis", ["author", "title", "school", "year"]),
    ("proceedings", ["title", "year"]),
    ("techreport", ["author", "title", "institution", "year"]),
    ("unpublished", ["author", "title", "note"]),
])
def test_required_fields(entry_type, required):
    assert ENTRY_TYPES[entry_type]["required"] == required
    assert set(EXAMPLES[entry_type]) == set(required)


def test_conference_has_the_fields_of_inproceedings():
    assert set(fields_of("inproceedings")) <= set(fields_of("conference"))


def test_fields_of_a_thesis_in_form_order():
    assert fields_of("phdthesis") == ["author", "title", "school", "year", "month", "address",
                                      "note"]


# validation

@pytest.mark.parametrize("entry_type", MORE_TYPES)
def test_required_fields_are_enough(entry_type):
    assert validate_reference(entry_type, EXAMPLES[entry_type]) == EXAMPLES[entry_type]


@pytest.mark.parametrize("entry_type", [t for t in MORE_TYPES if EXAMPLES[t]])
def test_each_required_field_is_required(entry_type):
    for name in EXAMPLES[entry_type]:
        form = dict(EXAMPLES[entry_type], **{name: " "})
        with pytest.raises(UserInputError, match="is required"):
            validate_reference(entry_type, form)


def test_optional_year_is_still_checked():
    with pytest.raises(UserInputError, match="four-digit"):
        validate_reference("misc", {"year": "20"})


def test_fields_of_other_types_are_left_out():
    fields = validate_reference("misc", {"title": "Page", "journal": "Journal", "url": "u"})
    assert fields == {"title": "Page", "url": "u"}


# generated keys without an author or a year

@pytest.mark.parametrize("author,year,title,expected", [
    ("Doe, Jane", "2020", "Report", "doe2020"),
    ("Doe, Jane", None, "Report", "doe"),
    (None, "2020", "The Manual", "the2020"),
    (None, None, "  ¿Qué? Manual", "que"),
    (None, None, None, "ref"),
    (None, "2020", None, "ref2020"),
])
def test_key_base(author, year, title, expected):
    assert cite_key_base(author, year, title) == expected


def test_added_reference_without_an_author_gets_a_key_from_the_title(client, actions, logged_in):
    add(actions, "manual", title="User Guide", year="2020")
    add(actions, "manual", title="User Guide", edition="2")
    add(actions, "proceedings", title="Proceedings of Keys", year="2014", editor="Roe, Rick")
    keys = [r.cite_key for r in own_references(actions)]
    assert keys == ["roe2014", "user", "user2020"]


def test_misc_without_any_fields_is_added(client, actions, logged_in):
    response = add(actions, "misc")
    assert response.status_code == 302
    assert own_references(actions)[0].cite_key == "ref"


def test_edit_without_an_author_generates_the_key_again(client, actions, logged_in):
    add(actions, "misc", title="Some Page")
    misc = own_references(actions)[0]
    client.post(f"/references/{misc.id}/edit", data={
        "entry_type": "misc", "title": "Other Page", "year": "2021",
        "csrf_token": actions.csrf_token(),
    })
    assert own_references(actions)[0].cite_key == "other2021"


# BibTeX and citation

@pytest.mark.parametrize("entry_type", MORE_TYPES)
def test_bibtex_of_each_type(entry_type):
    fields = EXAMPLES[entry_type] or {"title": "Some Page"}
    text = to_bibtex(reference(entry_type, **fields))
    assert text.startswith(f"@{entry_type}{{key,\n")
    for name, value in fields.items():
        assert re.search(rf"\n  {name} *= \{{{re.escape(value)}\}}", text)


def test_url_is_written_as_such():
    text = to_bibtex(reference("misc", url="https://example.com/a_b%20c#d"))
    assert "url = {https://example.com/a_b%20c#d}" in text


@pytest.mark.parametrize("entry_type,fields,expected", [
    ("booklet", {"title": "How to Cite", "howpublished": "Handed out", "year": "2020"},
     "<i>How to Cite</i>. (2020). Handed out."),
    ("conference", EXAMPLES["conference"],
     "Doe, Jane (2019). On Keys. In <i>Proc. of Keys</i>."),
    ("inbook", dict(EXAMPLES["inbook"], pages="5-9", address="Helsinki"),
     "Doe, Jane (2018). <i>Big Book</i> (Chapter 3, pp. 5–9). Helsinki: Gaudeamus."),
    ("incollection", dict(EXAMPLES["incollection"], editor="Roe, Rick and Poe, Pia", pages="1-2"),
     "Doe, Jane (2017). A Part. In Roe, Rick &amp; Poe, Pia (Eds.), "
     "<i>Collected Works</i> (pp. 1–2). Gaudeamus."),
    ("manual", {"title": "User Guide", "organization": "ACME", "edition": "2nd"},
     "<i>User Guide</i> (2nd ed.). (n.d.). ACME."),
    ("mastersthesis", EXAMPLES["mastersthesis"],
     "Doe, Jane (2016). <i>Thesis</i>. [Master&#39;s thesis, University of Helsinki]."),
    ("misc", {"title": "Some Page", "url": "https://example.com"},
     "<i>Some Page</i>. (n.d.). https://example.com"),
    ("misc", {}, "(n.d.)."),
    ("phdthesis", EXAMPLES["phdthesis"],
     "Doe, Jane (2015). <i>Dissertation</i>. [Doctoral dissertation, University of Helsinki]."),
    ("proceedings", dict(EXAMPLES["proceedings"], editor="Roe, Rick", volume="2"),
     "Roe, Rick (Ed.) (2014). <i>Proceedings of Keys</i> (Vol. 2)."),
    ("techreport", dict(EXAMPLES["techreport"], number="C-2013-1"),
     "Doe, Jane (2013). <i>Report</i> (Report No. C-2013-1). University of Helsinki."),
    ("unpublished", EXAMPLES["unpublished"],
     "Doe, Jane (n.d.). <i>Draft</i>. [Unpublished manuscript]. Manuscript in preparation."),
])
def test_citation_of_each_type(entry_type, fields, expected):
    assert str(to_citation(reference(entry_type, **fields))) == expected


def test_citation_values_are_escaped():
    text = str(to_citation(reference("misc", title="<b>", howpublished="<i>")))
    assert "<b>" not in text and "&lt;b&gt;" in text and "&lt;i&gt;" in text


# list, BibTeX page and search

def test_list_shows_editor_and_no_date(client, actions, logged_in):
    add(actions, "proceedings", title="Proceedings of Keys", year="2014", editor="Roe, Rick")
    add(actions, "misc", title="Some Page")
    add(actions, "misc")
    page = page_of(client, "/references")
    assert re.search(r'class="reference-authors">\s*Roe, Rick \(2014\)', page)
    assert re.search(r'class="reference-authors">\s*\(n\.d\.\)', page)
    # a reference without a title is shown with its key
    assert '<span class="reference-title">ref</span>' in page


@pytest.mark.parametrize("entry_type,venue", [
    ("mastersthesis", "University of Helsinki"),
    ("techreport", "University of Helsinki"),
    ("incollection", "Collected Works"),
])
def test_venue_of_new_types(client, actions, logged_in, entry_type, venue):
    add(actions, entry_type, **EXAMPLES[entry_type])
    page = page_of(client, "/references")
    assert f'<span class="reference-venue muted">{venue}</span>' in page
    assert len(reference_repository.get_references(
        actions.session()["user_id"], filters={"venue": venue.split()[-1]})) == 1


def test_search_finds_new_fields(client, actions, logged_in):
    add(actions, "misc", title="Page", note="Remember this", url="https://example.com")
    user_id = actions.session()["user_id"]
    assert len(reference_repository.get_references(user_id, "remember")) == 1
    assert len(reference_repository.get_references(user_id, "example.com")) == 1


def test_type_filter_accepts_new_types(client, actions, logged_in):
    assert search_filters({"type": "techreport"}) == ({"type": "techreport"}, [])
    add(actions, "techreport", **EXAMPLES["techreport"])
    actions.add_reference()
    page = page_of(client, "/references?type=techreport")
    assert page.count('class="reference-card"') == 1


def test_bibtex_page_of_a_new_type(client, actions, logged_in):
    add(actions, "phdthesis", **EXAMPLES["phdthesis"])
    thesis = own_references(actions)[0]
    page = page_of(client, f"/references/{thesis.id}")
    assert "@phdthesis{doe2015," in page
    assert "<dt>school</dt>" in page


# the "more" menu

def menu_of(page):
    return page[page.index('<details class="type-more"'):page.index("</details>",
                page.index('<details class="type-more"'))]


def test_add_form_has_the_main_types_and_the_more_menu(client, logged_in):
    page = page_of(client, "/add")
    choice = page[page.index('<fieldset class="type-choice">'):page.index("</fieldset>")]
    menu = menu_of(page)
    for entry_type in MAIN_TYPES:
        assert f'id="type-{entry_type}"' in choice and f'id="type-{entry_type}"' not in menu
    for entry_type in MORE_TYPES:
        assert (f'<input type="radio" name="entry_type" id="type-{entry_type}" '
                f'value="{entry_type}" />') in menu
    assert '<span class="type-more-label">more</span>' in menu
    assert 'src="/static/type_choice.js"' in page


def test_chosen_type_of_the_menu_is_shown_in_place_of_more(client, logged_in):
    page = page_of(client, "/add?type=techreport")
    menu = menu_of(page)
    assert '<span class="type-more-label">techreport</span>' in menu
    assert 'id="type-techreport" value="techreport" checked' in menu
    # the menu is closed and the fields of the type are shown
    assert '<details class="type-more" id="type-more">' in page
    assert re.search(r'<input type="text" name="institution"[^>]*required', page)


def test_edit_form_shows_the_type_of_the_menu(client, actions, logged_in):
    add(actions, "unpublished", **EXAMPLES["unpublished"])
    draft = own_references(actions)[0]
    page = page_of(client, f"/references/{draft.id}/edit")
    assert '<span class="type-more-label">unpublished</span>' in page


def test_search_has_the_more_menu_with_any(client, actions, logged_in):
    actions.add_reference()
    page = page_of(client, "/references?type=misc")
    assert 'id="type-any" value="" />' in page
    assert '<span class="type-more-label">misc</span>' in page
    assert '<input type="radio" name="type" id="type-misc" value="misc" checked />' in page
    assert 'src="/static/type_choice.js"' in page


def test_type_choice_script_is_served(client):
    response = client.get("/static/type_choice.js")
    assert response.status_code == 200
    assert "type-more" in response.get_data(as_text=True)
