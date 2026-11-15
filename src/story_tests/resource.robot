*** Settings ***
Library  Browser

*** Variables ***
${SERVER}        localhost:5001
${DELAY}         500ms
${HOME_URL}      http://${SERVER}
${LOGIN_URL}     http://${SERVER}/login
${REGISTER_URL}  http://${SERVER}/register
${RESET_URL}     http://${SERVER}/reset_db
${BROWSER}       chromium
${HEADLESS}      false
${PASSWORD}      secret-password

*** Keywords ***
Open And Configure Browser
    IF  $HEADLESS == 'true'
        New Browser  browser=${BROWSER}  headless=True
    ELSE
        New Browser  browser=${BROWSER}  headless=False  slowMo=${DELAY}
    END
    New Context
    New Page  about:blank

Reset Application
    Go To  ${RESET_URL}

Submit Registration
    [Arguments]  ${username}  ${password}  ${confirmation}
    Go To  ${REGISTER_URL}
    Fill Text  id=username  ${username}
    Fill Text  id=password  ${password}
    Fill Text  id=password_confirmation  ${confirmation}
    Click  input[type="submit"]

Submit Login
    [Arguments]  ${username}  ${password}
    Go To  ${LOGIN_URL}
    Fill Text  id=username  ${username}
    Fill Text  id=password  ${password}
    Click  input[type="submit"]

Create User
    [Arguments]  ${username}  ${password}=${PASSWORD}
    Submit Registration  ${username}  ${password}  ${password}
    Click  text=log out

Login Page Should Be Open
    Get Url  ==  ${LOGIN_URL}
    Get Title  ==  Log in · bibtexgen

User Should Be Logged In
    Get Url  ==  ${HOME_URL}/references
    Get Element Count  nav.top-bar  ==  1

User Should Not Be Logged In
    Get Element Count  nav.top-bar  ==  0
