*** Settings ***
Resource  resource.robot
Library   Collections
Suite Setup      Open And Configure Browser
Suite Teardown   Close Browser
Test Setup       Reset Application And Log In

*** Variables ***
@{MORE_TYPES}  booklet  conference  inbook  incollection  manual  mastersthesis  misc
...            phdthesis  proceedings  techreport  unpublished

*** Keywords ***
Reset Application And Log In
    Reset Application
    Submit Registration  maija  ${PASSWORD}  ${PASSWORD}

Open More Menu
    Click  id=type-more >> summary
    Get Element States  .type-more-list  contains  visible

More Menu Should Be Closed
    Get Element States  .type-more-list  contains  hidden

More Label Should Be
    [Arguments]  ${text}
    Get Text  .type-more-label  ==  ${text}

Add Techreport
    Go To  ${HOME_URL}/add
    Open More Menu
    Click  label[for="type-techreport"]
    Fill Text  id=author  Doe, Jane
    Fill Text  id=title  A Report
    Fill Text  id=institution  University of Helsinki
    Fill Text  id=year  2013
    Click  input[type="submit"]
    Get Text  .flash  *=  Reference added with the key doe2013

*** Test Cases ***
More menu is next to the main types and opens a list of the other types
    Go To  ${HOME_URL}/add
    More Label Should Be  more
    More Menu Should Be Closed
    ${inproceedings}=  Get BoundingBox  label[for="type-inproceedings"]
    ${more}=  Get BoundingBox  id=type-more >> summary
    Should Be True  ${more}[x] > ${inproceedings}[x] + ${inproceedings}[width]
    Should Be True  abs(${more}[y] + ${more}[height] / 2 - ${inproceedings}[y] - ${inproceedings}[height] / 2) < 2
    Open More Menu
    ${labels}=  Get Elements  .type-more-list label
    ${texts}=  Create List
    FOR  ${label}  IN  @{labels}
        ${text}=  Get Text  ${label}
        Append To List  ${texts}  ${text}
    END
    Lists Should Be Equal  ${texts}  ${MORE_TYPES}

More looks like the other types and has a thin chevron
    Go To  ${HOME_URL}/add
    ${font}=  Get Style  label[for="type-book"]  font-size
    Get Style  .type-more-label  font-size  ==  ${font}
    ${color}=  Get Style  label[for="type-book"]  color
    Get Style  .type-more-label  color  ==  ${color}
    Get Style  .type-more-label  text-decoration-line  ==  none
    # the chevron is a corner of two thin lines
    ${border}=  Evaluate JavaScript  id=type-more >> summary
    ...  (summary) => getComputedStyle(summary, "::after").borderRightWidth
    Should Be Equal  ${border}  1px

Choosing a type in the menu shows it underlined in place of more
    Go To  ${HOME_URL}/add
    Open More Menu
    Click  label[for="type-phdthesis"]
    More Menu Should Be Closed
    More Label Should Be  phdthesis
    Get Style  .type-more-label  text-decoration-line  ==  underline
    Get Style  label[for="type-article"]  text-decoration-line  ==  none
    # the fields of the type
    Get Element States  id=school  contains  visible
    Get Element States  id=journal  contains  hidden

Choosing a main type shows more again
    Go To  ${HOME_URL}/add?type=misc
    More Label Should Be  misc
    Click  label[for="type-book"]
    More Label Should Be  more
    Get Style  .type-more-label  text-decoration-line  ==  none
    Get Element States  id=publisher  contains  visible

Escape and a click outside close the menu
    Go To  ${HOME_URL}/add
    Open More Menu
    Keyboard Key  press  Escape
    More Menu Should Be Closed
    More Label Should Be  more
    Open More Menu
    Click  h1
    More Menu Should Be Closed

Reference of a type in the menu is added and shown
    Add Techreport
    Go To  ${HOME_URL}/references
    Get Text  .reference-card >> nth=0 >> .reference-title  ==  A Report
    Get Text  .reference-card >> nth=0 >> .reference-venue  ==  University of Helsinki
    Get Text  .reference-card >> nth=0 >> .reference-type  ==  techreport
    Click  .reference-card >> nth=0
    Get Text  id=bibtex  *=  @techreport{doe2013,
    Get Text  id=bibtex  *=  institution = {University of Helsinki}

Misc needs no fields
    Go To  ${HOME_URL}/add
    Open More Menu
    Click  label[for="type-misc"]
    Fill Text  id=title  Some web page
    Fill Text  id=url  https://example.com
    Click  input[type="submit"]
    Get Text  .flash  *=  Reference added with the key some
    Go To  ${HOME_URL}/references
    Get Text  .reference-card >> nth=0 >> .reference-authors  ==  (n.d.)

Edit form shows the type of the menu
    Add Techreport
    Go To  ${HOME_URL}/references
    Click  .reference-card >> nth=0
    Click  id=edit
    More Label Should Be  techreport
    Get Style  .type-more-label  text-decoration-line  ==  underline
    Open More Menu
    Click  label[for="type-mastersthesis"]
    Fill Text  id=school  Aalto University
    Click  id=save
    Get Text  id=bibtex  *=  @mastersthesis{doe2013,

Advanced search filters by a type of the menu
    Add Techreport
    Go To  ${HOME_URL}/references
    Click  id=advanced
    Get Text  .advanced-fields .type-more-label  ==  more
    Click  .advanced-fields .type-more summary
    Click  label[for="type-techreport"]
    Get Text  .advanced-fields .type-more-label  ==  techreport
    Click  id=search
    Get Element Count  .reference-card  ==  1
    Get Text  .advanced-fields .type-more-label  ==  techreport
    # the advanced fields stay open after the search
    Click  label[for="type-any"]
    Get Text  .advanced-fields .type-more-label  ==  more
