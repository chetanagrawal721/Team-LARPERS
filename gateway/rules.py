"""Deterministic rules R01-R12, R99 and reversibility tiers (Final Solution section 7). Pure functions over plain dicts."""
from . import labels as labels_mod
from .policy_loader import Policy

TIER_TABLE = {"snapshot": ["T0", "T1", "T2"], "compensating": ["T1", "T2", "T3"], "none": ["T2", "T3", "T3"]}
TIERS = ["T0", "T1", "T2", "T3"]
SENSITIVE_DESTINATIONS = {"payment_rail", "external_email"}


def tier_of(effect: dict | None, policy: Policy, action: str, bump: int = 0) -> str:
    """Tier from reversibility x blast radius. No measurable effect -> T0."""
    if not effect:
        return "T0"
    rows = effect.get("rows", {})
    primary = policy.action_def(action).get("primary_table")
    count = len(rows.get(primary, [])) if primary and primary in rows else sum(len(v) for v in rows.values())
    count = max(count, len(effect.get("recipients", [])))
    if count == 0 and not effect.get("amount_minor"):
        return TIERS[min(bump, 3)]
    size = effect.get("table_sizes", {}).get(primary, 0) if primary else 0
    big = count > 1000 or (size > 0 and count / size > 0.2)
    col = 2 if big else (1 if count > 10 else 0)
    tier = TIER_TABLE.get(effect.get("reversible", "snapshot"), TIER_TABLE["none"])[col]
    for ov in policy.model.tier_overrides:
        if ov.get("action") != action:
            continue
        lbls = set(effect.get("labels", [])) - {"UNTRUSTED"}
        if "labels_subset" in ov and not lbls <= set(ov["labels_subset"]):
            continue
        if "destinations_only" in ov and not set(effect.get("destinations", [])) <= set(ov["destinations_only"]):
            continue
        if TIERS.index(ov["tier"]) < TIERS.index(tier):
            tier = ov["tier"]
    return TIERS[min(TIERS.index(tier) + bump, 3)]


def approvals_for(tier: str, effect: dict | None, policy: Policy) -> int:
    n = 2 if tier == "T3" else 1
    threshold = policy.model.tiers.get("two_approvers_above_amount")
    if effect and threshold and effect.get("amount_minor", 0) >= int(threshold) * 100:
        n = 2
    return n


def block_rules(inp: dict, policy: Policy) -> tuple[str, str] | None:
    """First BLOCK among R01-R06 (in order), or None."""
    if not inp.get("sig_ok", True):
        return "R01", "invalid signature, nonce or timestamp"
    eff = inp.get("effect")
    unknown = labels_mod.unknown_destinations(policy, eff.get("destinations", [])) if eff else []
    if not inp.get("known", True) or unknown:
        what = f"unknown destination {unknown[0]}" if unknown else "unknown agent or action"
        return "R02", what + " (default deny)"
    if inp.get("honeytoken") or inp.get("self_change") or inp.get("frozen"):
        why = "honeytoken action" if inp.get("honeytoken") else (
            "agent attempted to change its own permissions" if inp.get("self_change") else "agent is frozen")
        return "R03", why
    if not inp.get("permitted", True):
        return "R04", "outside effective permissions (agent and acting human)"
    if eff:
        bad = labels_mod.uncleared_destinations(policy, eff.get("labels", []), eff.get("destinations", []))
        if bad:
            top = labels_mod.max_level(eff.get("labels", []))
            return "R05", f"{top} data would reach {', '.join(bad)}, which is not cleared for it"
    chk = inp.get("check")
    if chk and not chk.get("inside", True):
        return "R06", "effect is outside what was asked: " + "; ".join(chk.get("reasons", []))
    if inp.get("noop"):
        return "R99", "no records matched this request, so there is nothing to do"
    return None


def hold_rules(inp: dict, policy: Policy, tier: str) -> list[tuple[str, str]]:
    """All HOLD rules that apply, strongest first: R07, R08, R09, R10."""
    out: list[tuple[str, str]] = []
    eff = inp.get("effect") or {}
    action = inp["action"]
    protected = policy.is_protected(action)
    if "UNTRUSTED" in eff.get("labels", []) and (protected or set(eff.get("destinations", [])) & SENSITIVE_DESTINATIONS):
        out.append(("R07", "action is built from UNTRUSTED data"))
    if inp.get("budget_exceeded"):
        out.append(("R08", "cumulative budget would be exceeded"))
    if protected:
        out.append(("R09", f"{action} is a protected class of action"))
    if tier in ("T2", "T3"):
        out.append(("R10", f"tier {tier}: human approval required"))
    return out
