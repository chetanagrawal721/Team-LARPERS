import copy

import pytest

from gateway import policy_loader
from gateway.decide import decide
from tests.helpers import make_proposal


def propose(engine, agent, action, args, on_behalf_of="", user_instruction="", intent=""):
    return engine.propose(make_proposal(agent, action, args, on_behalf_of=on_behalf_of,
                                        user_instruction=user_instruction, intent=intent))


def test_phone_update_allowed(engine):
    d = propose(engine, "ops-agent", "update_contact", {"customer": "C-0007", "phone": "+91-9800000007"})
    assert d.verdict == "ALLOW" and d.rule == "R12" and d.baseline_verdict == "ALLOW"


def test_broad_refund_blocked_baseline_allows(engine):
    d = propose(engine, "refund-agent", "refund", {"customer": "C-1042", "month": "March", "match": "batch"})
    assert d.verdict == "BLOCK" and d.rule == "R06" and d.baseline_verdict == "ALLOW"
    assert not d.envelope_check.inside


def test_single_customer_refund_allowed(engine):
    d = propose(engine, "refund-agent", "refund", {"customer": "C-1042", "month": "March"})
    assert d.verdict == "ALLOW" and d.tier == "T1"


def test_pii_to_external_blocked_r05(engine):
    inp = {"agent": "a", "action": "send_email", "sig_ok": True, "known": True, "permitted": True,
           "effect": {"labels": ["PII"], "destinations": ["external_email"], "rows": {}, "recipients": ["x@y.z"]},
           "check": {"inside": True, "reasons": []}, "ai": {}}
    assert decide(inp, engine.policy)["rule"] == "R05"


def test_untrusted_payee_change_hold_r07(engine):
    d = propose(engine, "ops-agent", "payee_change",
                {"vendor": "V-17", "new_account": "ICICI-0009083", "source": "inbox:E-9001"})
    assert d.verdict == "HOLD" and d.rule == "R07" and "R09" in d.rules_fired


def test_verified_form_payee_change_hold_r09(engine):
    d = propose(engine, "ops-agent", "payee_change",
                {"vendor": "V-17", "new_account": "HDFC-0004411", "source": "form:F-100"})
    assert d.verdict == "HOLD" and d.rule == "R09"


def test_protected_grant_role_hold_r09(engine):
    d = propose(engine, "ops-agent", "grant_role", {"target": "meera", "role": "ops_officer"}, on_behalf_of="rahul")
    assert d.verdict == "HOLD" and d.rule == "R09"


def test_self_permission_change_blocked_r03(engine):
    d = propose(engine, "ops-agent", "grant_role", {"target": "ops-agent", "role": "admin"}, on_behalf_of="rahul")
    assert d.verdict == "BLOCK" and d.rule == "R03"


def test_honeytoken_blocks_and_freezes(engine):
    d = propose(engine, "ops-agent", "export_all_credentials", {})
    assert d.verdict == "BLOCK" and d.rule == "R03" and engine.is_frozen("ops-agent")
    d2 = propose(engine, "ops-agent", "lookup", {"customer": "C-0007"})
    assert d2.verdict == "BLOCK" and d2.rule == "R03"


def test_tier_t3_needs_two_approvers(engine):
    d = propose(engine, "ops-agent", "transfer", {"batch": "pending"}, on_behalf_of="rahul")
    assert d.verdict == "HOLD" and d.rule == "R10" and d.tier == "T3" and d.approvals_needed == 2


def test_confused_deputy_blocked_r04(engine):
    d = propose(engine, "ops-agent", "transfer", {"batch": "pending"}, on_behalf_of="priya")
    assert d.verdict == "BLOCK" and d.rule == "R04"


def test_default_deny_r99(engine):
    inp = {"agent": "a", "action": "lookup", "sig_ok": True, "known": True, "permitted": True,
           "effect": {"rows": {}, "labels": [], "destinations": []}, "check": None, "ai": {}}
    out = decide(inp, engine.policy)
    assert out["verdict"] == "BLOCK" and out["rule"] == "R99"


def test_ai_can_only_escalate(engine):
    base = {"agent": "a", "action": "payee_change", "sig_ok": True, "known": True, "permitted": True,
            "effect": {"rows": {}, "labels": [], "destinations": []}, "check": {"inside": True, "reasons": []}}
    assert decide({**base, "ai": {"escalation": "NONE", "status": "ok"}}, engine.policy)["verdict"] == "HOLD"
    low = decide({**base, "ai": {"escalation": "ALLOW", "status": "ok"}}, engine.policy)
    assert low["verdict"] == "HOLD"
    base["action"] = "lookup"
    up = decide({**base, "ai": {"escalation": "HOLD", "status": "ok", "reason": "mismatch"}}, engine.policy)
    assert up["verdict"] == "HOLD" and up["rule"] == "R11" and up["decision_path"] == "rules+ai"


def test_decide_is_deterministic(engine):
    inp = {"agent": "a", "action": "lookup", "sig_ok": True, "known": True, "permitted": True,
           "effect": {"rows": {}, "labels": [], "destinations": []}, "check": {"inside": True, "reasons": []}, "ai": {}}
    assert decide(copy.deepcopy(inp), engine.policy) == decide(copy.deepcopy(inp), engine.policy)


def test_every_decision_logged_with_rule_and_path(engine):
    from gateway import audit
    propose(engine, "refund-agent", "refund", {"customer": "C-1042", "month": "March", "match": "batch"})
    e = audit.entries(engine.state)[0]
    assert e["rule"] == "R06" and e["decision_path"] == "fallback"
    assert audit.verify(engine.state)["ok"]


def test_invalid_args_blocked_not_crashed(engine):
    d = propose(engine, "refund-agent", "refund", {"customer": "C-1' OR 1=1 --", "month": "March"})
    assert d.verdict == "BLOCK"
