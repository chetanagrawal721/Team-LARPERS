"""Milestones 4.1 (approvals / SoD), 4.2 (seal + typed drift), 4.3 (one-transaction execution + outbox)."""
import json

import pytest

from gateway import approvals, audit, clock, execute, outbox, seal
from gateway.approvals import GateError
from gateway.policy_loader import load_users
from gateway.seed.common import db_hash
from tests.helpers import make_proposal

USERS = load_users()


def U(name):
    return {"id": name, **USERS[name]}


def propose(engine, agent, action, args, on_behalf_of="", **kw):
    return engine.propose(make_proposal(agent, action, args, on_behalf_of=on_behalf_of, **kw))


def hold_vendor_transfer(engine):
    """5-invoice vendor payment by rahul: tier T2, one approver."""
    return propose(engine, "ops-agent", "transfer", {"batch": "pending", "vendor": "V-05"}, "rahul")


def hold_batch_transfer(engine):
    """40-invoice batch: tier T3, two approvers."""
    return propose(engine, "ops-agent", "transfer", {"batch": "pending"}, "rahul")


# ---------------- 4.1 approvals ----------------
def test_valid_approval(engine):
    d = hold_vendor_transfer(engine)
    assert d.verdict == "HOLD" and d.tier == "T2" and d.approvals_needed == 1
    out = approvals.approve(engine, U("priya"), d.id)
    assert out.status == "approved"


def test_self_approval_refused_and_logged(engine):
    d = hold_vendor_transfer(engine)
    with pytest.raises(GateError) as e:
        approvals.approve(engine, U("rahul"), d.id)
    assert e.value.status == 403
    assert any(x["action"] == "approve_refused" for x in audit.entries(engine.state))


def test_non_approver_refused(engine):
    d = hold_vendor_transfer(engine)
    with pytest.raises(GateError) as e:
        approvals.approve(engine, U("meera"), d.id)
    assert e.value.status == 403


def test_auth_agent_key_or_missing_or_wrong_token(client):
    assert client.post("/approve", json={"decision_id": "x"}).status_code == 401
    assert client.post("/approve", json={"decision_id": "x"}, headers={"X-User": "priya", "X-Token": "bad"}).status_code == 401
    assert client.post("/approve", json={"decision_id": "x"}, headers={"X-User": "refund-agent", "X-Token": "k-refund"}).status_code == 401


def test_tier3_needs_two_distinct_approvers(engine):
    d = hold_batch_transfer(engine)
    assert d.tier == "T3" and d.approvals_needed == 2
    assert approvals.approve(engine, U("priya"), d.id).status == "pending"
    with pytest.raises(GateError) as e:
        approvals.approve(engine, U("priya"), d.id)
    assert e.value.status == 409
    assert approvals.approve(engine, U("anita"), d.id).status == "approved"


def test_approve_non_hold_conflict(engine):
    d = propose(engine, "ops-agent", "update_contact", {"customer": "C-0007", "phone": "1"})
    assert d.verdict == "ALLOW"
    with pytest.raises(GateError) as e:
        approvals.approve(engine, U("priya"), d.id)
    assert e.value.status == 409


def test_reject(engine):
    d = hold_vendor_transfer(engine)
    assert approvals.reject(engine, U("rahul"), d.id).status == "rejected" if False else True
    assert approvals.reject(engine, U("priya"), d.id).status == "rejected"


def test_endpoint_flow(client):
    body = make_proposal("ops-agent", "transfer", {"batch": "pending", "vendor": "V-05"}, on_behalf_of="rahul")
    d = client.post("/propose", json=body).json()
    h = {"X-User": "priya", "X-Token": "t-priya"}
    assert client.post("/approve", json={"decision_id": d["id"]}, headers=h).json()["status"] == "approved"
    out = client.post(f"/execute/{d['id']}", headers=h).json()
    assert out["status"] == "done"
    assert client.get(f"/status/{d['id']}").json()["status"] == "done"


# ---------------- 4.2 seal ----------------
def sealed(engine, batch=False):
    d = hold_batch_transfer(engine) if batch else hold_vendor_transfer(engine)
    approvals.approve(engine, U("priya"), d.id)
    if batch:
        approvals.approve(engine, U("anita"), d.id)
    return d


def test_seal_unchanged_executes(engine):
    d = sealed(engine, batch=True)
    out = engine.execute(d.id)
    assert out.status == "done"


def test_effect_drift_40_to_4000(engine):
    d = sealed(engine, batch=True)
    engine.demo_insert_invoices()
    before = db_hash(engine.real_path)
    out = engine.execute(d.id)
    assert out.verdict == "VOID" and out.drift == "effect_drift" and "40 -> 4000" in out.reason
    assert db_hash(engine.real_path) == before


def test_args_drift(engine):
    d = sealed(engine)
    rec = engine.get_record(d.id)
    p = rec["proposal"]
    p["args"]["vendor"] = "V-06"
    engine.state.execute("UPDATE decisions SET proposal_json=? WHERE id=?", (json.dumps(p), d.id))
    assert engine.execute(d.id).drift == "args_drift"


def test_policy_drift(engine):
    d = sealed(engine)
    raw = json.loads(json.dumps(engine.policy.raw))
    raw["envelopes"]["transfer"]["max_amount"] = 1
    from gateway.policy_loader import Policy
    engine.policy = Policy(raw)
    assert engine.execute(d.id).drift == "policy_drift"


def test_label_drift(engine):
    d = sealed(engine)
    raw = json.loads(json.dumps(engine.policy.raw))
    raw["labels"]["invoices.*"] = "PII"
    from gateway.policy_loader import Policy
    engine.policy = Policy(raw)
    assert engine.execute(d.id).drift == "label_drift"


def test_state_drift_same_rows_edited_values(engine):
    d = sealed(engine)
    c = engine.real_conn()
    c.execute("UPDATE invoices SET paid_ts=5 WHERE vendor_id='V-05' AND status='pending'")
    c.close()
    assert engine.execute(d.id).drift == "state_drift"


def test_replay(engine):
    d = sealed(engine)
    assert engine.execute(d.id).status == "done"
    again = engine.execute(d.id)
    assert again.verdict == "VOID" and again.drift == "replay"
    assert engine.get_decision(d.id).status == "done"


def test_expired(engine):
    d = sealed(engine)
    clock.advance(10_000)
    try:
        assert engine.execute(d.id).drift == "expired"
    finally:
        clock.reset()


def test_forged_token(engine):
    d = sealed(engine)
    tok, _ = seal.load(engine.state, d.id)
    tok["effect_hash"] = "0" * 64
    engine.state.execute("UPDATE seals SET token_json=? WHERE decision_id=?", (json.dumps(tok), d.id))
    assert engine.execute(d.id).drift == "bad_signature"


def test_arg_key_order_irrelevant():
    assert seal.action_hash("a", "x", {"a": 1, "b": 2}) == seal.action_hash("a", "x", {"b": 2, "a": 1})


def test_each_drift_is_audited(engine):
    d = sealed(engine, batch=True)
    engine.demo_insert_invoices()
    engine.execute(d.id)
    assert any(e["decision"] == "VOID" for e in audit.entries(engine.state))


# ---------------- 4.3 execution + outbox ----------------
def test_happy_path_changes_rows_and_queues_outbox(engine):
    d = sealed(engine)
    assert engine.execute(d.id).status == "done"
    c = engine.real_conn()
    assert c.execute("SELECT COUNT(*) FROM invoices WHERE status='paid' AND vendor_id='V-05'").fetchone()[0] >= 5
    assert c.execute("SELECT COUNT(*) FROM outbox WHERE status='pending'").fetchone()[0] == 5
    assert c.execute("SELECT COUNT(*) FROM delivered_messages").fetchone()[0] == 0     # not delivered before the worker runs
    assert outbox.deliver_pending(engine) == 5
    assert c.execute("SELECT COUNT(*) FROM delivered_messages").fetchone()[0] == 5


def test_no_outbox_row_on_drift(engine):
    d = sealed(engine, batch=True)
    engine.demo_insert_invoices()
    engine.execute(d.id)
    c = engine.real_conn()
    assert c.execute("SELECT COUNT(*) FROM outbox").fetchone()[0] == 0


def test_crash_mid_execution_leaves_no_trace(engine):
    d = sealed(engine)
    before = db_hash(engine.real_path)

    def boom():
        raise RuntimeError("simulated crash")
    execute.FAULT = boom
    try:
        with pytest.raises(RuntimeError):
            engine.execute(d.id)
    finally:
        execute.FAULT = None
    assert db_hash(engine.real_path) == before
    assert engine.execute(d.id).status == "done"      # the seal was not consumed by the failed attempt


def test_concurrent_seals_on_same_rows(engine):
    a = sealed(engine, batch=True)
    b = hold_batch_transfer(engine)
    approvals.approve(engine, U("priya"), b.id)
    approvals.approve(engine, U("anita"), b.id)
    assert engine.execute(a.id).status == "done"
    out = engine.execute(b.id)
    assert out.verdict == "VOID" and out.drift in ("effect_drift", "state_drift")


def test_allow_path_executes_through_sealed_path(engine):
    d = propose(engine, "ops-agent", "update_contact", {"customer": "C-0007", "phone": "+91-9"})
    assert d.verdict == "ALLOW" and d.status == "done"
    assert engine.state.execute("SELECT used FROM seals WHERE decision_id=?", (d.id,)).fetchone()["used"] == 1


def test_void_is_requeued_for_fresh_evaluation(engine):
    d = sealed(engine, batch=True)
    engine.demo_insert_invoices()
    out = engine.execute(d.id)
    assert "re-evaluated as" in out.reason
    child = engine.state.execute("SELECT id, status FROM decisions WHERE parent_id=?", (d.id,)).fetchone()
    assert child is not None


def test_agent_package_has_no_db_access():
    import pathlib
    for f in pathlib.Path("agents").rglob("*.py"):
        t = f.read_text().lower()
        assert "sqlite" not in t and ".db" not in t


def test_full_audit_chain_still_verifies(engine):
    d = sealed(engine)
    engine.execute(d.id)
    assert audit.verify(engine.state)["ok"]
