*** Settings ***
Resource  resource.robot
Suite Setup      Open And Configure Browser
Suite Teardown   Close Browser
Test Setup       Reset Application And Add References

*** Keywords ***
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

Titles Should Be
    [Arguments]  @{titles}
    ${count}=  Get Length  ${titles}
    Get Element Count  .reference-card  ==  ${count}
    FOR  ${index}  ${title}  IN ENUMERATE  @{titles}
        Get Text  .reference-card >> nth=${index} >> .reference-title  ==  ${title}
    END

*** Test Cases ***
Search, advanced and delete are equally wide below each other
    ${search}=  Get BoundingBox  id=search
    ${advanced}=  Get BoundingBox  \#advanced summary
    ${delete}=  Get BoundingBox  id=delete-selected
    ${query}=  Get BoundingBox  id=query
    Should Be True  abs(${search}[width] - ${advanced}[width]) < 1
    Should Be True  abs(${search}[width] - ${delete}[width]) < 1
    Should Be True  abs(${search}[x] - ${advanced}[x]) < 1
    Should Be True  abs(${search}[x] - ${delete}[x]) < 1
    # the buttons are on the right of the search field
    Should Be True  ${query}[x] + ${query}[width] < ${search}[x]
    # advanced is close to search, delete a bit further from advanced
    ${gap_above}=  Evaluate  ${advanced}[y] - ${search}[y] - ${search}[height]
    ${gap_below}=  Evaluate  ${delete}[y] - ${advanced}[y] - ${advanced}[height]
    Should Be True  0 < ${gap_above} < ${gap_below}

Delete stays below the advanced fields when they are open
    Click  \#advanced summary
    Get Element States  id=author  contains  visible
    ${advanced}=  Get BoundingBox  \#advanced summary
    ${fields}=  Get BoundingBox  id=advanced-fields
    ${delete}=  Get BoundingBox  id=delete-selected
    ${query}=  Get BoundingBox  id=query
    Should Be True  ${advanced}[y] + ${advanced}[height] <= ${fields}[y]
    Should Be True  ${fields}[y] + ${fields}[height] <= ${delete}[y]
    # the fields use the whole width
    Should Be True  abs(${fields}[x] - ${query}[x]) < 1
    Should Be True  abs(${fields}[x] + ${fields}[width] - ${delete}[x] - ${delete}[width]) < 1

Delete is grey and disabled until a reference is selected
    Get Element States  id=delete-selected  contains  disabled
    ${grey}=  Get Style  id=delete-selected  color
    Select  1
    Get Element States  id=delete-selected  contains  enabled
    ${black}=  Get Style  id=delete-selected  color
    Should Not Be Equal  ${grey}  ${black}
    Select  1
    Get Element States  id=delete-selected  contains  disabled

Every reference has a checkbox in the lower right corner of its box
    ${count}=  Get Element Count  .reference-select
    Should Be Equal As Integers  ${count}  3
    FOR  ${index}  IN RANGE  3
        ${card}=  Get BoundingBox  .reference-card >> nth=${index}
        ${box}=  Get BoundingBox  .reference-select >> nth=${index}
        ${right_gap}=  Evaluate  ${card}[x] + ${card}[width] - ${box}[x] - ${box}[width]
        ${bottom_gap}=  Evaluate  ${card}[y] + ${card}[height] - ${box}[y] - ${box}[height]
        # inside the box, about the width of one space from its line
        Should Be True  2 <= ${right_gap} <= 8
        Should Be True  2 <= ${bottom_gap} <= 8
    END

Checkbox has the same line as the box of the reference
    ${card_color}=  Get Style  .reference-card >> nth=0  border-top-color
    Get Style  .reference-select >> nth=0  border-top-color  ==  ${card_color}
    Get Style  .reference-select >> nth=0  border-top-style  ==  solid
    Get Style  .reference-select >> nth=0  border-top-width  ==  1px

Selected checkbox shows a cross
    Get Style  .reference-select >> nth=0  background-image  ==  none
    Select  0
    Get Checkbox State  .reference-select >> nth=0  ==  checked
    Get Style  .reference-select >> nth=0  background-image  *=  linear-gradient
    ${card_color}=  Get Style  .reference-card >> nth=0  border-top-color
    Get Style  .reference-select >> nth=0  background-image  *=  ${card_color}

Selecting does not open the reference
    Select  0
    Get Url  ==  ${HOME_URL}/references
    Click  .reference-card >> nth=0
    Get Url  matches  ${HOME_URL}/references/\\d+

Delete removes the selected references
    Select  0
    Select  2
    Handle Future Dialogs  action=accept
    Click  id=delete-selected
    Get Url  ==  ${HOME_URL}/references
    Get Text  .flash  *=  2 references deleted
    Titles Should Be  Clean Architecture

Delete asks first and can be cancelled
    Select  0
    Handle Future Dialogs  action=dismiss
    Click  id=delete-selected
    Get Url  ==  ${HOME_URL}/references
    Titles Should Be  Clean Agile  Clean Architecture  Clean Code

Delete returns to the search
    Go To  ${HOME_URL}/references?query=clean+201
    Titles Should Be  Clean Agile  Clean Architecture
    Select  1
    Handle Future Dialogs  action=accept
    Click  id=delete-selected
    Get Url  ==  ${HOME_URL}/references?query=clean+201
    Get Text  .flash  *=  1 reference deleted
    Titles Should Be  Clean Agile

Select all is on the left of delete
    ${select_all}=  Get BoundingBox  id=select-all
    ${delete}=  Get BoundingBox  id=delete-selected
    Should Be True  abs(${select_all}[y] - ${delete}[y]) < 1
    Should Be True  ${select_all}[x] + ${select_all}[width] < ${delete}[x]
    Get Text  id=select-all  ==  select all

Select all selects every reference and turns into unselect
    Click  id=select-all
    FOR  ${index}  IN RANGE  3
        Get Checkbox State  .reference-select >> nth=${index}  ==  checked
    END
    Get Text  id=select-all  ==  unselect
    Get Element States  id=delete-selected  contains  enabled
    Get Url  ==  ${HOME_URL}/references

Unselect clears every selection
    Click  id=select-all
    Click  id=select-all
    FOR  ${index}  IN RANGE  3
        Get Checkbox State  .reference-select >> nth=${index}  ==  unchecked
    END
    Get Text  id=select-all  ==  select all
    Get Element States  id=delete-selected  contains  disabled

Text follows the checkboxes selected by hand
    Select  0
    Select  1
    Get Text  id=select-all  ==  select all
    Select  2
    Get Text  id=select-all  ==  unselect
    Select  1
    Get Text  id=select-all  ==  select all
    # with some selected, select all selects the rest
    Click  id=select-all
    Get Checkbox State  .reference-select >> nth=1  ==  checked
    Get Text  id=select-all  ==  unselect

Select all selects only the search results
    Go To  ${HOME_URL}/references?query=clean+201
    Titles Should Be  Clean Agile  Clean Architecture
    Click  id=select-all
    Get Text  id=select-all  ==  unselect
    Handle Future Dialogs  action=accept
    Click  id=delete-selected
    Get Text  .flash  *=  2 references deleted
    Go To  ${HOME_URL}/references
    Titles Should Be  Clean Code

Select all is disabled when the search finds nothing
    Go To  ${HOME_URL}/references?query=zzz
    Get Element Count  .reference-card  ==  0
    Get Element States  id=select-all  contains  disabled
    Get Element States  id=delete-selected  contains  disabled
