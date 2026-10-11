"""Agents are signed clients that can only propose. (The live, model-driven agent is tested in test_llm_agent.py.)"""
import pathlib

from agents import tools
from gateway import verify


def test_tool_signs_and_gateway_accepts(client):
    a = tools.Agent("refund-agent", client=client)
    d = a.lookup(customer="C-1042")
    assert d["rule"] not in ("R01", "R02") and d["verdict"] == "ALLOW"


def test_signature_matches_gateway_implementation():
    body = {"agent": "x", "action": "y", "args": {"b": 1, "a": 2}, "nonce": "n", "ts": 1}
    assert tools.sign("k", body) == verify.sign("k", body)


def test_agent_handles_hold_by_polling(client):
    a = tools.Agent("ops-agent", client=client, wait_seconds=0.2, poll=0.05)
    d = a.propose("transfer", {"batch": "pending", "vendor": "V-05"}, on_behalf_of="rahul")
    assert d["verdict"] == "HOLD"
    h = {"X-User": "priya", "X-Token": "t-priya"}
    client.post("/approve", json={"decision_id": d["id"]}, headers=h)
    client.post(f"/execute/{d['id']}", headers=h)
    assert a.wait(d)["status"] == "done"


def test_agents_have_no_db_or_user_tokens():
    for f in pathlib.Path("agents").rglob("*"):
        if f.suffix in (".py", ".txt"):
            t = f.read_text().lower()
            assert "sqlite" not in t and ".db" not in t and "user_token" not in t and "seal_key" not in t, f


def test_nothing_in_the_project_is_scripted_any_more():
    assert not pathlib.Path("agents/scenarios.py").exists()
    main = pathlib.Path("gateway/main.py").read_text()
    assert "scenarios" not in main and '"/demo/{scenario}"' not in main
