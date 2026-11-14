import pytest
from sqlalchemy import text

from config import db
from tests.conftest import PASSWORD


def user_count():
    return db.session.execute(text("SELECT COUNT(*) FROM users")).scalar()


# pages for users who are not logged in

def test_index_redirects_to_login_when_logged_out(client):
    response = client.get("/")
    assert response.status_code == 302
    assert response.headers["Location"] == "/login"


@pytest.mark.parametrize("url", ["/add", "/references"])
def test_pages_require_login(client, url):
    response = client.get(url)
    assert response.status_code == 302
    assert response.headers["Location"] == "/login"


def test_login_page_has_form_and_register_button(client):
    response = client.get("/login")
    assert response.status_code == 200
    assert b'action="/login"' in response.data
    assert b'href="/register"' in response.data


@pytest.mark.parametrize("url", ["/login", "/register"])
def test_logged_out_pages_have_no_top_bar(client, url):
    response = client.get(url)
    assert b"top-bar" not in response.data
    assert b'href="/add"' not in response.data
    assert b'href="/references"' not in response.data
    assert b'href="/logout"' not in response.data


def test_register_page_has_form(client):
    response = client.get("/register")
    assert response.status_code == 200
    assert b'action="/register"' in response.data
    assert b'name="password_confirmation"' in response.data


def test_stylesheet_is_served(client):
    response = client.get("/static/main.css")
    assert response.status_code == 200


# registering

def test_register_creates_user_logs_in_and_redirects(client, actions):
    response = actions.register("maija")
    assert response.status_code == 302
    assert response.headers["Location"] == "/"
    assert user_count() == 1

    session = actions.session()
    assert session["username"] == "maija"
    assert "user_id" in session
    assert "csrf_token" in session


def test_register_with_username_in_use(client, actions):
    actions.register("maija")
    actions.logout()

    response = actions.register("maija")
    assert response.status_code == 200
    assert b"Username already in use" in response.data
    assert "user_id" not in actions.session()
    assert user_count() == 1


@pytest.mark.parametrize("username", ["", "ab", "a" * 31, "maija m"])
def test_register_with_invalid_username(client, actions, username):
    response = actions.register(username)
    assert response.status_code == 200
    assert b"Username" in response.data
    assert "user_id" not in actions.session()
    assert user_count() == 0


def test_register_with_too_short_password(client, actions):
    response = actions.register("maija", "a" * 7)
    assert b"Password must be 8-100 characters long" in response.data
    assert "user_id" not in actions.session()
    assert user_count() == 0


def test_register_with_mismatching_passwords(client, actions):
    response = actions.register("maija", PASSWORD, PASSWORD + "x")
    assert b"Passwords do not match" in response.data
    assert user_count() == 0


def test_failed_register_keeps_username_in_form(client, actions):
    response = actions.register("maija", "short")
    assert b'value="maija"' in response.data


def test_register_strips_whitespace_around_username(client, actions):
    actions.register("  maija  ")
    assert actions.session()["username"] == "maija"


def test_register_with_missing_fields(client):
    response = client.post("/register", data={})
    assert response.status_code == 200
    assert user_count() == 0


# logging in and out

def test_login_with_correct_credentials(client, actions):
    actions.register("maija")
    actions.logout()

    response = actions.login("maija")
    assert response.status_code == 302
    assert response.headers["Location"] == "/"

    session = actions.session()
    assert session["username"] == "maija"
    assert "user_id" in session
    assert "csrf_token" in session


def test_login_with_wrong_password(client, actions):
    actions.register("maija")
    actions.logout()

    response = actions.login("maija", "wrong-password")
    assert response.status_code == 200
    assert b"Wrong username or password" in response.data
    assert b'value="maija"' in response.data
    assert "user_id" not in actions.session()


def test_login_with_unknown_user(client, actions):
    response = actions.login("maija")
    assert b"Wrong username or password" in response.data
    assert "user_id" not in actions.session()


def test_login_with_missing_fields(client, actions):
    response = client.post("/login", data={})
    assert response.status_code == 200
    assert "user_id" not in actions.session()


def test_login_logs_in_the_right_user(client, actions):
    actions.register("maija")
    maija_id = actions.session()["user_id"]
    actions.logout()
    actions.register("uolevi", "other-password")
    actions.logout()

    actions.login("maija")
    assert actions.session()["user_id"] == maija_id


def test_logout_clears_session_and_redirects_to_login(client, actions):
    actions.register("maija")

    response = actions.logout()
    assert response.headers["Location"] == "/login"
    assert actions.session() == {}
    assert client.get("/references").headers["Location"] == "/login"


def test_new_login_gets_new_csrf_token(client, actions):
    actions.register("maija")
    first_token = actions.session()["csrf_token"]
    actions.logout()
    actions.login("maija")
    assert actions.session()["csrf_token"] != first_token


# pages for users who are logged in

def test_index_redirects_to_references_when_logged_in(client, actions):
    actions.register("maija")
    response = client.get("/")
    assert response.headers["Location"] == "/references"


@pytest.mark.parametrize("url", ["/login", "/register"])
def test_login_and_register_pages_redirect_when_logged_in(client, actions, url):
    actions.register("maija")
    response = client.get(url)
    assert response.status_code == 302
    assert response.headers["Location"] == "/"


@pytest.mark.parametrize("url", ["/add", "/references"])
def test_top_bar_is_shown_when_logged_in(client, actions, url):
    actions.register("maija")
    response = client.get(url)
    assert response.status_code == 200
    assert b"top-bar" in response.data
    assert b'href="/add"' in response.data
    assert b'href="/references"' in response.data
    assert b'href="/logout"' in response.data


def test_top_bar_marks_current_page(client, actions):
    actions.register("maija")

    page = client.get("/add").get_data(as_text=True)
    assert '<a href="/add" class="active"' in page
    assert '<a href="/references" class="active"' not in page

    page = client.get("/references").get_data(as_text=True)
    assert '<a href="/references" class="active"' in page
    assert '<a href="/add" class="active"' not in page
