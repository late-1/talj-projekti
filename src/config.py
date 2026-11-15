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
