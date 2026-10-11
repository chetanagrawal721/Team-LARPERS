"""Signed requests (R01): HMAC-SHA256 over the canonical body, plus nonce and timestamp checks."""
import hashlib
import hmac
import json
import sqlite3

from . import clock, config
from .schemas import Proposal


def canonical_body(body: dict) -> str:
    return json.dumps({k: v for k, v in body.items() if k != "sig"}, sort_keys=True, separators=(",", ":"))


def sign(key: str, body: dict) -> str:
    return hmac.new(key.encode(), canonical_body(body).encode(), hashlib.sha256).hexdigest()


def check_signature(p: Proposal) -> tuple[bool, str]:
    key = config.agent_key(p.agent)
    if not key:
        return False, "no signing key for agent"
    expected = sign(key, p.model_dump())
    if not hmac.compare_digest(expected, p.sig):
        return False, "bad signature"
    return True, ""


def check_fresh(p: Proposal) -> tuple[bool, str]:
    drift = clock.now() - p.ts
    if drift > config.TS_WINDOW_SECONDS:
        return False, "stale timestamp"
    if drift < -config.TS_WINDOW_SECONDS:
        return False, "timestamp in the future"
    return True, ""


def consume_nonce(conn: sqlite3.Connection, p: Proposal) -> tuple[bool, str]:
    try:
        conn.execute("INSERT INTO nonces (nonce, agent, ts) VALUES (?,?,?)", (p.nonce, p.agent, p.ts))
    except sqlite3.IntegrityError:
        return False, "replayed nonce"
    return True, ""


def verify_proposal(conn: sqlite3.Connection, p: Proposal) -> tuple[bool, str]:
    """Order: signature, then freshness, then nonce (a nonce is only consumed by an authentic request)."""
    for check in (check_signature, check_fresh):
        ok, why = check(p)
        if not ok:
            return False, why
    return consume_nonce(conn, p)
