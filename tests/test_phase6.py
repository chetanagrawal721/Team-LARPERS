"""Milestones 6.1 (smallest safe version), 6.2 (Shadow Mode), 6.3 (replay + honeytoken freeze)."""
import json
import random

import pytest

from gateway import approvals, audit, outbox, replay, safe_version, shadow
from gateway.approvals import GateError
from gateway.policy_loader import Policy, load_users
from gateway.seed.common import db_hash
from tests.helpers import make_proposal

USERS = load_users()


def U(name):
    return {"id": name, **USERS[name]}


def propose(engine, agent, action, args, on_behalf_of="", **kw):
    return engine.propose(make_proposal(agent, action, args, on_behalf_of=on_behalf_of, **kw))


BROAD = {"customer": "C-1042", "month": "March", "match": "batch"}


# ---------------- 6.1 ----------------
def test_broad_refund_offers_three_refunds(engine):
    d = propose(engine, "refund-agent", "refund", BROAD)
    sv = d.safe_version
    assert d.verdict == "BLOCK" and sv and sv["verdict"] == "ALLOW"
    assert sv["rows"] == {"refunds": 3} and sv["amount_minor"] == 640000 and "Rs 6,400" in sv["description"]


def test_honeytoken_has_no_safe_version(engine):
    assert propose(engine, "ops-agent", "export_all_credentials", {}).safe_version is None


def test_accept_safe_version_reseals_and_executes(engine):
    d = propose(engine, "refund-agent", "refund", BROAD)
    nd = safe_version.accept(engine, U("priya"), d.id)
    assert nd.status == "done" and nd.verdict == "ALLOW"
    c = engine.real_conn()
    assert c.execute("SELECT COUNT(*), SUM(amount_minor) FROM refunds").fetchone() == (3, 640000)
    child = engine.state.execute("SELECT parent_id FROM decisions WHERE id=?", (nd.id,)).fetchone()
    assert child["parent_id"] == d.id
    tok = engine.state.execute("SELECT used FROM seals WHERE decision_id=?", (nd.id,)).fetchone()
    assert tok["used"] == 1


def test_accept_requires_authorised_non_requester(engine):
    d = propose(engine, "refund-agent", "refund", BROAD)
    with pytest.raises(GateError):
        safe_version.accept(engine, U("meera"), d.id)


def test_reduced_still_unsafe_not_offered(engine):
    raw = json.loads(json.dumps(engine.policy.raw))
    raw["envelopes"]["refund"]["max_amount"] = 1
    engine.policy = Policy(raw)
    assert propose(engine, "refund-agent", "refund", BROAD).safe_version is None


def test_no_split_suggestion_for_budget_hold(engine):
    from gateway import budgets
    c = engine.real_conn()
    for _ in range(50):
        budgets.check_and_charge_atomic(c, engine.policy, "refund-agent", "refund", 100000)
    d = propose(engine, "refund-agent", "refund", {"customer": "C-1042", "month": "March"})
    assert d.verdict == "HOLD" and d.rule == "R08" and d.safe_version is None


def test_batch_transfer_reduces_to_lower_tier(engine):
    d = propose(engine, "ops-agent", "transfer", {"batch": "pending"}, "rahul")
    sv = d.safe_version
    assert d.tier == "T3" and sv and sv["tier"] == "T2" and sv["rows"]["invoices"] == 10
    nd = safe_version.accept(engine, U("priya"), d.id)
    assert nd.status == "done"


# ---------------- 6.2 ----------------
UNTRUSTED = {"vendor": "V-17", "new_account": "ICICI-0009083", "source": "inbox:E-9001"}


def shadowed(engine):
    d = propose(engine, "ops-agent", "payee_change", UNTRUSTED, "priya")
    assert d.verdict == "HOLD" and d.rule == "R07" and d.shadow_session
    return d


def test_enter_shadow_real_unchanged(engine):
    before = db_hash(engine.real_path)
    d = shadowed(engine)
    for n in range(3):
        s = propose(engine, "ops-agent", "update_contact", {"customer": "C-0007", "phone": f"+91-{n}"}, "priya")
        assert s.status == "shadow" and s.verdict == "ALLOW" and s.shadow_session == d.shadow_session
    assert db_hash(engine.real_path) == before


def test_total_diff(engine):
    d = shadowed(engine)
    propose(engine, "ops-agent", "update_contact", {"customer": "C-0007", "phone": "+91-1"}, "priya")
    v = shadow.view(engine, d.shadow_session)
    assert v["totals"]["steps"] == 2 and "V-17" in v["diff"]["vendors"] and "C-0007" in v["diff"]["customers"]


def test_promote_ok(engine):
    d = shadowed(engine)
    propose(engine, "ops-agent", "update_contact", {"customer": "C-0007", "phone": "+91-1"}, "priya")
    out = shadow.promote(engine, U("rahul"), d.shadow_session)
    assert out["status"] == "promoted"
    c = engine.real_conn()
    assert c.execute("SELECT account FROM vendors WHERE id='V-17'").fetchone()[0] == "ICICI-0009083"
    assert engine.get_decision(d.id).status == "done"


def test_promote_with_real_drift_rolls_back(engine):
    d = shadowed(engine)
    c = engine.real_conn()
    c.execute("UPDATE vendors SET account='HDFC-CHANGED' WHERE id='V-17'")
    before = db_hash(engine.real_path)
    out = shadow.promote(engine, U("rahul"), d.shadow_session)
    assert out["status"] == "void" and out["drift"] == "state_drift"
    assert db_hash(engine.real_path) == before


def test_discard_leaves_real_untouched(engine):
    before = db_hash(engine.real_path)
    d = shadowed(engine)
    propose(engine, "ops-agent", "update_contact", {"customer": "C-0007", "phone": "+91-1"}, "priya")
    assert shadow.discard(engine, U("rahul"), d.shadow_session)["status"] == "discarded"
    assert db_hash(engine.real_path) == before
    assert not (engine.scratch / f"{d.shadow_session}.db").exists()
    assert engine.get_decision(d.id).status == "rejected"


def test_no_sandbox_emails_or_payments(engine):
    d = shadowed(engine)
    propose(engine, "ops-agent", "transfer", {"batch": "pending", "vendor": "V-05"}, "rahul")
    assert outbox.deliver_pending(engine) == 0
    c = engine.real_conn()
    assert c.execute("SELECT COUNT(*) FROM delivered_messages").fetchone()[0] == 0


def test_requester_cannot_promote(engine):
    d = shadowed(engine)
    with pytest.raises(GateError) as e:
        shadow.promote(engine, U("priya"), d.shadow_session)
    assert e.value.status == 403


def test_tier3_session_needs_two_promoters(engine):
    d = shadowed(engine)
    propose(engine, "ops-agent", "transfer", {"batch": "pending"}, "rahul")
    assert shadow.promote(engine, U("anita"), d.shadow_session)["status"] == "pending"
    assert shadow.promote(engine, U("rahul"), d.shadow_session)["status"] == "promoted"


def test_blocked_action_in_shadow_stays_blocked(engine):
    shadowed(engine)
    b = propose(engine, "ops-agent", "export_all_credentials", {})
    assert b.verdict == "BLOCK"


# ---------------- 6.3 ----------------
def entries_with_inputs(engine):
    out = []
    for e in audit.entries(engine.state):
        if "inputs" in json.loads(e["payload_json"]):
            out.append(e)
    return out


def test_replay_matches(engine):
    propose(engine, "ops-agent", "update_contact", {"customer": "C-0007", "phone": "1"})
    propose(engine, "refund-agent", "refund", BROAD)
    propose(engine, "ops-agent", "payee_change", UNTRUSTED, "priya")
    es = entries_with_inputs(engine)
    assert len(es) >= 3
    for e in es:
        r = replay.replay(engine, e["seq"])
        assert r["reproduced"] is True, r


def test_replay_uses_stored_policy_after_change(engine):
    propose(engine, "refund-agent", "refund", BROAD)
    seq = entries_with_inputs(engine)[0]["seq"]
    raw = json.loads(json.dumps(engine.policy.raw))
    raw["envelopes"]["refund"]["max_rows"] = 1000
    raw["envelopes"]["refund"]["max_amount"] = 10**9
    engine.policy = Policy(raw)
    engine._store_policy_version()
    assert replay.replay(engine, seq)["reproduced"] is True


def test_replay_refused_on_tampered_chain(engine):
    propose(engine, "ops-agent", "update_contact", {"customer": "C-0007", "phone": "1"})
    seq = entries_with_inputs(engine)[0]["seq"]
    engine.state.execute("UPDATE audit_log SET decision='BLOCK' WHERE seq=?", (seq,))
    with pytest.raises(GateError) as e:
        replay.replay(engine, seq)
    assert e.value.status == 409


def test_honeytoken_freeze_and_unfreeze(client):
    h = {"X-User": "priya", "X-Token": "t-priya"}
    r = client.post("/propose", json=make_proposal("ops-agent", "export_all_credentials", {})).json()
    assert r["verdict"] == "BLOCK" and r["rule"] == "R03"
    frozen = client.post("/propose", json=make_proposal("ops-agent", "lookup", {"customer": "C-0007"})).json()
    assert frozen["verdict"] == "BLOCK"
    assert client.post("/agents/ops-agent/unfreeze", headers={"X-User": "meera", "X-Token": "t-meera"}).status_code == 403
    assert client.post("/agents/ops-agent/unfreeze", headers=h).json()["frozen"] is False
    ok = client.post("/propose", json=make_proposal("ops-agent", "lookup", {"customer": "C-0007"})).json()
    assert ok["verdict"] == "ALLOW"


def test_replay_ten_random_entries(engine):
    rnd = random.Random(1)
    for i in range(12):
        propose(engine, "ops-agent", "update_contact", {"customer": f"C-10{rnd.randint(10, 60)}", "phone": str(i)})
    es = entries_with_inputs(engine)
    for e in rnd.sample(es, 10):
        assert replay.replay(engine, e["seq"])["reproduced"] is True
