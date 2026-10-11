"""Hash-chained, tamper-evident audit log (R8, R10)."""
import hashlib
import json
import sqlite3

GENESIS = "0" * 64
FIELDS = ("ts", "agent", "action", "payload_json", "decision", "rule", "decision_path", "policy_hash")


def canonical(entry: dict) -> str:
    return json.dumps({k: entry.get(k) for k in FIELDS}, sort_keys=True, separators=(",", ":"))


def entry_hash(prev_hash: str, entry: dict) -> str:
    return hashlib.sha256((prev_hash + canonical(entry)).encode()).hexdigest()


def append(conn: sqlite3.Connection, ts: int, agent: str, action: str, payload: dict, decision: str,
           rule: str, decision_path: str, policy_hash: str) -> int:
    """Append one entry. Does not commit: callers do it inside the decision's transaction."""
    row = conn.execute("SELECT entry_hash FROM audit_log ORDER BY seq DESC LIMIT 1").fetchone()
    prev = row["entry_hash"] if row else GENESIS
    entry = {"ts": ts, "agent": agent, "action": action,
             "payload_json": json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str),
             "decision": decision, "rule": rule, "decision_path": decision_path, "policy_hash": policy_hash}
    h = entry_hash(prev, entry)
    cur = conn.execute(
        "INSERT INTO audit_log (prev_hash, ts, agent, action, payload_json, decision, rule, decision_path,"
        " policy_hash, entry_hash) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (prev, ts, agent, action, entry["payload_json"], decision, rule, decision_path, policy_hash, h))
    return cur.lastrowid


def verify(conn: sqlite3.Connection) -> dict:
    """Return {'ok': True} or {'ok': False, 'first_broken_seq': n}."""
    prev = GENESIS
    for r in conn.execute("SELECT * FROM audit_log ORDER BY seq"):
        if r["prev_hash"] != prev or entry_hash(prev, dict(r)) != r["entry_hash"]:
            return {"ok": False, "first_broken_seq": r["seq"]}
        prev = r["entry_hash"]
    return {"ok": True, "first_broken_seq": None}


def entries(conn: sqlite3.Connection, limit: int = 200) -> list[dict]:
    rows = conn.execute("SELECT * FROM audit_log ORDER BY seq DESC LIMIT ?", (limit,)).fetchall()
    return [dict(r) for r in rows]


def get(conn: sqlite3.Connection, seq: int) -> dict | None:
    r = conn.execute("SELECT * FROM audit_log WHERE seq=?", (seq,)).fetchone()
    return dict(r) if r else None
