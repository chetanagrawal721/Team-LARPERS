"""Effect seal (C4) and typed drift detection (C5). A seal is an HMAC-signed token bound to the measured effect."""
import hashlib
import hmac
import json
import secrets
import sqlite3

from . import clock, config

SEAL_FIELDS = ("decision_id", "action_hash", "effect_hash", "label_path_hash", "label_catalog_ver", "policy_ver",
               "state_ver", "requester", "tier", "approvers", "nonce", "expiry")
DEFAULT_TTL = 900


def action_hash(agent: str, action: str, args: dict) -> str:
    body = json.dumps({"agent": agent, "action": action, "args": args}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(body.encode()).hexdigest()


def _canon(token: dict) -> bytes:
    return json.dumps({k: token.get(k) for k in SEAL_FIELDS}, sort_keys=True, separators=(",", ":")).encode()


def sign(token: dict) -> str:
    return hmac.new(config.seal_key(), _canon(token), hashlib.sha256).hexdigest()


def create(state: sqlite3.Connection, *, decision_id: str, agent: str, action: str, args: dict, effect_hash: str,
           label_path_hash: str, label_catalog_ver: str, policy_ver: str, state_ver: str, requester: str, tier: str,
           approvers: list[str], ttl: int = DEFAULT_TTL) -> dict:
    token = {"decision_id": decision_id, "action_hash": action_hash(agent, action, args), "effect_hash": effect_hash,
             "label_path_hash": label_path_hash, "label_catalog_ver": label_catalog_ver, "policy_ver": policy_ver,
             "state_ver": state_ver, "requester": requester, "tier": tier, "approvers": sorted(approvers),
             "nonce": secrets.token_hex(12), "expiry": int(clock.now()) + ttl}
    token["sig"] = sign(token)
    state.execute("INSERT OR REPLACE INTO seals (decision_id, token_json, nonce, used) VALUES (?,?,?,0)",
                  (decision_id, json.dumps(token, sort_keys=True), token["nonce"]))
    return token


def load(state: sqlite3.Connection, decision_id: str) -> tuple[dict | None, bool]:
    r = state.execute("SELECT token_json, used FROM seals WHERE decision_id=?", (decision_id,)).fetchone()
    return (json.loads(r["token_json"]), bool(r["used"])) if r else (None, False)


def mark_used(state: sqlite3.Connection, decision_id: str) -> None:
    state.execute("UPDATE seals SET used=1 WHERE decision_id=?", (decision_id,))


def check(token: dict, fresh: dict, now: float | None = None) -> str:
    """Return 'OK' or a drift type. Components are compared in a fixed order so the reported reason is the most
    fundamental one: signature, expiry, replay, args, policy, label, effect, state. Missing `fresh` keys are skipped
    (cheap checks run before the action is re-executed; the rest after)."""
    now = clock.now() if now is None else now
    if not hmac.compare_digest(sign(token), str(token.get("sig", ""))):
        return "bad_signature"
    if now > token["expiry"]:
        return "expired"
    if fresh.get("nonce_used"):
        return "replay"
    if "action_hash" in fresh and fresh["action_hash"] != token["action_hash"]:
        return "args_drift"
    if "policy_ver" in fresh and fresh["policy_ver"] != token["policy_ver"]:
        return "policy_drift"
    if ("label_catalog_ver" in fresh and fresh["label_catalog_ver"] != token["label_catalog_ver"]) or (
            "label_path_hash" in fresh and fresh["label_path_hash"] != token["label_path_hash"]):
        return "label_drift"
    if "effect_hash" in fresh and fresh["effect_hash"] != token["effect_hash"]:
        return "effect_drift"
    if "state_ver" in fresh and fresh["state_ver"] != token["state_ver"]:
        return "state_drift"
    return "OK"
