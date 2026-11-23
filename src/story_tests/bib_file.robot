*** Settings ***
Resource  resource.robot
Library   OperatingSystem
Suite Setup      Open Browser That Accepts Downloads
Suite Teardown   Close Browser
Test Setup       Reset Application And Add References

*** Variables ***
${BIB_FILE}  ${TEMPDIR}${/}bibtexgen-robot-references.bib

*** Keywords ***
Open Browser That Accepts Downloads
    Open And Configure Browser
    New Context  acceptDownloads=True
    New Page  about:blank

Reset Application And Add References
    Reset Application
    Submit Registration  maija  ${PASSWORD}  ${PASSWORD}
    Add Article  Clean Code  2008
    Add Article  Clean Architecture  2017
    Add Article  Clean Agile  2019
    Go To  ${HOME_URL}/references

Add Article
    [Arguments]  ${title}  ${year}
    Go To  ${HOME_URL}/add
    Fill Text  id=author  Martin, Robert
    Fill Text  id=title  ${title}
    Fill Text  id=journal  Journal of Software
    Fill Text  id=year  ${year}
    Click  input[type="submit"]
    Get Text  .flash  *=  Reference added

Select
    [Arguments]  ${index}
    Click  .reference-select >> nth=${index}

Download Bib File
    [Documentation]  Clicks create .bib and returns the content of the downloaded file
    Remove File  ${BIB_FILE}
    ${promise}=  Promise To Wait For Download  ${BIB_FILE}
    Click  id=create-bib
    ${download}=  Wait For  ${promise}
    Should Be Equal  ${download}[suggestedFilename]  references.bib
    ${content}=  Get File  ${BIB_FILE}  encoding=UTF-8
    Remove File  ${BIB_FILE}
    RETURN  ${content}

*** Test Cases ***
Create .bib is between select all and delete
    ${select_all}=  Get BoundingBox  id=select-all
    ${create_bib}=  Get BoundingBox  id=create-bib
    ${delete}=  Get BoundingBox  id=delete-selected
    Get Text  id=create-bib  ==  create .bib
    Should Be True  abs(${select_all}[y] - ${create_bib}[y]) < 1
    Should Be True  abs(${create_bib}[y] - ${delete}[y]) < 1
    Should Be True  ${select_all}[x] + ${select_all}[width] < ${create_bib}[x]
    Should Be True  ${create_bib}[x] + ${create_bib}[width] < ${delete}[x]

Create .bib is grey and disabled until a reference is selected
    Get Element States  id=create-bib  contains  disabled
    ${grey}=  Get Style  id=create-bib  color
    Select  0
    Get Element States  id=create-bib  contains  enabled
    ${black}=  Get Style  id=create-bib  color
    Should Not Be Equal  ${grey}  ${black}
    Select  0
    Get Element States  id=create-bib  contains  disabled
    Click  id=select-all
    Get Element States  id=create-bib  contains  enabled
    Click  id=select-all
    Get Element States  id=create-bib  contains  disabled

Downloaded file has the selected references
    Select  0
    Select  2
    ${content}=  Download Bib File
    Should Start With  ${content}  @article{martin2019,\n
    Should Contain  ${content}  title${SPACE*3}= {Clean Agile}
    Should Contain  ${content}  }\n\n@article{martin2008,\n
    Should Contain  ${content}  title${SPACE*3}= {Clean Code}
    Should Not Contain  ${content}  Clean Architecture
    Should End With  ${content}  }\n

Downloaded file has every reference after select all
    Click  id=select-all
    ${content}=  Download Bib File
    Should Contain  ${content}  @article{martin2019,
    Should Contain  ${content}  @article{martin2017,
    Should Contain  ${content}  @article{martin2008,

Creating a file does not ask, delete or change the page
    Select  1
    Handle Future Dialogs  action=dismiss
    ${content}=  Download Bib File
    Should Contain  ${content}  @article{martin2017,
    Get Url  ==  ${HOME_URL}/references
    Get Element Count  .reference-card  ==  3
    Get Element Count  .flash  ==  0
    # the selection stays
    Get Checkbox State  .reference-select >> nth=1  ==  checked
    Get Element States  id=create-bib  contains  enabled
