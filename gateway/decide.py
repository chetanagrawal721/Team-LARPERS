"""decide(): one pure function from decision inputs to a verdict (deterministic, replayable)."""
from . import rules
from .policy_loader import Policy

RANK = {"ALLOW": 0, "HOLD": 1, "BLOCK": 2}


def decide(inp: dict, policy: Policy) -> dict:
    """final = max(rule_decision, ai_escalation). The AI can only raise the verdict, never lower it."""
    bump = 1 if inp.get("intent_unverified") else 0
    tier = rules.tier_of(inp.get("effect"), policy, inp["action"], bump)
    fired: list[str] = []
    blocked = rules.block_rules(inp, policy)
    if blocked:
        verdict, rule, reason = "BLOCK", blocked[0], blocked[1]
        fired = [rule]
    else:
        holds = rules.hold_rules(inp, policy, tier)
        fired = [r for r, _ in holds]
        if holds:
            verdict, (rule, reason) = "HOLD", holds[0]
        elif inp.get("effect") is not None and inp.get("check") is not None:
            verdict, rule, reason = "ALLOW", "R12", f"inside what was asked, tier {tier}"
            fired = ["R12"]
        else:
            verdict, rule, reason = "BLOCK", "R99", "no rule matched (default deny)"
            fired = ["R99"]
    ai = inp.get("ai") or {}
    esc = ai.get("escalation", "NONE")
    if esc in RANK and RANK[esc] > RANK[verdict]:
        verdict, rule = esc, "R11"
        reason = "AI escalation: " + (ai.get("reason") or "flagged for review")
        fired = fired + ["R11"]
    approvals = rules.approvals_for(tier, inp.get("effect"), policy) if verdict == "HOLD" else 0
    if inp.get("effect") is None:
        path = "rules-only"
    elif ai.get("status") == "ok":
        path = "rules+ai"
    else:
        path = "fallback"
    return {"verdict": verdict, "rule": rule, "reason": reason, "rules_fired": fired, "tier": tier,
            "approvals_needed": approvals, "decision_path": path}


def baseline_verdict(inp: dict, policy: Policy) -> str:
    """What a typical request-level gate (mode B: allowlist + argument-bound approvals) would say."""
    if not inp.get("sig_ok", True) or not inp.get("known", True) or inp.get("honeytoken") or inp.get("frozen"):
        return "BLOCK"
    if not inp.get("permitted", True):
        return "BLOCK"
    if policy.is_protected(inp["action"]):
        return "HOLD"
    return "ALLOW"


def mode_decide(inp: dict, policy: Policy, mode: str) -> dict:
    """Ablation baselines used by the Attack Lab (same gateway, features switched off).
    A = allowlist + default deny + signature check. B = A + request-level approval of protected actions."""
    stripped = dict(inp, effect=None, check=None)
    blocked = rules.block_rules(stripped, policy)
    if blocked:
        return {"verdict": "BLOCK", "rule": blocked[0], "reason": blocked[1], "rules_fired": [blocked[0]],
                "tier": "T0", "approvals_needed": 0, "decision_path": "rules-only"}
    if mode == "B" and policy.is_protected(inp["action"]):
        return {"verdict": "HOLD", "rule": "R09", "reason": "protected action needs approval", "rules_fired": ["R09"],
                "tier": "T0", "approvals_needed": 1, "decision_path": "rules-only"}
    return {"verdict": "ALLOW", "rule": "R12", "reason": f"mode {mode}: request-level checks passed",
            "rules_fired": ["R12"], "tier": "T0", "approvals_needed": 0, "decision_path": "rules-only"}
