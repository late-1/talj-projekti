import os
import tempfile

# The configuration is read when the application is imported, so the test
# settings have to be in place before that. Tests never touch the real database.
_temp_dir = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
os.environ["DATABASE_URL"] = f"sqlite:///{os.path.join(_temp_dir.name, 'test.db')}"
os.environ["TEST_ENV"] = "true"
os.environ["SECRET_KEY"] = "test-secret"

# pylint: disable=wrong-import-position
import pytest  # noqa: E402

from app import app  # noqa: E402
from db_helper import setup_db  # noqa: E402

PASSWORD = "secret-password"

ARTICLE = {
    "entry_type": "article",
    "author": "Martin, Robert",
    "title": "Clean Code",
    "journal": "Journal of Software",
    "year": "2008",
}

BOOK = {
    "entry_type": "book",
    "author": "Fowler, Martin",
    "title": "Refactoring",
    "publisher": "Addison-Wesley",
    "year": "1999",
}

INPROCEEDINGS = {
    "entry_type": "inproceedings",
    "author": "Vihavainen, Arto and Luukkainen, Matti",
    "title": "Extreme Apprenticeship Method",
    "booktitle": "SIGCSE '11",
    "year": "2011",
}


@pytest.fixture(autouse=True)
def database():
    """Every test starts with an empty database"""
    with app.app_context():
        setup_db()
        yield


@pytest.fixture
def client():
    app.config["TESTING"] = True
    return app.test_client()


class Actions:
    def __init__(self, client):
        self.client = client

    def register(self, username, password=PASSWORD, password_confirmation=None):
        if password_confirmation is None:
            password_confirmation = password
        return self.client.post("/register", data={
            "username": username,
            "password": password,
            "password_confirmation": password_confirmation,
        })

    def login(self, username, password=PASSWORD):
        return self.client.post("/login", data={
            "username": username,
            "password": password,
        })

    def logout(self):
        return self.client.get("/logout")

    def csrf_token(self):
        return self.session().get("csrf_token", "")

    def add_reference(self, csrf_token=None, **fields):
        """Posts the add reference form; the defaults make a valid article"""
        data = dict(ARTICLE)
        data.update(fields)
        data["csrf_token"] = self.csrf_token() if csrf_token is None else csrf_token
        return self.client.post("/add", data=data)

    def session(self):
        with self.client.session_transaction() as session:
            return dict(session)


@pytest.fixture
def actions(client):
    return Actions(client)
