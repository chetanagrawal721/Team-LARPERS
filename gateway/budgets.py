"""Resource-keyed cumulative budgets charged on the resolved effect (S4, R08). Lives in the domain DB."""
import sqlite3

from . import clock
from .policy_loader import Policy

WINDOW_SECONDS = 3600


def keys_for(policy: Policy, agent: str, action: str) -> list[tuple[str, str, int]]:
    """(budget name, storage key, limit in minor units) for every budget that applies to this action."""
    out = []
    for name, b in policy.model.budgets.items():
        if b.get("action") != action:
            continue
        parts = [name] + [agent if k == "agent" else action for k in b.get("key", ["resource"])]
        out.append((name, ":".join(parts), int(b["amount"]) * 100))
    return out


def used(conn: sqlite3.Connection, key: str, now: float) -> int:
    r = conn.execute("SELECT COALESCE(SUM(amount),0) FROM budgets WHERE key=? AND ts>?", (key, now - WINDOW_SECONDS))
    return r.fetchone()[0]


def check(conn: sqlite3.Connection, policy: Policy, agent: str, action: str, amount_minor: int,
          now: float | None = None) -> dict:
    """Would charging `amount_minor` exceed any applicable budget? Returns a snapshot for the audit log."""
    now = clock.now() if now is None else now
    snap, exceeded = {}, []
    for name, key, limit in keys_for(policy, agent, action):
        u = used(conn, key, now)
        snap[key] = {"used": u, "limit": limit, "charge": amount_minor}
        if u + amount_minor > limit:
            exceeded.append(name)
    return {"exceeded": bool(exceeded), "which": exceeded, "snapshot": snap}


def charge(conn: sqlite3.Connection, policy: Policy, agent: str, action: str, amount_minor: int,
           now: float | None = None) -> dict:
    """Check and charge atomically. The caller must hold a write transaction (BEGIN IMMEDIATE)."""
    now = clock.now() if now is None else now
    res = check(conn, policy, agent, action, amount_minor, now)
    if res["exceeded"]:
        return res
    for _, key, _ in keys_for(policy, agent, action):
        conn.execute("INSERT INTO budgets (key, ts, amount) VALUES (?,?,?)", (key, int(now), amount_minor))
    return res


def check_and_charge_atomic(conn: sqlite3.Connection, policy: Policy, agent: str, action: str,
                            amount_minor: int, now: float | None = None) -> dict:
    conn.execute("BEGIN IMMEDIATE")
    try:
        res = charge(conn, policy, agent, action, amount_minor, now)
        conn.execute("COMMIT")
        return res
    except Exception:
        conn.execute("ROLLBACK")
        raise
