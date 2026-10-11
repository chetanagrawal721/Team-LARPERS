"""Deterministic fictional seed data for KartBazaar."""
import pathlib
import random
import sys

from .. import config
from .bank_seed import CITIES, FIRST, LAST
from .common import fresh_db

BUSINESS_TABLES = ["customers", "mailing_lists"]

SCHEMA = """
CREATE TABLE customers (id TEXT PRIMARY KEY, name TEXT, email TEXT, phone TEXT, city TEXT, spend_minor INTEGER);
CREATE TABLE mailing_lists (id TEXT PRIMARY KEY, list_name TEXT, email TEXT, declared TEXT);
"""


def seed(path=None) -> pathlib.Path:
    path = pathlib.Path(path or (config.DATA_DIR / "shop.db"))
    rng = random.Random(11)
    conn = fresh_db(path, SCHEMA)
    conn.execute("BEGIN")
    for n in range(1, 61):
        name = f"{rng.choice(FIRST)} {rng.choice(LAST)}"
        conn.execute("INSERT INTO customers VALUES (?,?,?,?,?,?)",
                     (f"K-{n:04d}", name, f"{name.split()[0].lower()}{n}@mail.example", f"+91-96{n:04d}{rng.randint(1000, 9999)}",
                      rng.choice(CITIES), rng.randrange(500, 90000) * 100))
    n = 0

    def member(lst, email, declared):
        nonlocal n
        n += 1
        conn.execute("INSERT INTO mailing_lists VALUES (?,?,?,?)", (f"M-{n:05d}", lst, email, declared))

    for i in range(1, 21):                       # 20 internal staff
        member("staff_internal", f"staff{i}@kartbazaar.example", "internal_email")
        member("staff_all", f"staff{i}@kartbazaar.example", "internal_email")
    for i in range(1, 38):                       # 37 external contractors silently added to the "staff" list
        member("staff_all", f"contractor{i}@outside.example", "internal_email")
    for i in range(1, 61):                       # newsletter subscribers
        member("newsletter", f"subscriber{i}@mail.example", "external_email")
    member("agency", "campaigns@brandboost.example", "external_email")
    conn.execute("COMMIT")
    conn.close()
    return path


if __name__ == "__main__":
    print(seed(sys.argv[1] if len(sys.argv) > 1 else None))
