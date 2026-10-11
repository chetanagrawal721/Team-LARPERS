"""Human approvals with separation of duties (F6, R7). Authorisation is enforced server-side."""
import hmac

from . import audit, clock, config, seal
from .policy_loader import load_users
from .schemas import Decision


class GateError(Exception):
    """An API-level refusal carrying an HTTP status."""

    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status
        self.message = message


def authenticate(user: str | None, token: str | None) -> dict:
    """Demo-only auth: X-User plus a per-user token from .env. Agents have no user tokens."""
    users = load_users()
    if not user or user not in users:
        raise GateError(401, "unknown user")
    expected = config.user_token(user)
    if not expected or not token or not hmac.compare_digest(expected, token):
        raise GateError(401, "bad token")
    return {"id": user, **users[user]}


def _log(engine, user: str, action: str, decision: str, rule: str, payload: dict) -> None:
    audit.append(engine.state, int(clock.now()), user, action, payload, decision, rule, "rules-only",
                 engine.policy.hash)


def _refuse(engine, user: str, decision_id: str, status: int, msg: str, rule: str = "R7") -> None:
    _log(engine, user, "approve_refused", "BLOCK", rule, {"decision_id": decision_id, "reason": msg})
    raise GateError(status, msg)


def approve(engine, user: dict, decision_id: str, note: str = "") -> Decision:
    with engine.lock:
        rec = engine.get_record(decision_id)
        if not rec:
            raise GateError(404, "no such decision")
        d: Decision = rec["decision"]
        if d.verdict != "HOLD" or d.status != "pending":
            _refuse(engine, user["id"], decision_id, 409, f"decision is not awaiting approval (status {d.status})")
        if user["id"] == rec["requester"] and engine.mode == "C":
            _refuse(engine, user["id"], decision_id, 403, "requesters cannot approve their own requests")
        if not user.get("can_approve"):
            _refuse(engine, user["id"], decision_id, 403, "user is not authorised to approve")
        if user["id"] in d.approvals:
            _refuse(engine, user["id"], decision_id, 409, "already approved by this user")
        engine.state.execute("INSERT INTO approvals (decision_id, user, action, ts, note) VALUES (?,?,?,?,?)",
                             (decision_id, user["id"], "approve", int(clock.now()), note))
        d.approvals = d.approvals + [user["id"]]
        engine.trace(d.id, f"{user['id'].title()} approved ({len(d.approvals)} of {max(d.approvals_needed, 1)})", "ok", decision_id=d.id)
        if len(set(d.approvals)) >= max(d.approvals_needed, 1):
            meta, p = rec["meta"], rec["proposal"]
            seal.create(engine.state, decision_id=d.id, agent=p["agent"], action=p["action"], args=p["args"],
                        effect_hash=meta["effect_hash"], label_path_hash=meta["label_path_hash"],
                        label_catalog_ver=meta["label_catalog_ver"], policy_ver=engine.policy.rules_hash,
                        state_ver=meta["state_ver"], requester=rec["requester"], tier=d.tier,
                        approvers=d.approvals,
                        ttl=int(engine.policy.model.tiers.get("approval_ttl_seconds", seal.DEFAULT_TTL)))
            d.status = "approved"
        engine.save_decision(d)
        _log(engine, user["id"], "approve", d.verdict, "R7",
             {"decision_id": d.id, "approvals": d.approvals, "needed": d.approvals_needed,
              "sealed": d.status == "approved"})
        engine.emit("approval", d.id, user=user["id"], approvals=d.approvals, needed=d.approvals_needed,
                    status=d.status)
        return d


def reject(engine, user: dict, decision_id: str, note: str = "") -> Decision:
    with engine.lock:
        rec = engine.get_record(decision_id)
        if not rec:
            raise GateError(404, "no such decision")
        d: Decision = rec["decision"]
        if d.verdict != "HOLD" or d.status != "pending":
            _refuse(engine, user["id"], decision_id, 409, f"decision is not awaiting approval (status {d.status})")
        if not user.get("can_approve"):
            _refuse(engine, user["id"], decision_id, 403, "user is not authorised to reject")
        engine.state.execute("INSERT INTO approvals (decision_id, user, action, ts, note) VALUES (?,?,?,?,?)",
                             (decision_id, user["id"], "reject", int(clock.now()), note))
        d.status = "rejected"
        engine.save_decision(d)
        _log(engine, user["id"], "reject", "BLOCK", "R7", {"decision_id": d.id, "note": note})
        engine.emit("approval", d.id, user=user["id"], status="rejected")
        return d
