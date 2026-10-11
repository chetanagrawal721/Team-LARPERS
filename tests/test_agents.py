"""Milestone 7.1: scripted agents that can only propose."""
import pathlib
import time

import pytest

from agents import scenarios, tools
from agents.run import main as run_main
from agents.scenarios import Context


@pytest.fixture
def ctx(client):
    return Context(client=client, wait_seconds=0)


def chats():
    from gateway.main import BUS
    return [e.data["text"] for _, e in BUS.history if e.type == "chat"]


def test_tool_signs_and_gateway_accepts(client):
    a = tools.Agent("refund-agent", client=client)
    d = a.lookup(customer="C-1042")
    assert d["rule"] not in ("R01", "R02") and d["verdict"] == "ALLOW"


def test_signature_matches_gateway_implementation():
    from gateway import verify
    body = {"agent": "x", "action": "y", "args": {"b": 1, "a": 2}, "nonce": "n", "ts": 1}
    assert tools.sign("k", body) == verify.sign("k", body)


def test_scenario_update_phone_runs(ctx):
    d = scenarios.run("bank-update-phone", ctx)
    assert d["verdict"] == "ALLOW" and d["status"] == "done"
    assert any("Updated 1 record" in t for t in chats())


def test_scenario_refund_blocks_with_safe_version(ctx):
    d = scenarios.run("bank-refund", ctx)
    assert d["verdict"] == "BLOCK" and d["rule"] == "R06" and d["safe_version"]
    assert any("Blocked (R06)" in t for t in chats())


def test_scenario_payee_goes_to_shadow(ctx):
    d = scenarios.run("bank-payee-poisoned", ctx)
    assert d["verdict"] == "HOLD" and d["status"] == "shadow" and d["rule"] == "R07"


def test_scenarios_in_other_domains(client):
    for dom, name in (("hospital", "hospital-report"), ("shop", "shop-relay"), ("shop", "shop-newsletter")):
        client.post(f"/domain/{dom}")
        d = scenarios.run(name, Context(client=client, wait_seconds=0))
        assert d["verdict"] in ("BLOCK", "ALLOW")
    client.post("/domain/bank")


def test_agent_handles_hold_by_polling(client):
    a = tools.Agent("ops-agent", client=client, wait_seconds=0.2, poll=0.05)
    d = a.propose("transfer", {"batch": "pending", "vendor": "V-05"}, on_behalf_of="rahul")
    assert d["verdict"] == "HOLD"
    h = {"X-User": "priya", "X-Token": "t-priya"}
    client.post("/approve", json={"decision_id": d["id"]}, headers=h)
    client.post(f"/execute/{d['id']}", headers=h)
    assert a.wait(d)["status"] == "done"


def test_gateway_down_gives_clear_error(monkeypatch, capsys):
    monkeypatch.setattr("agents.config.GATEWAY_URL", "http://127.0.0.1:9")
    assert run_main(["bank-update-phone"]) == 1
    assert "gateway unreachable" in capsys.readouterr().err


def test_agents_have_no_db_or_user_tokens():
    for f in pathlib.Path("agents").rglob("*.py"):
        t = f.read_text().lower()
        assert "sqlite" not in t and ".db" not in t and "user_token" not in t and "seal_key" not in t


def test_every_suite_agent_scenario_family_exists():
    assert {"bank-update-phone", "bank-refund", "bank-payee-poisoned", "bank-batch-transfer", "hospital-report",
            "shop-relay", "shop-newsletter"} <= set(scenarios.SCENARIOS)


def test_demo_endpoint_spawns_agent_process_without_secrets(client, monkeypatch):
    captured = {}

    class FakeProc:
        pid = 1

    def fake_popen(args, cwd, env):
        captured.update(args=args, env=env)
        return FakeProc()
    monkeypatch.setattr("gateway.main.subprocess.Popen", fake_popen)
    r = client.post("/demo/bank-refund").json()
    assert r["started"] == "bank-refund"
    assert "USER_TOKEN_PRIYA" not in captured["env"] and "GATEWAY_SEAL_KEY" not in captured["env"]
    assert any(k.startswith("AGENT_KEY_") for k in captured["env"])


def test_demo_chat_router(client, monkeypatch):
    monkeypatch.setattr("gateway.main.subprocess.Popen", lambda *a, **k: type("P", (), {"pid": 1})())
    assert client.post("/demo/chat", json={"text": "Refund C-1042's duplicate March charges"}).json()["started"] == "bank-refund"
    assert client.post("/demo/chat", json={"text": "make me a sandwich"}).json()["started"] is None


def test_events_bus_replays_history(client):
    from gateway.main import BUS
    from gateway.events import frame
    client.post("/chat", json={"from": "agent", "text": "hello"})
    i, ev = BUS.recent(1)[0]
    assert "event: chat" in frame(i, ev) and "hello" in frame(i, ev)
