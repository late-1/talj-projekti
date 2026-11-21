*** Settings ***
Resource  resource.robot
Suite Setup      Open And Configure Browser
Suite Teardown   Close Browser
Test Setup       Reset Application And Open Reference

*** Keywords ***
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

Reset Application And Open Reference
    Reset Application
    Submit Registration  maija  ${PASSWORD}  ${PASSWORD}
    Add Article
    Go To  ${HOME_URL}/references
    Click  .reference-card
    Get Text  id=bibtex  *=  @article{martin2008,

Edit Form Should Be Closed
    Get Element Count  id=reference-form  ==  0
    Get Url  matches  ${HOME_URL}/references/\\d+(\\?back=.*)?$

*** Test Cases ***
Edit button opens the form above the BibTeX
    Get Element Count  id=reference-form  ==  0
    Click  id=edit
    Get Url  matches  ${HOME_URL}/references/\\d+/edit
    Get Text  id=author  ==  Martin, Robert
    Get Text  id=title  ==  Clean Code
    Get Text  id=journal  ==  Journal of Software
    Get Text  id=year  ==  2008
    Get Text  id=pages  ==  12-34
    Get Text  id=cite_key  ==  martin2008
    Get Checkbox State  id=type-article  ==  checked
    ${form}=  Get BoundingBox  id=reference-form
    ${bibtex}=  Get BoundingBox  id=bibtex
    Should Be True  ${form}[y] + ${form}[height] <= ${bibtex}[y]
    Should Be True  abs(${form}[x] - ${bibtex}[x]) < 2

Save and cancel buttons are below the fields
    Click  id=edit
    ${key}=  Get BoundingBox  id=cite_key
    ${save}=  Get BoundingBox  id=save
    ${cancel}=  Get BoundingBox  id=cancel
    Should Be True  ${key}[y] + ${key}[height] <= ${save}[y]
    Should Be True  abs(${save}[y] - ${cancel}[y]) < 2
    Should Be True  ${save}[x] < ${cancel}[x]

Buttons stay above the form while editing
    Click  id=edit
    ${form}=  Get BoundingBox  id=reference-form
    ${bibtex}=  Get BoundingBox  id=bibtex
    FOR  ${button}  IN  back  copy  edit  delete
        ${box}=  Get BoundingBox  id=${button}
        Should Be True  ${box}[y] + ${box}[height] <= ${form}[y]
        Should Be True  ${box}[x] >= ${bibtex}[x] - 1
        Should Be True  ${box}[x] + ${box}[width] <= ${bibtex}[x] + ${bibtex}[width] + 1
    END

Save updates the BibTeX and closes the form
    Click  id=edit
    Fill Text  id=title  Cleaner Code
    Fill Text  id=year  2009
    Fill Text  id=pages  ${EMPTY}
    Click  id=save
    Edit Form Should Be Closed
    Get Text  id=bibtex  *=  title${SPACE*3}= {Cleaner Code}
    Get Text  id=bibtex  *=  year${SPACE*4}= {2009}
    Get Text  id=bibtex  not contains  pages
    Get Text  id=bibtex  *=  @article{martin2008,
    Get Text  id=data-title  ==  Cleaner Code
    Get Text  id=data-year  ==  2009
    Get Element Count  id=data-pages  ==  0

Cancel closes the form without changes
    Click  id=edit
    Fill Text  id=title  Cleaner Code
    Click  id=cancel
    Edit Form Should Be Closed
    Get Text  id=bibtex  *=  title${SPACE*3}= {Clean Code}

Type can be changed while editing
    Click  id=edit
    Click  label[for="type-book"]
    Get Element States  id=journal  contains  hidden
    Get Element States  id=publisher  contains  visible  enabled
    Fill Text  id=publisher  Prentice Hall
    Click  id=save
    Edit Form Should Be Closed
    Get Text  id=bibtex  *=  @book{martin2008,
    Get Text  id=bibtex  *=  publisher = {Prentice Hall}
    Get Text  id=bibtex  not contains  journal

Key can be changed while editing
    Click  id=edit
    Fill Text  id=cite_key  cleancode
    Click  id=save
    Get Text  id=bibtex  *=  @article{cleancode,

Invalid values are not saved
    Click  id=edit
    # the browser checks are passed by, so that the server has to reject the value
    Evaluate JavaScript  id=reference-form  (form) => form.setAttribute("novalidate", "")
    Fill Text  id=year  08
    Click  id=save
    Get Text  .flash  *=  Year must be a four-digit number
    Get Element Count  id=reference-form  ==  1
    Get Text  id=year  ==  08
    Get Text  id=bibtex  *=  year${SPACE*4}= {2008}

Edited reference is changed in the list
    Click  id=edit
    Fill Text  id=title  Cleaner Code
    Click  id=save
    Click  id=back
    Get Url  ==  ${HOME_URL}/references
    Get Text  .reference-card  *=  Cleaner Code

Back returns to the search after editing
    Go To  ${HOME_URL}/references?query=clean
    Click  .reference-card
    Click  id=edit
    Fill Text  id=title  Clean Coder
    Click  id=save
    Click  id=back
    Get Url  ==  ${HOME_URL}/references?query=clean
    Get Text  .reference-card  *=  Clean Coder

Delete removes the reference
    Handle Future Dialogs  action=accept
    Click  id=delete
    Get Url  ==  ${HOME_URL}/references
    Get Text  .flash  *=  Reference martin2008 deleted
    Get Element Count  .reference-card  ==  0
    Get Text  main  *=  No references yet

Delete asks first and can be cancelled
    Handle Future Dialogs  action=dismiss
    Click  id=delete
    Get Url  matches  ${HOME_URL}/references/\\d+
    Get Text  id=bibtex  *=  @article{martin2008,
    Go To  ${HOME_URL}/references
    Get Element Count  .reference-card  ==  1

Delete returns to the search the user came from
    Add Article  title=Clean Architecture  year=2017
    Go To  ${HOME_URL}/references?query=clean
    Click  .reference-card >> nth=0
    Handle Future Dialogs  action=accept
    Click  id=delete
    Get Url  ==  ${HOME_URL}/references?query=clean
    Get Element Count  .reference-card  ==  1
    Get Text  .reference-card  *=  Clean Code
