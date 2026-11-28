import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, OperationalError

from config import db
from db_helper import migrate_tables, reset_db, setup_db, setup_db_if_missing, tables
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


# bringing an old database up to date (migrate_tables)

OLD_REFERENCE_TABLE = """
CREATE TABLE bib_references (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL REFERENCES users,
  entry_type TEXT NOT NULL,
  cite_key TEXT NOT NULL,
  author TEXT NOT NULL,
  title TEXT NOT NULL,
  year TEXT NOT NULL,
  journal TEXT,
  booktitle TEXT,
  publisher TEXT,
  volume TEXT,
  number TEXT,
  pages TEXT,
  address TEXT,
  edition TEXT,
  isbn TEXT,
  doi TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (user_id, cite_key)
)
"""


def columns(table):
    return {row[1]: row for row in db.session.execute(text(f"PRAGMA table_info({table})"))}


def make_old_database():
    """The reference table as it was before the new types, with two references"""
    user = user_repository.create_user("maija", "secret-password")
    db.session.execute(text("DROP TABLE bib_references"))
    db.session.execute(text(OLD_REFERENCE_TABLE))
    db.session.execute(text("CREATE INDEX idx_user_references ON bib_references (user_id)"))
    db.session.execute(text(
        "INSERT INTO bib_references (id, user_id, entry_type, cite_key, author, title, year, "
        "journal, volume, created_at) VALUES "
        "(5, :user, 'article', 'martin2008', 'Martin, Robert', 'Clean Code', '2008', "
        "'Journal of Software', '12', '2024-01-01 10:00:00'), "
        "(9, :user, 'book', 'fowler1999', 'Fowler, Martin', 'Refactoring', '1999', "
        "NULL, NULL, '2024-01-02 10:00:00')"
    ), {"user": user.id})
    db.session.commit()
    return user


def test_migration_keeps_the_references():
    user = make_old_database()
    assert setup_db_if_missing() == []

    references = reference_repository.get_references(user.id)
    assert [(r.id, r.cite_key) for r in references] == [(9, "fowler1999"), (5, "martin2008")]
    assert references[1].fields == {
        "author": "Martin, Robert", "title": "Clean Code", "journal": "Journal of Software",
        "year": "2008", "volume": "12",
    }
    created = db.session.execute(text("SELECT created_at FROM bib_references WHERE id = 5"))
    assert created.scalar() == "2024-01-01 10:00:00"


def test_migration_adds_the_new_columns_and_allows_empty_author_title_and_year():
    make_old_database()
    assert "url" not in columns("bib_references")
    assert columns("bib_references")["author"][3] == 1

    setup_db_if_missing()

    after = columns("bib_references")
    for name in ["editor", "chapter", "school", "institution", "organization", "howpublished",
                 "month", "series", "url", "note"]:
        assert name in after
    for name in ["author", "title", "year"]:
        assert after[name][3] == 0
    assert after["cite_key"][3] == 1
    assert tables() == ["users", "bib_references"]


def test_migrated_table_takes_new_types_and_continues_the_ids():
    user = make_old_database()
    setup_db_if_missing()
    misc = reference_repository.create_reference(user.id, "misc", {"title": "Some Page"})
    assert misc.id == 10
    assert reference_repository.get_reference(user.id, misc.id).fields == {"title": "Some Page"}


def test_migrated_table_keeps_its_rules():
    user = make_old_database()
    setup_db_if_missing()
    indexes = db.session.execute(text("PRAGMA index_list(bib_references)")).fetchall()
    assert "idx_user_references" in [row[1] for row in indexes]
    # the key is still unique for the user, and the user has to exist
    with pytest.raises(IntegrityError):
        db.session.execute(text(
            "INSERT INTO bib_references (user_id, entry_type, cite_key) "
            "VALUES (:user, 'misc', 'martin2008')"
        ), {"user": user.id})
    db.session.rollback()
    with pytest.raises(IntegrityError):
        db.session.execute(text(
            "INSERT INTO bib_references (user_id, entry_type, cite_key) VALUES (999, 'misc', 'x')"
        ))
    db.session.rollback()


def test_migration_is_done_only_once():
    make_old_database()
    assert migrate_tables() == ["bib_references"]
    assert not migrate_tables()


def test_up_to_date_database_is_not_migrated():
    assert not migrate_tables()


def test_failed_copy_leaves_the_old_table(monkeypatch):
    user = make_old_database()
    real_execute = db.session.execute

    def failing_execute(statement, *args, **kwargs):
        if str(statement).startswith("INSERT INTO bib_references_new"):
            raise OperationalError(str(statement), {}, Exception("disk full"))
        return real_execute(statement, *args, **kwargs)

    monkeypatch.setattr(db.session, "execute", failing_execute)
    with pytest.raises(OperationalError):
        migrate_tables()
    monkeypatch.undo()

    assert tables() == ["users", "bib_references"]
    assert "url" not in columns("bib_references")
    count = db.session.execute(text("SELECT COUNT(*) FROM bib_references WHERE user_id = :u"),
                               {"u": user.id})
    assert count.scalar() == 2
