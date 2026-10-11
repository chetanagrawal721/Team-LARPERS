"""Deterministic fictional seed data for Pune Care Hospital."""
import pathlib
import random
import sys

from .. import config
from .bank_seed import FIRST, LAST
from .common import fresh_db

BUSINESS_TABLES = ["patients", "reports", "appointments", "doctors"]

SCHEMA = """
CREATE TABLE doctors (id TEXT PRIMARY KEY, name TEXT, email TEXT);
CREATE TABLE patients (id TEXT PRIMARY KEY, name TEXT, phone TEXT, email TEXT, diagnosis TEXT);
CREATE TABLE reports (id TEXT PRIMARY KEY, patient_id TEXT REFERENCES patients(id) ON DELETE CASCADE,
  summary TEXT, ts INTEGER);
CREATE TABLE appointments (id TEXT PRIMARY KEY, patient_id TEXT REFERENCES patients(id) ON DELETE CASCADE,
  doctor_id TEXT REFERENCES doctors(id), ts INTEGER);
"""
DIAGNOSES = ["hypertension", "type 2 diabetes", "asthma", "fracture follow-up", "migraine", "anaemia"]


def seed(path=None) -> pathlib.Path:
    path = pathlib.Path(path or (config.DATA_DIR / "hospital.db"))
    rng = random.Random(7)
    conn = fresh_db(path, SCHEMA)
    conn.execute("BEGIN")
    conn.execute("INSERT INTO doctors VALUES ('D-1','Dr. Shah','dr.shah@punecare.example')")
    conn.execute("INSERT INTO doctors VALUES ('D-2','Dr. Menon','dr.menon@punecare.example')")
    for n in range(1, 341):
        pid = f"P-{n:04d}"
        name = "Ramesh Kulkarni" if n == 1 else f"{rng.choice(FIRST)} {rng.choice(LAST)}"
        conn.execute("INSERT INTO patients VALUES (?,?,?,?,?)",
                     (pid, name, f"+91-97{n:04d}{rng.randint(1000, 9999)}",
                      f"{name.split()[0].lower()}{n}@mail.example", rng.choice(DIAGNOSES)))
        if n < 300:
            conn.execute("INSERT INTO reports VALUES (?,?,?,?)", (f"R-{n:04d}", pid, f"Discharge summary {n}", 1_740_000_000))
    for k in range(12):
        conn.execute("INSERT INTO appointments VALUES (?,?,?,?)", (f"A-{k + 1:04d}", "P-0100", "D-1", 1_750_000_000 + k))
    conn.execute("INSERT INTO appointments VALUES ('A-0100','P-0001','D-2',1750000000)")
    conn.execute("COMMIT")
    conn.close()
    return path


if __name__ == "__main__":
    print(seed(sys.argv[1] if len(sys.argv) > 1 else None))
