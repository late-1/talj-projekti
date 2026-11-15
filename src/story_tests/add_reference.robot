*** Settings ***
Resource  resource.robot
Suite Setup      Open And Configure Browser
Suite Teardown   Close Browser
Test Setup       Reset Application And Open Add Page

*** Keywords ***
Reset Application And Open Add Page
    Reset Application
    Submit Registration  maija  ${PASSWORD}  ${PASSWORD}
    Click  .nav-left >> text=add
    Get Url  ==  ${HOME_URL}/add

Choose Type
    [Arguments]  ${type}
    Click  label[for="type-${type}"]

Fill Article
    [Arguments]  ${author}=Martin, Robert  ${title}=Clean Code  ${journal}=Journal of Software  ${year}=2008
    Fill Text  id=author  ${author}
    Fill Text  id=title  ${title}
    Fill Text  id=journal  ${journal}
    Fill Text  id=year  ${year}

Submit Reference
    Click  input[type="submit"]

Field Should Be Visible
    [Arguments]  ${name}
    Get Element States  id=${name}  contains  visible  enabled

Field Should Be Hidden
    [Arguments]  ${name}
    Get Element States  id=${name}  contains  hidden  disabled

*** Test Cases ***
Add page shows the article fields by default
    Get Checkbox State  id=type-article  ==  checked
    FOR  ${name}  IN  author  title  journal  year  volume  number  pages  doi  cite_key
        Field Should Be Visible  ${name}
    END
    FOR  ${name}  IN  booktitle  publisher  address  edition  isbn
        Field Should Be Hidden  ${name}
    END

Fields change when the type is changed
    Choose Type  book
    FOR  ${name}  IN  author  title  publisher  year  address  edition  isbn  cite_key
        Field Should Be Visible  ${name}
    END
    FOR  ${name}  IN  journal  booktitle  volume  number  pages  doi
        Field Should Be Hidden  ${name}
    END
    Choose Type  inproceedings
    FOR  ${name}  IN  author  title  booktitle  year  pages  publisher  doi  cite_key
        Field Should Be Visible  ${name}
    END
    FOR  ${name}  IN  journal  volume  number  address  edition  isbn
        Field Should Be Hidden  ${name}
    END

Optional fields are marked
    Get Text  label[for="volume"]  ==  volume (optional)
    Get Text  label[for="journal"]  ==  journal
    Choose Type  book
    Get Text  label[for="publisher"]  ==  publisher
    Choose Type  inproceedings
    Get Text  label[for="publisher"]  ==  publisher (optional)

User can add an article
    Fill Article
    Fill Text  id=volume  12
    Fill Text  id=pages  12-34
    Submit Reference
    Get Text  .flash  ==  Reference added with the key martin2008
    Get Url  ==  ${HOME_URL}/add?type=article
    Get Text  id=title  ==  ${EMPTY}

User can add a book
    Choose Type  book
    Fill Text  id=author  Fowler, Martin
    Fill Text  id=title  Refactoring
    Fill Text  id=publisher  Addison-Wesley
    Fill Text  id=year  1999
    Fill Text  id=isbn  978-0201485677
    Submit Reference
    Get Text  .flash  ==  Reference added with the key fowler1999
    # the form is ready for the next book
    Get Checkbox State  id=type-book  ==  checked
    Field Should Be Visible  publisher

User can add a conference paper
    Choose Type  inproceedings
    Fill Text  id=author  Vihavainen, Arto and Luukkainen, Matti
    Fill Text  id=title  Extreme Apprenticeship Method
    Fill Text  id=booktitle  SIGCSE '11
    Fill Text  id=year  2011
    Submit Reference
    Get Text  .flash  ==  Reference added with the key vihavainen2011

User can give the key
    Fill Article
    Fill Text  id=cite_key  cleancode
    Submit Reference
    Get Text  .flash  ==  Reference added with the key cleancode

Generated key gets a letter when the key is in use
    Fill Article
    Submit Reference
    Fill Article  title=Clean Architecture
    Submit Reference
    Get Text  .flash  ==  Reference added with the key martin2008a

Key that is in use is rejected and the form keeps its values
    Fill Article
    Fill Text  id=cite_key  cleancode
    Submit Reference
    Fill Article  title=Clean Architecture
    Fill Text  id=cite_key  cleancode
    Submit Reference
    Get Text  .flash  *=  Key cleancode is already in use
    Get Text  id=title  ==  Clean Architecture
    Get Text  id=cite_key  ==  cleancode

Reference is not added without required fields
    Fill Article  title=${EMPTY}
    Submit Reference
    # the browser stops the form because the field is required
    Get Element Count  .flash  ==  0
    Get Url  ==  ${HOME_URL}/add

Reference is not added with an invalid year
    Fill Article  year=200
    Submit Reference
    Get Element Count  .flash  ==  0
    Get Text  id=title  ==  Clean Code

Hidden fields of another type do not block the form
    Choose Type  book
    Fill Text  id=publisher  Addison-Wesley
    Choose Type  article
    Fill Article
    Submit Reference
    Get Text  .flash  ==  Reference added with the key martin2008
