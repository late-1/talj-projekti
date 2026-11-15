*** Settings ***
Resource  resource.robot
Suite Setup      Open And Configure Browser
Suite Teardown   Close Browser
Test Setup       Reset Application

*** Test Cases ***
Logged out user is taken to the login page
    Go To  ${HOME_URL}
    Login Page Should Be Open
    User Should Not Be Logged In

Logged out user cannot open the application pages
    Go To  ${HOME_URL}/references
    Login Page Should Be Open
    Go To  ${HOME_URL}/add
    Login Page Should Be Open

Login page has a register button
    Go To  ${LOGIN_URL}
    Click  text=register
    Get Url  ==  ${REGISTER_URL}
    User Should Not Be Logged In

User can register
    Submit Registration  maija  ${PASSWORD}  ${PASSWORD}
    User Should Be Logged In

Registering fails with a too short password
    Submit Registration  maija  short  short
    # the browser stops the form because of the minlength attribute
    Get Url  ==  ${REGISTER_URL}
    User Should Not Be Logged In

Registering fails with mismatching passwords
    Submit Registration  maija  ${PASSWORD}  other-password
    Get Text  .flash  ==  Passwords do not match
    User Should Not Be Logged In

Registering fails with a username that is in use
    Create User  maija
    Submit Registration  maija  ${PASSWORD}  ${PASSWORD}
    Get Text  .flash  *=  Username already in use
    User Should Not Be Logged In

User can log in
    Create User  maija
    Submit Login  maija  ${PASSWORD}
    User Should Be Logged In

Login fails with a wrong password
    Create User  maija
    Submit Login  maija  wrong-password
    Get Text  .flash  ==  Wrong username or password
    User Should Not Be Logged In

Login fails with an unknown username
    Submit Login  uolevi  ${PASSWORD}
    Get Text  .flash  ==  Wrong username or password
    User Should Not Be Logged In

User can log out
    Submit Registration  maija  ${PASSWORD}  ${PASSWORD}
    Click  text=log out
    Login Page Should Be Open
    Go To  ${HOME_URL}/references
    Login Page Should Be Open

Top bar links work and the current page is underlined
    Submit Registration  maija  ${PASSWORD}  ${PASSWORD}
    Get Text  .nav-left a.active  ==  view / search
    Get Style  .nav-left a.active  text-decoration-line  ==  underline
    Click  .nav-left >> text=add
    Get Url  ==  ${HOME_URL}/add
    Get Text  .nav-left a.active  ==  add
    Get Element Count  .nav-left a  ==  2
    Get Text  .nav-right a  ==  log out
    Click  .nav-left >> text=view / search
    Get Url  ==  ${HOME_URL}/references
