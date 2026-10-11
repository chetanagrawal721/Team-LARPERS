import sqlite3
import subprocess

import pytest

from gateway import sandbox
from gateway.seed import bank_seed
from gateway.seed.common import db_hash


@pytest.fixture(scope="module")
def bank_db(tmp_path_factory):
    return bank_seed.seed(tmp_path_factory.mktemp("seed") / "bank.db")


def q(path, sql, *a):
    c = sqlite3.connect(str(path))
    try:
        return c.execute(sql, a).fetchall()
    finally:
        c.close()


def test_tables_exist(bank_db):
    names = {r[0] for r in q(bank_db, "SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"customers", "transactions", "refunds", "invoices", "vendors", "inbox", "outbox", "budgets"} <= names


def test_deterministic(bank_db, tmp_path):
    other = bank_seed.seed(tmp_path / "again.db")
    assert db_hash(bank_db) == db_hash(other)


def test_fixture_c1042(bank_db):
    n, total = q(bank_db, "SELECT COUNT(*), SUM(amount_minor) FROM transactions "
                          "WHERE customer_id='C-1042' AND month='March' AND is_duplicate=1")[0]
    assert n == 3 and total == 640000


def test_broad_match_fixture(bank_db):
    n, cust, total = q(bank_db, "SELECT COUNT(*), COUNT(DISTINCT customer_id), SUM(amount_minor) FROM transactions "
                                "WHERE month='March' AND is_duplicate=1")[0]
    assert (n, cust, total) == (212, 61, 98_000_000)


def test_forty_pending_invoices(bank_db):
    assert q(bank_db, "SELECT COUNT(*) FROM invoices WHERE status='pending'")[0][0] == 40


def test_fk_cascade_is_real(bank_db, tmp_path):
    cp = sandbox.copy(bank_db, tmp_path)
    c = sqlite3.connect(str(cp))
    c.execute("PRAGMA foreign_keys=ON")
    c.execute("INSERT INTO refunds VALUES ('RF-X','T-000001','C-1',100,1)")
    c.execute("DELETE FROM transactions WHERE id='T-000001'")
    assert c.execute("SELECT COUNT(*) FROM refunds WHERE id='RF-X'").fetchone()[0] == 0
    c.close()


def test_sandbox_isolation_and_cleanup(bank_db, tmp_path):
    before = db_hash(bank_db)
    cp = sandbox.copy(bank_db, tmp_path)
    c = sqlite3.connect(str(cp))
    c.execute("DELETE FROM customers WHERE id='C-0007'")
    c.commit()
    c.close()
    assert db_hash(bank_db) == before
    sandbox.cleanup(cp)
    assert not cp.exists()


def test_db_not_tracked():
    out = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True).stdout
    assert ".db" not in out
