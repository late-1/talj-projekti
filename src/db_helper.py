import os
import re
import sqlite3
import sys

from sqlalchemy import text

from config import app, db

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")


def tables():
    """Returns all table names from the database in the order they were created"""
    sql = text(
        "SELECT name FROM sqlite_master "
        "WHERE type = 'table' AND name NOT LIKE 'sqlite_%' "
        "ORDER BY rowid"
    )
    result = db.session.execute(sql)
    return [row[0] for row in result.fetchall()]


def reset_db():
    """Removes all rows from all tables"""
    # newest first, so that rows referring to other tables are removed first
    for table in reversed(tables()):
        db.session.execute(text(f"DELETE FROM {table}"))
    db.session.commit()


def create_tables():
    with open(SCHEMA_PATH, encoding="utf-8") as file:
        statements = [s.strip() for s in file.read().split(";") if s.strip()]

    for statement in statements:
        db.session.execute(text(statement))
    db.session.commit()


def setup_db():
    """
    Creates the database.
    If database tables already exist, those are dropped before the creation.
    """
    tables_in_db = tables()
    if tables_in_db:
        print(f"Tables exist, dropping: {', '.join(tables_in_db)}")
        for table in reversed(tables_in_db):
            db.session.execute(text(f"DROP TABLE {table}"))
        db.session.commit()

    print("Creating database")
    create_tables()


def setup_db_if_missing():
    """
    Creates the tables that do not exist yet and brings the existing tables
    up to date with schema.sql (see migrate_tables), keeping the existing data.
    Returns the names of the created tables.
    """
    tables_before = tables()
    create_tables()
    created = [table for table in tables() if table not in tables_before]

    if created:
        print(f"Created tables: {', '.join(created)}")

    migrated = migrate_tables()
    if migrated:
        print(f"Updated tables: {', '.join(migrated)}")
    return created


def _schema_tables():
    """
    The tables of schema.sql: name -> (columns, CREATE TABLE statement,
    CREATE INDEX statements). The schema is created in an empty in-memory
    database, so SQLite itself tells what the columns are.
    """
    with open(SCHEMA_PATH, encoding="utf-8") as file:
        schema = file.read()

    connection = sqlite3.connect(":memory:")
    try:
        connection.executescript(schema)
        result = {}
        for (name,) in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall():
            columns = connection.execute(f"PRAGMA table_info({name})").fetchall()
            create = connection.execute(
                "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = ?", (name,)
            ).fetchone()[0]
            indexes = [row[0] for row in connection.execute(
                "SELECT sql FROM sqlite_master WHERE type = 'index' AND tbl_name = ? "
                "AND sql IS NOT NULL", (name,)
            ).fetchall()]
            result[name] = (columns, create, indexes)
        return result
    finally:
        connection.close()


def _columns_in_db(table):
    return db.session.execute(text(f"PRAGMA table_info({table})")).fetchall()


def migrate_tables():
    """
    Rebuilds the tables whose columns differ from schema.sql (new columns, or
    a column that is no longer required), and copies the rows over with the
    same ids. Columns that are no longer in the schema are left out.
    Returns the names of the rebuilt tables.

    SQLite cannot change a column with ALTER TABLE, so a new table is created
    with a temporary name, the rows are copied there, and only then is the old
    table dropped and the new one renamed. If copying fails, the old table
    is left as it was.
    """
    migrated = []
    for name, (columns, create, indexes) in _schema_tables().items():
        current = _columns_in_db(name)
        # (name, type, not null, default, primary key) of each column
        if [tuple(c[1:]) for c in current] == [tuple(c[1:]) for c in columns]:
            continue

        new_name = f"{name}_new"
        current_names = {column[1] for column in current}
        common = ", ".join(column[1] for column in columns if column[1] in current_names)

        db.session.execute(text(f"DROP TABLE IF EXISTS {new_name}"))
        db.session.execute(text(
            re.sub(rf"^CREATE TABLE {name}\b", f"CREATE TABLE {new_name}", create)
        ))
        try:
            db.session.execute(text(
                f"INSERT INTO {new_name} ({common}) SELECT {common} FROM {name}"
            ))
        except Exception:
            db.session.rollback()
            db.session.execute(text(f"DROP TABLE IF EXISTS {new_name}"))
            db.session.commit()
            raise
        db.session.execute(text(f"DROP TABLE {name}"))
        db.session.execute(text(f"ALTER TABLE {new_name} RENAME TO {name}"))
        for index in indexes:
            db.session.execute(text(index))
        db.session.commit()
        migrated.append(name)
    return migrated


if __name__ == "__main__":
    with app.app_context():
        if "--if-missing" in sys.argv:
            setup_db_if_missing()
        else:
            setup_db()
