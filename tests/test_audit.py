from gateway import audit
from tests.helpers import make_proposal


def fill(engine, n=5):
    for i in range(n):
        audit.append(engine.state, 1000 + i, "a", "act", {"i": i}, "ALLOW", "R12", "rules-only", "h")


def test_chain_builds(engine):
    fill(engine)
    assert audit.verify(engine.state)["ok"]


def test_edit_detected(engine):
    fill(engine)
    engine.state.execute("UPDATE audit_log SET decision='BLOCK' WHERE seq=3")
    assert audit.verify(engine.state) == {"ok": False, "first_broken_seq": 3}


def test_deletion_detected(engine):
    fill(engine)
    engine.state.execute("DELETE FROM audit_log WHERE seq=2")
    assert audit.verify(engine.state) == {"ok": False, "first_broken_seq": 3}


def test_insertion_detected(engine):
    fill(engine)
    engine.state.execute(
        "INSERT INTO audit_log (seq, prev_hash, ts, agent, action, payload_json, decision, rule, decision_path,"
        " policy_hash, entry_hash) VALUES (3, 'x', 1, 'f', 'f', '{}', 'ALLOW', 'R', 'p', 'h', 'forged')"
        " ON CONFLICT(seq) DO UPDATE SET entry_hash='forged'")
    assert not audit.verify(engine.state)["ok"]


def test_refusals_logged_with_path(engine):
    p = make_proposal()
    p["args"] = {"tampered": True}
    engine.propose(p)
    e = audit.entries(engine.state)[0]
    assert e["decision"] == "BLOCK" and e["rule"] == "R01" and e["decision_path"]


def test_endpoint_verify(client):
    assert client.post("/audit/verify").json()["ok"] in (True, False)
