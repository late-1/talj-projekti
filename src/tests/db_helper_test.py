from sqlalchemy import text

from config import db
from db_helper import reset_db, setup_db, setup_db_if_missing, tables
from repositories import reference_repository, user_repository


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
    assert setup_db_if_missing() == []
    assert user_count() == 1


def test_setup_if_missing_creates_tables_into_empty_database():
    for table in reversed(tables()):
        db.session.execute(text(f"DROP TABLE {table}"))
    db.session.commit()
    assert tables() == []

    assert setup_db_if_missing() == ["users", "bib_references"]
    assert tables() == ["users", "bib_references"]


def test_setup_if_missing_adds_new_tables_to_an_old_database():
    user_repository.create_user("maija", "secret-password")
    db.session.execute(text("DROP TABLE bib_references"))
    db.session.commit()

    assert setup_db_if_missing() == ["bib_references"]
    assert user_count() == 1


def test_reset_removes_rows_but_keeps_tables():
    user_repository.create_user("maija", "secret-password")
    reset_db()
    assert "users" in tables()
    assert user_count() == 0


def test_setup_creates_reference_table():
    assert "bib_references" in tables()


def test_foreign_keys_are_checked():
    assert db.session.execute(text("PRAGMA foreign_keys")).scalar() == 1


def test_setup_and_reset_work_when_users_have_references():
    for action in [reset_db, setup_db]:
        user = user_repository.create_user("maija", "secret-password")
        reference_repository.create_reference(
            user.id, "article",
            {"author": "Martin, Robert", "title": "Clean Code", "journal": "J", "year": "2008"},
        )
        action()
        assert user_count() == 0
        assert db.session.execute(text("SELECT COUNT(*) FROM bib_references")).scalar() == 0
