from sqlalchemy import text

from config import db
from db_helper import reset_db, setup_db, setup_db_if_missing, tables
from repositories import user_repository


def user_count():
    return db.session.execute(text("SELECT COUNT(*) FROM users")).scalar()


def test_setup_creates_tables():
    assert "users" in tables()


def test_setup_drops_existing_data():
    user_repository.create_user("maija", "secret-password")
    setup_db()
    assert "users" in tables()
    assert user_count() == 0


def test_setup_if_missing_keeps_existing_data():
    user_repository.create_user("maija", "secret-password")
    assert setup_db_if_missing() is False
    assert user_count() == 1


def test_setup_if_missing_creates_tables_into_empty_database():
    for table in tables():
        db.session.execute(text(f"DROP TABLE {table}"))
    db.session.commit()
    assert tables() == []

    assert setup_db_if_missing() is True
    assert "users" in tables()


def test_reset_removes_rows_but_keeps_tables():
    user_repository.create_user("maija", "secret-password")
    reset_db()
    assert "users" in tables()
    assert user_count() == 0
