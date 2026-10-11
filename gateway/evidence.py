"""Evidence trail for one decision: the chain of facts that led to its outcome, rebuilt from the audit log and state."""
import json

from . import audit
from .approvals import GateError
from .schemas import Decision


def _money(minor: int) -> str:
    r = round((minor or 0) / 100)
    if r >= 100000:
        return f"₹{r / 100000:.2f}".rstrip("0").rstrip(".") + " lakh"
    return f"₹{r:,}"


def build(engine, seq: int) -> dict:
    entry = audit.get(engine.state, seq)
    if not entry:
        raise GateError(404, "no such audit entry")
    payload = json.loads(entry["payload_json"])
    did = payload.get("decision_id")
    base = {"seq": seq, "when": entry["ts"], "agent": entry["agent"], "action": entry["action"],
            "entry_hash": entry["entry_hash"], "prev_hash": entry["prev_hash"], "policy_hash": entry["policy_hash"],
            "decision": entry["decision"], "rule": entry["rule"], "path": entry["decision_path"]}
    rec = engine.get_record(did) if did else None
    if rec is None:
        # a gate refusal or lifecycle event: show what the log itself holds
        return {**base, "steps": [{"key": "Request", "state": "done" if entry["rule"] != "R01" else "failed",
                                   "text": payload.get("reason") or f"{entry['action']} recorded"}],
                "result": entry["decision"], "labels": [], "provenance": []}

    d: Decision = rec["decision"]
    meta, prop = rec["meta"], rec["proposal"]
    first = next((json.loads(e["payload_json"]) for e in reversed(audit.entries(engine.state, 1000))
                  if json.loads(e["payload_json"]).get("decision_id") == did and "inputs" in json.loads(e["payload_json"])), {})
    inputs = first.get("inputs", {})
    env, eff = d.envelope, d.effect
    steps = [{"key": "Request", "state": "done", "text": f"Signed by {d.agent} and verified (signature, fresh timestamp, new nonce)"}]
    if env:
        lim = [f"{k} {v}" for k, v in env.scope.items()]
        if env.max_rows is not None:
            lim.append(f"up to {env.max_rows} rows")
        if env.max_amount_minor is not None:
            lim.append(f"up to {_money(env.max_amount_minor)}")
        steps.append({"key": "Envelope", "state": "done",
                      "text": ("AI-generated limits from the user's request: " if env.source == "ai_from_instruction"
                               else "Policy default limits: ") + (", ".join(lim) or "none")})
    if eff:
        n = sum(len(v) for v in eff.rows.values())
        parts = [f"{n:,} rows" if n else "no rows"]
        if eff.amount_minor:
            parts.append(_money(eff.amount_minor))
        if eff.recipients:
            parts.append(f"{len(eff.recipients)} recipients")
        steps.append({"key": "Measured effect", "state": "done", "text": " · ".join(parts) + " (sandbox, real data untouched)"})
    steps.append({"key": "Policy", "state": "failed" if d.verdict == "BLOCK" else "done",
                  "text": f"Rule {d.rule}: {d.reason.split(' | ')[0]} (a request-level gate would say {d.baseline_verdict})"})
    appr = [dict(r) for r in engine.state.execute("SELECT user, action, ts FROM approvals WHERE decision_id=? ORDER BY id", (did,))]
    if d.verdict == "HOLD" or appr:
        have = [a["user"] for a in appr if a["action"] == "approve"]
        steps.append({"key": "Approval", "state": "done" if len(have) >= max(d.approvals_needed, 1) else "pending",
                      "text": (", ".join(h.title() for h in have) or "Nobody yet") + f" ({len(have)} of {max(d.approvals_needed, 1)})"})
    else:
        steps.append({"key": "Approval", "state": "skipped", "text": "Not required" if d.verdict == "ALLOW" else "Not available (blocked)"})
    seal_row = engine.state.execute("SELECT token_json, used FROM seals WHERE decision_id=?", (did,)).fetchone()
    if seal_row:
        tok = json.loads(seal_row["token_json"])
        steps.append({"key": "Seal", "state": "done", "text": f"{tok['effect_hash'][:6]}…{tok['effect_hash'][-4:]} bound to the measured effect"
                      + (" (consumed)" if seal_row["used"] else "")})
    else:
        steps.append({"key": "Seal", "state": "skipped", "text": "Not issued"})
    if d.status == "done":
        steps.append({"key": "Execution", "state": "done", "text": "Executed in one transaction; the real effect matched the seal"})
    elif d.status == "void":
        steps.append({"key": "Execution", "state": "failed", "text": f"Not executed: seal broken ({(d.drift or 'changed').replace('_', ' ')}). {d.reason.split(';')[0]}"})
    elif d.status == "blocked":
        steps.append({"key": "Execution", "state": "skipped", "text": "Not executed (blocked)"})
    else:
        steps.append({"key": "Execution", "state": "pending", "text": "Not executed yet"})
    return {**base, "decision_id": did, "headline": f"{d.agent} → {d.action}", "steps": steps,
            "result": {"done": "EXECUTED", "void": "VOIDED", "blocked": "BLOCKED", "pending": "WAITING", "approved": "APPROVED",
                       "shadow": "SANDBOXED", "rejected": "REJECTED", "allowed": "ALLOWED"}.get(d.status, d.status.upper()),
            "labels": eff.labels if eff else [], "provenance": eff.label_path if eff else [],
            "baseline": d.baseline_verdict, "ai_note": d.ai_reason, "inputs_present": bool(inputs)}
