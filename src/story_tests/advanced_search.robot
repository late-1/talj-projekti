*** Settings ***
Resource  resource.robot
Suite Setup      Open And Configure Browser
Suite Teardown   Close Browser
Test Setup       Reset Application And Add References

*** Keywords ***
Reset Application And Add References
    Reset Application
    Submit Registration  maija  ${PASSWORD}  ${PASSWORD}
    Add Reference  article  Martin, Robert  Clean Code  journal  Journal of Software  2008
    Add Reference  book  Fowler, Martin  Refactoring  publisher  Addison-Wesley  1999
    Add Reference  inproceedings  Vihavainen, Arto  Extreme Apprenticeship  booktitle  Proceedings of SIGCSE  2011
    Click  .nav-left >> text=view / search

Add Reference
    [Arguments]  ${type}  ${author}  ${title}  ${venue_field}  ${venue}  ${year}
    Go To  ${HOME_URL}/add
    Click  label[for="type-${type}"]
    Fill Text  id=author  ${author}
    Fill Text  id=title  ${title}
    Fill Text  id=${venue_field}  ${venue}
    Fill Text  id=year  ${year}
    Click  input[type="submit"]
    Get Text  .flash  *=  Reference added

Open Advanced
    Click  \#advanced summary
    Get Element States  id=author  contains  visible

Submit Search
    Click  .search-form input[type="submit"]

Titles Should Be
    [Arguments]  @{titles}
    ${count}=  Get Length  ${titles}
    Get Element Count  .reference-card  ==  ${count}
    FOR  ${index}  ${title}  IN ENUMERATE  @{titles}
        Get Text  .reference-card >> nth=${index} >> .reference-title  ==  ${title}
    END

*** Test Cases ***
Advanced button is below the search field and the fields are hidden at first
    Get Text  \#advanced summary  ==  advanced
    ${query}=  Get BoundingBox  id=query
    ${button}=  Get BoundingBox  \#advanced summary
    Should Be True  ${button}[y] > ${query}[y] + ${query}[height]
    FOR  ${name}  IN  author  title  venue  key  year_from  year_to
        Get Element States  id=${name}  contains  hidden
    END

Advanced button shows and hides the fields
    Open Advanced
    FOR  ${name}  IN  author  title  venue  key  year_from  year_to
        Get Element States  id=${name}  contains  visible
    END
    Get Checkbox State  id=type-any  ==  checked
    Click  \#advanced summary
    Get Element States  id=author  contains  hidden

User can search by author
    Open Advanced
    Fill Text  id=author  martin
    Submit Search
    Titles Should Be  Refactoring  Clean Code
    Get Text  .reference-count  *=  2 of 3 references
    Get Url  ==  ${HOME_URL}/references?author=martin

User can search by title
    Open Advanced
    Fill Text  id=title  clean
    Submit Search
    Titles Should Be  Clean Code

Author search does not look at other fields
    Open Advanced
    Fill Text  id=author  clean
    Submit Search
    Get Element Count  .reference-card  ==  0
    Get Text  .no-results  *=  No references found

User can search by where the reference was published
    Open Advanced
    Fill Text  id=venue  sigcse
    Submit Search
    Titles Should Be  Extreme Apprenticeship
    Fill Text  id=venue  addison
    Submit Search
    Titles Should Be  Refactoring

User can search by key
    Open Advanced
    Fill Text  id=key  fowler1999
    Submit Search
    Titles Should Be  Refactoring

User can search by years
    Open Advanced
    Fill Text  id=year_from  2000
    Submit Search
    Titles Should Be  Extreme Apprenticeship  Clean Code
    Fill Text  id=year_to  2010
    Submit Search
    Titles Should Be  Clean Code
    Get Url  ==  ${HOME_URL}/references?year_from=2000&year_to=2010

User can search by type
    Open Advanced
    Click  label[for="type-book"]
    Submit Search
    Titles Should Be  Refactoring
    Get Checkbox State  id=type-book  ==  checked
    Click  label[for="type-any"]
    Submit Search
    Titles Should Be  Extreme Apprenticeship  Refactoring  Clean Code
    Get Url  ==  ${HOME_URL}/references

Advanced fields are combined with each other and the search field
    Open Advanced
    Fill Text  id=query  martin
    Submit Search
    Titles Should Be  Refactoring  Clean Code
    Open Advanced
    Fill Text  id=year_to  2000
    Submit Search
    Titles Should Be  Refactoring
    Click  label[for="type-article"]
    Submit Search
    Get Element Count  .reference-card  ==  0

Advanced fields stay open and keep their values after searching
    Open Advanced
    Fill Text  id=author  martin
    Fill Text  id=year_from  2000
    Keyboard Key  press  Enter
    Titles Should Be  Clean Code
    Get Element States  id=author  contains  visible
    Get Text  id=author  ==  martin
    Get Text  id=year_from  ==  2000

Invalid year is not accepted
    Open Advanced
    Fill Text  id=year_from  20
    Submit Search
    # the browser stops the form because of the pattern of the field
    Get Url  ==  ${HOME_URL}/references
    Go To  ${HOME_URL}/references?year_from=20
    Get Text  .flash  ==  Years must be four-digit numbers
    Titles Should Be  Extreme Apprenticeship  Refactoring  Clean Code

Show all removes the advanced search
    Open Advanced
    Fill Text  id=author  fowler
    Submit Search
    Click  id=clear-search
    Get Url  ==  ${HOME_URL}/references
    Titles Should Be  Extreme Apprenticeship  Refactoring  Clean Code
    Get Element States  id=author  contains  hidden

Back button returns to the advanced search results
    Open Advanced
    Fill Text  id=author  martin
    Click  label[for="type-book"]
    Submit Search
    Click  .reference-card
    Get Text  id=bibtex  *=  @book{fowler1999,
    Click  id=back
    Get Url  ==  ${HOME_URL}/references?author=martin&type=book
    Titles Should Be  Refactoring
    Get Text  id=author  ==  martin
    Get Checkbox State  id=type-book  ==  checked
