*** Settings ***
Resource  resource.robot
Suite Setup      Open And Configure Browser
Suite Teardown   Close Browser
Test Setup       Reset Application And Add Article

*** Keywords ***
Reset Application And Add Article
    Reset Application
    Submit Registration  maija  ${PASSWORD}  ${PASSWORD}
    Submit Article
    Get Text  .flash  *=  Reference added with the key martin2008

Submit Article
    [Arguments]  ${title}=Clean Code
    Go To  ${HOME_URL}/add
    Fill Text  id=author  Martin, Robert
    Fill Text  id=title  ${title}
    Fill Text  id=journal  Journal of Software
    Fill Text  id=year  2008
    Click  input[type="submit"]

Dialog Should Be Open
    [Arguments]  ${message}
    Get Element States  id=duplicate-dialog  contains  visible
    Get Text  id=duplicate-message  ==  ${message}

Dialog Should Be Closed
    Get Element States  id=duplicate-dialog  contains  hidden

Reference Count Should Be
    [Arguments]  ${count}
    Go To  ${HOME_URL}/references
    Get Element Count  .reference-card  ==  ${count}

*** Test Cases ***
Adding the same reference asks first
    Submit Article
    Dialog Should Be Open  The same reference already exists (martin2008). Add it anyway?
    Get Text  id=duplicate-confirm  ==  add
    Get Text  id=duplicate-cancel  ==  cancel

Dialog is modal and its buttons look like the other buttons
    Submit Article
    Dialog Should Be Open  The same reference already exists (martin2008). Add it anyway?
    # the page behind the dialog cannot be used
    ${modal}=  Evaluate JavaScript  id=duplicate-dialog  (dialog) => dialog.matches(":modal")
    Should Be True  ${modal}
    FOR  ${button}  IN  duplicate-confirm  duplicate-cancel
        Get Style  id=${button}  border-top-style  ==  solid
        Get Style  id=${button}  border-top-width  ==  1px
        Get Style  id=${button}  border-top-left-radius  ==  0px
    END
    ${confirm}=  Get Style  id=duplicate-confirm  outline-style
    ${cancel}=  Get Style  id=duplicate-cancel  outline-style
    Should Be Equal  ${confirm}  ${cancel}

Add in the dialog adds the reference with a new key
    Submit Article
    Click  id=duplicate-confirm
    Get Text  .flash  *=  Reference added with the key martin2008a
    Reference Count Should Be  2

Cancel closes the dialog and keeps the form filled
    Submit Article
    Click  id=duplicate-cancel
    Dialog Should Be Closed
    Get Url  ==  ${HOME_URL}/add
    Get Text  id=title  ==  Clean Code
    Get Text  id=author  ==  Martin, Robert
    Reference Count Should Be  1

Escape closes the dialog like cancel
    Submit Article
    Dialog Should Be Open  The same reference already exists (martin2008). Add it anyway?
    Keyboard Key  press  Escape
    Dialog Should Be Closed
    Get Text  id=title  ==  Clean Code
    Reference Count Should Be  1

Different reference is added without asking
    Submit Article  Clean Architecture
    Get Element Count  id=duplicate-dialog  ==  0
    Get Text  .flash  *=  Reference added with the key martin2008a

Saving an edited reference that is the same as another asks first
    Submit Article  Clean Architecture
    Go To  ${HOME_URL}/references
    Click  .reference-card >> nth=0
    Click  id=edit
    Fill Text  id=title  Clean Code
    Click  id=save
    Dialog Should Be Open  The same reference already exists (martin2008). Save it anyway?
    Get Text  id=duplicate-confirm  ==  save
    Click  id=duplicate-cancel
    Dialog Should Be Closed
    # still editing, the reference is unchanged
    Get Text  id=title  ==  Clean Code
    Get Text  id=bibtex  *=  {Clean Architecture}

Save in the dialog stores the edited reference
    Submit Article  Clean Architecture
    Go To  ${HOME_URL}/references
    Click  .reference-card >> nth=0
    Click  id=edit
    Fill Text  id=title  Clean Code
    Click  id=save
    Click  id=duplicate-confirm
    Get Element Count  id=reference-form  ==  0
    Get Text  id=bibtex  *=  title${SPACE*3}= {Clean Code}
    Go To  ${HOME_URL}/references
    Get Text  .reference-card >> nth=0 >> .reference-title  ==  Clean Code
    Get Text  .reference-card >> nth=1 >> .reference-title  ==  Clean Code
