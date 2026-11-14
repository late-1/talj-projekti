import os
import sys

from sqlalchemy import text

from config import app, db

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")


def tables():
    """Returns all table names from the database"""
    sql = text(
        "SELECT name FROM sqlite_master "
        "WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
    )
    result = db.session.execute(sql)
    return [row[0] for row in result.fetchall()]


def reset_db():
    """Removes all rows from all tables"""
    for table in tables():
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
        for table in tables_in_db:
            db.session.execute(text(f"DROP TABLE {table}"))
        db.session.commit()

    print("Creating database")
    create_tables()


def setup_db_if_missing():
    """Creates the tables only when the database is empty"""
    if tables():
        return False

    print("Creating database")
    create_tables()
    return True


if __name__ == "__main__":
    with app.app_context():
        if "--if-missing" in sys.argv:
            setup_db_if_missing()
        else:
            setup_db()
