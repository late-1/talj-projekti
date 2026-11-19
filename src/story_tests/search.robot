*** Settings ***
Resource  resource.robot
Suite Setup      Open And Configure Browser
Suite Teardown   Close Browser
Test Setup       Reset Application And Add References

*** Keywords ***
Reset Application And Add References
    Reset Application
    Submit Registration  maija  ${PASSWORD}  ${PASSWORD}
    Add Article  Martin, Robert  Clean Code  2008
    Add Article  Fowler, Martin  Refactoring  1999
    Add Article  Mäkelä, Äänis  Extreme Apprenticeship  2011
    Click  .nav-left >> text=view / search

Add Article
    [Arguments]  ${author}  ${title}  ${year}
    Go To  ${HOME_URL}/add
    Fill Text  id=author  ${author}
    Fill Text  id=title  ${title}
    Fill Text  id=journal  Journal of Software
    Fill Text  id=year  ${year}
    Click  input[type="submit"]
    Get Text  .flash  *=  Reference added

Search
    [Arguments]  ${query}
    Fill Text  id=query  ${query}
    Click  .search-form input[type="submit"]

Titles Should Be
    [Arguments]  @{titles}
    ${count}=  Get Length  ${titles}
    Get Element Count  .reference-card  ==  ${count}
    FOR  ${index}  ${title}  IN ENUMERATE  @{titles}
        Get Text  .reference-card >> nth=${index} >> .reference-title  ==  ${title}
    END

*** Test Cases ***
List has one search field above the references
    Get Element Count  .search-form input[type="text"]  ==  1
    Titles Should Be  Extreme Apprenticeship  Refactoring  Clean Code
    ${form}=  Get BoundingBox  .search-form
    ${card}=  Get BoundingBox  .reference-card >> nth=0
    Should Be True  ${form}[y] < ${card}[y]

User can search by title
    Search  refactoring
    Titles Should Be  Refactoring
    Get Text  .reference-count  *=  1 of 3 references
    Get Text  id=query  ==  refactoring

User can search by author and year
    Search  martin
    Titles Should Be  Refactoring  Clean Code
    Search  martin 2008
    Titles Should Be  Clean Code

Search does not care about letter case
    Search  CLEAN code
    Titles Should Be  Clean Code
    Search  MÄKELÄ
    Titles Should Be  Extreme Apprenticeship

Search can be started with the enter key
    Fill Text  id=query  fowler
    Keyboard Key  press  Enter
    Titles Should Be  Refactoring

Search without results tells that nothing was found
    Search  zzz
    Get Element Count  .reference-card  ==  0
    Get Text  .no-results  *=  No references found

Show all removes the search
    Search  refactoring
    Click  id=clear-search
    Get Url  ==  ${HOME_URL}/references
    Titles Should Be  Extreme Apprenticeship  Refactoring  Clean Code
    Get Text  id=query  ==  ${EMPTY}

Back button returns to the search results
    Search  martin
    Click  .reference-card >> nth=1
    Get Text  id=bibtex  *=  title${SPACE*3}= {Clean Code}
    Click  id=back
    Get Url  ==  ${HOME_URL}/references?query=martin
    Titles Should Be  Refactoring  Clean Code
    Get Text  id=query  ==  martin
