"""Smallest safe version (S1): the minimal change to the *resolved effect* that makes the decision safer.
Deterministic, no AI. Never offered for hard blocks, and never as a split into several actions (budget evasion)."""
import time

from . import resolvers
from .resolver import ResolverError
from .schemas import Decision, Envelope, Proposal

OFFER_FOR = {"R05", "R06", "R10"}          # everything else (R01-R04, R07-R09, R99) has nothing to reduce safely
RANK = {"ALLOW": 0, "HOLD": 1, "BLOCK": 2}
TIER_RANK = {"T0": 0, "T1": 1, "T2": 2, "T3": 3}


def describe(effect) -> str:
    primary = max(effect.rows, key=lambda t: len(effect.rows[t])) if effect.rows else None
    n = len(effect.rows[primary]) if primary else 0
    noun = (primary or "rows").rstrip("s")
    amt = f", Rs {effect.amount_minor // 100:,}" if effect.amount_minor else ""
    return f"{n} {noun}{'s' if n != 1 else ''}{amt}" if n else f"{len(effect.recipients)} recipient(s){amt}"


def compute(engine, p: Proposal, d: Decision, env: Envelope) -> dict | None:
    if d.verdict == "ALLOW" or d.rule not in OFFER_FOR or d.effect is None:
        return None
    if "SECRET" in d.effect.labels or d.rule in ("R01", "R02", "R03", "R04"):
        return None
    try:
        res = resolvers.get(engine.domain, p.action)
        new_args = res.reduce(dict(p.args), d.effect, d.envelope_check, env)
    except ResolverError:
        return None
    if not new_args or new_args == p.args:
        return None
    p2 = Proposal(agent=p.agent, action=p.action, args=new_args, intent="", user_instruction=p.user_instruction,
                  on_behalf_of=p.on_behalf_of, nonce="safe-version", ts=int(time.time()), sig="-")
    nd = engine._analyse(p2, p2.model_dump(), dry=True, env_override=env)
    if nd is None or nd.effect is None:
        return None
    better = RANK[nd.verdict] < RANK[d.verdict] or (
        nd.verdict == d.verdict == "HOLD" and TIER_RANK[nd.tier] < TIER_RANK[d.tier])
    if not better:
        return None
    return {"description": describe(nd.effect), "args": new_args, "verdict": nd.verdict, "rule": nd.rule,
            "tier": nd.tier, "amount_minor": nd.effect.amount_minor,
            "rows": {t: len(v) for t, v in nd.effect.rows.items()}, "recipients": nd.effect.recipients,
            "original_rows": {t: len(v) for t, v in d.effect.rows.items()}}


def accept(engine, user: dict, decision_id: str) -> Decision:
    """Run the reduced action through the full gate as a new decision, seal it and execute it."""
    from . import approvals
    from .approvals import GateError
    with engine.lock:
        rec = engine.get_record(decision_id)
        if not rec:
            raise GateError(404, "no such decision")
        d: Decision = rec["decision"]
        if not d.safe_version:
            raise GateError(409, "no safe version available for this decision")
        if not user.get("can_approve"):
            raise GateError(403, "user is not authorised to accept a safe version")
        if user["id"] == rec["requester"]:
            raise GateError(403, "requesters cannot approve their own requests")
        if d.status in ("done", "rejected", "void"):
            raise GateError(409, f"decision is {d.status}")
        p = rec["proposal"]
        p2 = dict(p, args=d.safe_version["args"], nonce=f"sv-{d.id}", ts=int(time.time()), sig="-", intent="")
        nd = engine._analyse(Proposal(**p2), p2, parent_id=d.id, accepted_by=user["id"])
        if nd.verdict == "BLOCK":
            raise GateError(409, f"safe version was not acceptable: {nd.reason}")
        if nd.verdict == "HOLD":
            nd = approvals.approve(engine, user, nd.id, note=f"accepted safe version of {d.id}")
            if nd.status == "approved":
                nd = engine.execute(nd.id)
        if d.status == "pending":
            d.status = "rejected"
        d.reason += f" | replaced by safe version {nd.id}"
        engine.save_decision(d)
        return nd
