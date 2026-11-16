*** Settings ***
Resource  resource.robot
Suite Setup      Open Browser With Clipboard
Suite Teardown   Close Browser
Test Setup       Reset Application And Register

*** Keywords ***
Open Browser With Clipboard
    Open And Configure Browser
    # the copy button needs a permission to use the clipboard
    @{permissions}=  Create List  clipboard-read  clipboard-write
    New Context  permissions=${permissions}
    New Page  about:blank

Reset Application And Register
    Reset Application
    Submit Registration  maija  ${PASSWORD}  ${PASSWORD}

Add Article
    [Arguments]  ${title}=Clean Code  ${author}=Martin, Robert  ${year}=2008
    Go To  ${HOME_URL}/add
    Fill Text  id=author  ${author}
    Fill Text  id=title  ${title}
    Fill Text  id=journal  Journal of Software
    Fill Text  id=year  ${year}
    Fill Text  id=pages  12-34
    Click  input[type="submit"]
    Get Text  .flash  *=  Reference added

Open List
    Click  .nav-left >> text=view / search
    Get Url  ==  ${HOME_URL}/references

*** Test Cases ***
List is empty at first
    Open List
    Get Text  main  *=  No references yet
    Get Element Count  .reference-card  ==  0

Added references are listed newest first
    Add Article  title=Clean Code
    Add Article  title=Clean Architecture  year=2017
    Open List
    Get Element Count  .reference-card  ==  2
    Get Text  .reference-card >> nth=0  *=  Clean Architecture
    Get Text  .reference-card >> nth=0  *=  Martin, Robert (2017)
    Get Text  .reference-card >> nth=0  *=  Journal of Software
    Get Text  .reference-card >> nth=0  *=  martin2017
    Get Text  .reference-card >> nth=1  *=  Clean Code
    Get Text  .reference-card >> nth=1  *=  martin2008

Each reference is in a box with a thin border
    Add Article
    Open List
    Get Style  .reference-card  border-top-width  ==  1px
    Get Style  .reference-card  border-top-style  ==  solid

Clicking a box opens the BibTeX page
    Add Article
    Open List
    Click  .reference-card
    Get Url  matches  ${HOME_URL}/references/\\d+\\?back=.*
    Get Text  id=bibtex  *=  @article{martin2008,
    Get Text  id=bibtex  *=  title${SPACE*3}= {Clean Code}
    Get Text  id=bibtex  *=  pages${SPACE*3}= {12--34}
    Get Text  .nav-left a.active  ==  view / search

Copy button copies the BibTeX to the clipboard
    Add Article
    Open List
    Click  .reference-card
    ${bibtex}=  Get Text  id=bibtex
    Click  id=copy
    Get Text  id=copy  ==  Copied
    ${clipboard}=  Evaluate JavaScript  ${None}  () => navigator.clipboard.readText()
    Should Be Equal  ${clipboard}  ${bibtex}
    Should Start With  ${clipboard}  @article{martin2008,
    Should End With  ${clipboard}  }

Back button is on the left and copy button on the right of the same row
    Add Article
    Open List
    Click  .reference-card
    ${back}=  Get BoundingBox  id=back
    ${copy}=  Get BoundingBox  id=copy
    ${bibtex}=  Get BoundingBox  id=bibtex
    Should Be True  ${back}[x] < ${copy}[x]
    Should Be True  abs(${back}[y] - ${copy}[y]) < 2
    Should Be True  abs(${back}[x] - ${bibtex}[x]) < 2
    Should Be True  abs((${copy}[x] + ${copy}[width]) - (${bibtex}[x] + ${bibtex}[width])) < 2
    Should Be True  ${copy}[y] + ${copy}[height] <= ${bibtex}[y]

Back button returns to the list
    Add Article
    Open List
    Click  .reference-card
    Click  id=back
    Get Url  ==  ${HOME_URL}/references
    Get Element Count  .reference-card  ==  1

User sees only own references
    Add Article  title=Secret of Maija
    Open List
    Click  .reference-card
    ${url}=  Get Url
    Click  text=log out
    Submit Registration  uolevi  ${PASSWORD}  ${PASSWORD}
    Open List
    Get Element Count  .reference-card  ==  0
    Go To  ${url}
    Get Text  body  not contains  Secret of Maija
    Get Element Count  id=bibtex  ==  0
