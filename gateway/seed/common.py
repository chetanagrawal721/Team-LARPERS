"""Shared helpers and bookkeeping tables for every domain database."""
import hashlib
import json
import pathlib
import sqlite3

# Bookkeeping tables are not part of an action's "effect" (they hold side-effect intents and counters).
BOOKKEEPING_TABLES = ("outbox", "delivered_messages", "budgets", "used_seals")

COMMON_SCHEMA = """
CREATE TABLE outbox (
  id INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT NOT NULL, recipient TEXT, subject TEXT, body TEXT,
  amount_minor INTEGER DEFAULT 0, payload_json TEXT, status TEXT NOT NULL DEFAULT 'pending',
  created_ts INTEGER, decision_id TEXT);
CREATE TABLE delivered_messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT, outbox_id INTEGER, kind TEXT, recipient TEXT, subject TEXT,
  amount_minor INTEGER, delivered_ts INTEGER);
CREATE TABLE budgets (id INTEGER PRIMARY KEY AUTOINCREMENT, key TEXT NOT NULL, ts INTEGER NOT NULL,
  amount INTEGER NOT NULL);
CREATE INDEX idx_budgets_key ON budgets(key, ts);
CREATE TABLE used_seals (nonce TEXT PRIMARY KEY, decision_id TEXT, ts INTEGER);
CREATE TABLE shared_files (path TEXT PRIMARY KEY, content TEXT, labels TEXT, label_path TEXT, written_by TEXT);
"""


def connect(path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(path), isolation_level=None, check_same_thread=False, timeout=10)
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def fresh_db(path, schema: str) -> sqlite3.Connection:
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    for suffix in ("", "-wal", "-shm", "-journal"):
        p = pathlib.Path(str(path) + suffix)
        if p.exists():
            p.unlink()
    conn = connect(path)
    conn.executescript(schema + COMMON_SCHEMA)
    return conn


def db_hash(path, tables: list[str] | None = None) -> str:
    """Content hash of a database (all tables, ordered), used to prove the real DB was not modified."""
    conn = sqlite3.connect(str(path))
    try:
        names = tables or [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
        h = hashlib.sha256()
        for t in names:
            h.update(t.encode())
            for row in conn.execute(f"SELECT * FROM {t} ORDER BY 1"):  # names come from sqlite_master
                h.update(json.dumps(row, default=str).encode())
        return h.hexdigest()
    finally:
        conn.close()
