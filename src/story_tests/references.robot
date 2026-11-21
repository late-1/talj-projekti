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

Buttons Should Be Above The BibTeX And Within Its Sides
    ${bibtex}=  Get BoundingBox  id=bibtex
    FOR  ${button}  IN  back  copy  edit  delete
        ${box}=  Get BoundingBox  id=${button}
        Should Be True  ${box}[y] + ${box}[height] <= ${bibtex}[y]
        Should Be True  ${box}[x] >= ${bibtex}[x] - 1
        Should Be True  ${box}[x] + ${box}[width] <= ${bibtex}[x] + ${bibtex}[width] + 1
    END
    ${back}=  Get BoundingBox  id=back
    ${delete}=  Get BoundingBox  id=delete
    # back is at the left side and delete at the right side of the box
    Should Be True  abs(${back}[x] - ${bibtex}[x]) < 2
    Should Be True  abs(${delete}[x] + ${delete}[width] - ${bibtex}[x] - ${bibtex}[width]) < 2

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
    Get Text  id=copy  ==  copied
    ${clipboard}=  Evaluate JavaScript  ${None}  () => navigator.clipboard.readText()
    Should Be Equal  ${clipboard}  ${bibtex}
    Should Start With  ${clipboard}  @article{martin2008,
    Should End With  ${clipboard}  }

Buttons are above the BibTeX and within its sides
    Add Article
    Open List
    Click  .reference-card
    Buttons Should Be Above The BibTeX And Within Its Sides

Copy, edit and delete are in a row on the right in this order
    Add Article
    Open List
    Click  .reference-card
    ${copy}=  Get BoundingBox  id=copy
    ${edit}=  Get BoundingBox  id=edit
    ${delete}=  Get BoundingBox  id=delete
    Should Be True  abs(${copy}[y] - ${edit}[y]) < 2
    Should Be True  abs(${copy}[y] - ${delete}[y]) < 2
    Should Be True  ${copy}[x] + ${copy}[width] <= ${edit}[x]
    Should Be True  ${edit}[x] + ${edit}[width] <= ${delete}[x]

Buttons stay within the sides of the BibTeX on a narrow screen
    Add Article
    Open List
    Click  .reference-card
    Set Viewport Size  360  740
    Buttons Should Be Above The BibTeX And Within Its Sides
    ${viewport}=  Get Viewport Size
    FOR  ${box}  IN  citation  details
        ${bounds}=  Get BoundingBox  id=${box}
        Should Be True  ${bounds}[x] + ${bounds}[width] <= ${viewport}[width]
    END
    [Teardown]  Set Viewport Size  1280  720

Citation and fields are in their own boxes below the BibTeX
    Add Article
    Open List
    Click  .reference-card
    ${bibtex}=  Get BoundingBox  id=bibtex
    ${citation}=  Get BoundingBox  id=citation
    ${details}=  Get BoundingBox  id=details
    Should Be True  ${bibtex}[y] + ${bibtex}[height] <= ${citation}[y]
    Should Be True  ${citation}[y] + ${citation}[height] <= ${details}[y]
    FOR  ${box}  IN  citation  details
        ${bounds}=  Get BoundingBox  id=${box}
        Should Be True  abs(${bibtex}[x] - ${bounds}[x]) < 2
        Should Be True  abs(${bibtex}[width] - ${bounds}[width]) < 2
        Get Style  id=${box}  border-top-style  ==  solid
        Get Style  id=${box}  border-top-width  ==  1px
    END

Details show the citation and every filled field
    Add Article
    Open List
    Click  .reference-card
    Get Text  id=citation  ==  Martin, Robert (2008). Clean Code. Journal of Software, 12–34.
    Get Style  id=citation >> i  font-style  ==  italic
    Get Text  id=data-type  ==  article
    Get Text  id=data-key  ==  martin2008
    Get Text  id=data-author  ==  Martin, Robert
    Get Text  id=data-title  ==  Clean Code
    Get Text  id=data-journal  ==  Journal of Software
    Get Text  id=data-year  ==  2008
    Get Text  id=data-pages  ==  12-34
    Get Element Count  id=data-volume  ==  0

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
