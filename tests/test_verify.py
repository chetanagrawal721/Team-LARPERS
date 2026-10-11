import time

from gateway import audit
from tests.helpers import make_proposal


def test_valid_signed_request_passes_r01(engine):
    d = engine.propose(make_proposal(action="lookup", args={"customer": "C-1042"}))
    assert d.rule not in ("R01", "R02")


def test_tampered_argument_blocked(engine):
    p = make_proposal(action="lookup", args={"customer": "C-1042"})
    p["args"]["customer"] = "C-9999"
    d = engine.propose(p)
    assert d.verdict == "BLOCK" and d.rule == "R01"


def test_wrong_key_blocked(engine):
    d = engine.propose(make_proposal(key="k-ops"))
    assert d.verdict == "BLOCK" and d.rule == "R01"


def test_replayed_nonce_blocked(engine):
    p = make_proposal()
    assert engine.propose(dict(p)).rule != "R01"
    d = engine.propose(dict(p))
    assert d.rule == "R01" and "replay" in d.reason


def test_stale_and_future_timestamp(engine):
    assert "stale" in engine.propose(make_proposal(ts=int(time.time()) - 300)).reason
    assert engine.propose(make_proposal(ts=int(time.time()) + 300)).rule == "R01"


def test_missing_signature_422(client):
    p = make_proposal()
    p.pop("sig")
    assert client.post("/propose", json=p).status_code == 422


def test_unknown_agent_r02(engine):
    d = engine.propose(make_proposal(agent="ghost"))
    assert d.verdict == "BLOCK" and d.rule == "R02"


def test_secrets_not_tracked():
    import subprocess
    out = subprocess.run(["git", "ls-files", ".env"], capture_output=True, text=True).stdout
    assert out.strip() == ""


def test_rejections_are_logged(engine):
    p = make_proposal()
    p["args"] = {"x": 1}
    engine.propose(p)
    assert any(e["rule"] == "R01" for e in audit.entries(engine.state))
