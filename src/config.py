from os import getenv

from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.engine import Engine

load_dotenv()

test_env = getenv("TEST_ENV") == "true"

app = Flask(__name__)
app.secret_key = getenv("SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = getenv("DATABASE_URL")
db = SQLAlchemy(app)


@event.listens_for(Engine, "connect")
def enable_foreign_keys(dbapi_connection, _connection_record):
    """SQLite checks foreign keys only when asked to"""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.close()

    # SQLite compares only the letters a-z case-insensitively, so searching
    # uses this function to make also letters such as Ä and ä equal
    dbapi_connection.create_function(
        "casefold", 1, lambda value: value.casefold() if isinstance(value, str) else value,
        deterministic=True,
    )
