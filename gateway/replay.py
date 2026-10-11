"""Replayable decisions (S5): re-evaluate a past decision from its stored inputs and stored policy version."""
import json

from . import audit
from .approvals import GateError
from .decide import decide
from .policy_loader import Policy


def replay(engine, seq: int) -> dict:
    chain = audit.verify(engine.state)
    if not chain["ok"]:
        raise GateError(409, f"audit chain is broken at entry {chain['first_broken_seq']}; replay refused")
    e = audit.get(engine.state, seq)
    if not e:
        raise GateError(404, "no such audit entry")
    payload = json.loads(e["payload_json"])
    inputs = payload.get("inputs")
    if inputs is None:
        return {"seq": seq, "reproduced": None, "stored": {"verdict": e["decision"], "rule": e["rule"]},
                "note": "this entry is a gate refusal or lifecycle event; there are no decision inputs to re-evaluate"}
    row = engine.state.execute("SELECT policy_json FROM policy_versions WHERE hash=?", (e["policy_hash"],)).fetchone()
    if not row:
        raise GateError(409, "stored policy version is missing")
    out = decide(inputs, Policy(json.loads(row["policy_json"])))
    if payload.get("requeue") and out["verdict"] == "ALLOW":
        out.update(verdict="HOLD", rule="R10")
    ok = out["verdict"] == e["decision"] and out["rule"] == e["rule"]
    return {"seq": seq, "reproduced": ok, "stored": {"verdict": e["decision"], "rule": e["rule"]},
            "replayed": {"verdict": out["verdict"], "rule": out["rule"], "reason": out["reason"]},
            "policy_hash": e["policy_hash"]}
