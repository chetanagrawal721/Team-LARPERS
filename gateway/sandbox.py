"""Sandbox copies: a SQLite database is one file, so a consistent copy of it is the practice-run environment."""
import pathlib
import sqlite3
import uuid

from . import config


def sandbox_dir() -> pathlib.Path:
    d = config.DATA_DIR / "sandbox"
    d.mkdir(parents=True, exist_ok=True)
    return d


def copy(src, dest_dir=None, name: str | None = None) -> pathlib.Path:
    """Copy `src` database to a new file using the SQLite backup API (consistent even if src is open)."""
    dest_dir = pathlib.Path(dest_dir) if dest_dir else sandbox_dir()
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / (name or f"sbx-{uuid.uuid4().hex[:10]}.db")
    s = sqlite3.connect(str(src))
    d = sqlite3.connect(str(dest))
    try:
        s.backup(d)
    finally:
        d.close()
        s.close()
    return dest


def cleanup(path) -> None:
    p = pathlib.Path(path)
    for suffix in ("", "-wal", "-shm", "-journal"):
        q = pathlib.Path(str(p) + suffix)
        if q.exists():
            q.unlink()
