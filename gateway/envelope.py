"""Expected-effect envelope and the deterministic request-vs-reality check (C2, C3). Pure functions, no DB writes."""
from .policy_loader import Policy
from .schemas import Effect, Envelope, EnvelopeCheck

# Scope keys an action is expected to carry, and how a scope key maps onto an affected row.
SCOPE_KEYS = {
    "refund": ["customer", "month"], "update_contact": ["customer"], "lookup": ["customer"],
    "payee_change": ["vendor"], "grant_role": ["target"], "transfer": [],
    "send_report": ["patient"], "delete_record": ["patient"], "write_file": [], "send_email": [],
}
REQUIRED_SCOPE = {"refund": ["customer"], "update_contact": ["customer"], "payee_change": ["vendor"],
                  "grant_role": ["target"], "send_report": ["patient"], "delete_record": ["patient"]}
SCOPE_ATTR = {"customer": "customer_id", "vendor": "vendor_id", "patient": "patient_id", "target": "subject"}
SCOPE_PK_TABLE = {"customer": "customers", "vendor": "vendors", "patient": "patients"}


def default_for(policy: Policy, action: str, args: dict) -> Envelope:
    """Envelope from policy defaults. A missing required scope key yields the strictest envelope (<= 1 row)."""
    scope = {k: args[k] for k in SCOPE_KEYS.get(action, []) if k in args}
    limits = policy.envelope_default(action)
    max_rows = limits["max_rows"]
    if any(k not in args for k in REQUIRED_SCOPE.get(action, [])):
        max_rows = 1 if max_rows is None else min(max_rows, 1)
    dests = list(policy.model.envelopes.get(action, {}).get("destinations", []))
    return Envelope(scope=scope, max_rows=max_rows, max_amount_minor=limits["max_amount_minor"],
                    allowed_destinations=dests, source="policy_default")


def check(effect: Effect, env: Envelope, policy: Policy) -> EnvelopeCheck:
    offending: dict[str, list[str]] = {}
    reasons: list[str] = []
    for table, pks in effect.rows.items():
        meta = effect.row_meta.get(table, {})
        for pk in pks:
            for key, want in env.scope.items():
                if key not in SCOPE_ATTR:
                    continue
                if SCOPE_PK_TABLE.get(key) == table:
                    got = pk
                elif SCOPE_ATTR[key] in meta.get(pk, {}):
                    got = meta[pk][SCOPE_ATTR[key]]
                else:
                    continue
                if got != want:
                    offending.setdefault(table, []).append(pk)
                    break
    n_out = sum(len(v) for v in offending.values())
    if n_out:
        scope_txt = ", ".join(f"{k}={v}" for k, v in env.scope.items() if k in SCOPE_ATTR)
        reasons.append(f"{n_out} affected rows are outside the requested scope ({scope_txt})")
    primary = policy.action_def(effect.action_type).get("primary_table")
    count = len(effect.rows.get(primary, [])) if primary else sum(len(v) for v in effect.rows.values())
    over_rows = 0
    if env.max_rows is not None and count > env.max_rows:
        over_rows = count - env.max_rows
        reasons.append(f"{count} rows affected; limit is {env.max_rows}")
        if not n_out and primary:
            offending[primary] = sorted(effect.rows[primary])[env.max_rows:]
    over_amount = 0
    if env.max_amount_minor is not None and effect.amount_minor > env.max_amount_minor:
        over_amount = effect.amount_minor - env.max_amount_minor
        reasons.append(f"amount {effect.amount_minor // 100} exceeds limit {env.max_amount_minor // 100}")
    bad_recipients: list[str] = []
    if env.allowed_destinations:
        outside = [d for d in effect.destinations if d not in env.allowed_destinations]
        if outside:
            bad_recipients = sorted(effect.recipients)
            reasons.append("destination(s) " + ", ".join(outside) + " not expected for this request")
    declared = effect.row_meta.get("recipients", {})
    stray = sorted(a for a, m in declared.items() if m.get("declared") and m.get("dest") != m["declared"])
    if stray:
        bad_recipients = sorted(set(bad_recipients) | set(stray))
        offending["recipients"] = stray
        reasons.append(f"{len(stray)} recipients are outside the list's declared audience")
    return EnvelopeCheck(inside=not reasons, offending_rows={t: sorted(v) for t, v in offending.items()},
                         offending_recipients=bad_recipients, over_amount=over_amount, over_rows=over_rows,
                         reasons=reasons)
