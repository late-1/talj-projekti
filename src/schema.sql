CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS bib_references (
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
);

CREATE INDEX IF NOT EXISTS idx_user_references ON bib_references (user_id);
