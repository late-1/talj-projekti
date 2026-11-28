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
  author TEXT,
  editor TEXT,
  title TEXT,
  journal TEXT,
  booktitle TEXT,
  chapter TEXT,
  school TEXT,
  institution TEXT,
  organization TEXT,
  howpublished TEXT,
  publisher TEXT,
  year TEXT,
  month TEXT,
  volume TEXT,
  number TEXT,
  series TEXT,
  pages TEXT,
  address TEXT,
  edition TEXT,
  isbn TEXT,
  doi TEXT,
  url TEXT,
  note TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (user_id, cite_key)
);

CREATE INDEX IF NOT EXISTS idx_user_references ON bib_references (user_id);
