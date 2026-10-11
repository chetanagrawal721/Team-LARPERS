"""Milestone 9.2: the ten demo beats end to end through the real API, plus restart and authorship checks."""
import json
import subprocess

import pytest

from agents import scenarios
from agents.scenarios import Context
from gateway import ai, audit, main
from gateway.engine import Engine

PRIYA = {"X-User": "priya", "X-Token": "t-priya"}
RAHUL = {"X-User": "rahul", "X-Token": "t-rahul"}
ANITA = {"X-User": "anita", "X-Token": "t-anita"}


def decisions(client):
    return client.get("/actions?limit=50").json()


def test_beat1_ordinary_work_goes_straight_through(client):
    d = scenarios.run("bank-update-phone", Context(client=client, wait_seconds=0))
    assert d["verdict"] == "ALLOW" and d["status"] == "done"


def test_beats_2_and_3_block_then_safe_version(client):
    d = scenarios.run("bank-refund", Context(client=client, wait_seconds=0))
    assert d["verdict"] == "BLOCK" and d["baseline_verdict"] == "ALLOW" and d["effect"]["amount_minor"] == 98_000_000
    out = client.post(f"/safe-version/{d['id']}", headers=PRIYA).json()
    assert out["status"] == "done" and out["effect"]["amount_minor"] == 640_000


def test_beat4_shadow_then_discard(client):
    d = scenarios.run("bank-payee-poisoned", Context(client=client, wait_seconds=0))
    sid = d["shadow_session"]
    v = client.get(f"/shadow/{sid}").json()
    assert v["totals"]["steps"] == 3 and "V-17" in v["diff"]["vendors"]
    assert client.post(f"/discard/{sid}", headers=RAHUL).json()["status"] == "discarded"


def test_beat5_seal_breaks_when_the_data_changes(client):
    d = scenarios.run("bank-batch-transfer", Context(client=client, wait_seconds=0))
    assert d["verdict"] == "HOLD" and d["tier"] == "T3"
    client.post("/approve", json={"decision_id": d["id"]}, headers=PRIYA)
    assert client.post("/approve", json={"decision_id": d["id"]}, headers=ANITA).json()["status"] == "approved"
    client.post("/demo/insert-invoices")
    out = client.post(f"/execute/{d['id']}", headers=PRIYA).json()
    assert out["verdict"] == "VOID" and out["drift"] == "effect_drift" and "40 -> 4000" in out["reason"]
    assert out["baseline_verdict"] == "ALLOW"


def test_beat6_and_7_other_domains(client):
    client.post("/domain/hospital")
    h = scenarios.run("hospital-report", Context(client=client, wait_seconds=0))
    assert h["verdict"] == "BLOCK" and h["safe_version"]["rows"] == {"disclosed": 1}
    client.post("/domain/shop")
    s = scenarios.run("shop-relay", Context(client=client, wait_seconds=0))
    assert s["verdict"] == "BLOCK" and s["rule"] == "R05"


def test_beat8_ai_off_gives_the_same_safety_with_fallback_path(client):
    client.post("/ai/toggle?enabled=false")
    d = scenarios.run("bank-refund", Context(client=client, wait_seconds=0))
    assert d["verdict"] == "BLOCK" and d["decision_path"] == "fallback"
    client.post("/ai/toggle?enabled=true")


def test_beat9_audit_tamper_detected(client):
    scenarios.run("bank-update-phone", Context(client=client, wait_seconds=0))
    assert client.post("/audit/verify").json()["ok"]
    main.engine().state.execute("UPDATE audit_log SET decision='BLOCK' WHERE seq=1")
    assert client.post("/audit/verify").json() == {"ok": False, "first_broken_seq": 1}


def test_restart_mid_demo_keeps_state_consistent(tmp_path):
    e = Engine("bank", data_dir=tmp_path)
    from tests.helpers import make_proposal
    e.propose(make_proposal("ops-agent", "update_contact", {"customer": "C-0007", "phone": "1"}))
    e.propose(make_proposal("refund-agent", "refund", {"customer": "C-1042", "month": "March", "match": "batch"}))
    e2 = Engine("bank", data_dir=tmp_path)           # the gateway process restarts
    assert audit.verify(e2.state)["ok"] and len(e2.list_decisions()) == 2
    c = e2.real_conn()
    assert c.execute("SELECT phone FROM customers WHERE id='C-0007'").fetchone()[0] == "1"


def test_demo_reset_restores_initial_state(client, tmp_path):
    scenarios.run("bank-update-phone", Context(client=client, wait_seconds=0))
    assert client.post("/demo/reset").json()["reset"] == ["bank", "hospital", "shop"]
    assert decisions(client) == []


def test_authorship_only_the_four_team_ids():
    out = subprocess.run(["git", "log", "--format=%an"], capture_output=True, text=True)
    if out.returncode != 0 or not out.stdout.strip():
        pytest.skip("no git history")
    allowed = {"aryanketkar-15", "chetanagrawal721", "Kanak-Agrawal-3008", "atharvg44",
               "Atharv Gaikwad"}      # display name on the snapshot commit pushed by atharvg44
    assert set(out.stdout.split("\n")) - {""} <= allowed


def test_no_foreign_coauthor_trailers():
    out = subprocess.run(["git", "log", "--format=%B"], capture_output=True, text=True).stdout.lower()
    assert "co-authored-by" not in out and "generated with" not in out
