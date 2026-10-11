"""End-to-end beats through the real API. Agents here are plain signed clients (agents.tools.Agent): the proposals are
made directly, so these tests exercise the gateway, the approvals and the audit trail without needing a language model."""
import subprocess

import pytest

from agents.tools import Agent
from gateway import audit, main
from gateway.engine import Engine

PRIYA = {"X-User": "priya", "X-Token": "t-priya"}
RAHUL = {"X-User": "rahul", "X-Token": "t-rahul"}
ANITA = {"X-User": "anita", "X-Token": "t-anita"}


def agent(client, name):
    return Agent(name, client=client, wait_seconds=0)


def test_beat1_ordinary_work_goes_straight_through(client):
    d = agent(client, "ops-agent").propose("update_contact", {"customer": "C-0007", "phone": "+91-9822000007"},
                                           intent="update one phone number", on_behalf_of="meera")
    assert d["verdict"] == "ALLOW" and d["status"] == "done"


def test_beats_2_and_3_block_then_safe_version(client):
    d = agent(client, "refund-agent").propose("refund", {"customer": "C-1042", "month": "March", "match": "batch"},
                                              intent="refund one customer", user_instruction="Refund C-1042's duplicate March charges")
    assert d["verdict"] == "BLOCK" and d["baseline_verdict"] == "ALLOW" and d["effect"]["amount_minor"] == 98_000_000
    out = client.post(f"/safe-version/{d['id']}", headers=PRIYA).json()
    assert out["status"] == "done" and out["effect"]["amount_minor"] == 640_000


def test_beat4_untrusted_source_goes_to_shadow_then_discard(client):
    d = agent(client, "ops-agent").propose("payee_change", {"vendor": "V-17", "new_account": "ICICI-0009083", "source": "inbox:E-9001"},
                                           on_behalf_of="priya")
    assert d["verdict"] == "HOLD" and d["rule"] == "R07" and d["status"] == "shadow"
    sid = d["shadow_session"]
    agent(client, "ops-agent").propose("transfer", {"batch": "pending", "vendor": "V-05"}, on_behalf_of="rahul")
    v = client.get(f"/shadow/{sid}").json()
    assert v["totals"]["steps"] == 2 and "V-17" in v["diff"]["vendors"]
    assert client.post(f"/discard/{sid}", headers=RAHUL).json()["status"] == "discarded"


def test_beat5_seal_breaks_when_the_data_changes(client):
    d = agent(client, "ops-agent").propose("transfer", {"batch": "pending"}, user_instruction="Pay the 40 pending vendor invoices",
                                           on_behalf_of="rahul")
    assert d["verdict"] == "HOLD" and d["tier"] == "T3"
    client.post("/approve", json={"decision_id": d["id"]}, headers=PRIYA)
    assert client.post("/approve", json={"decision_id": d["id"]}, headers=ANITA).json()["status"] == "approved"
    client.post("/demo/insert-invoices")
    out = client.post(f"/execute/{d['id']}", headers=PRIYA).json()
    assert out["verdict"] == "VOID" and out["drift"] == "effect_drift" and "40 -> 4000" in out["reason"]
    assert out["baseline_verdict"] == "ALLOW"


def test_beat6_and_7_other_domains(client):
    client.post("/domain/hospital")
    main.engine().require_human = False
    h = agent(client, "records-agent").propose("send_report", {"patient": "P-0001", "to": "dr.shah@punecare.example", "attachment": "batch_all"},
                                               user_instruction="Share Ramesh's report with Dr. Shah")
    assert h["verdict"] == "BLOCK" and h["safe_version"]["rows"] == {"disclosed": 1}
    client.post("/domain/shop")
    main.engine().require_human = False
    w = agent(client, "support-agent").propose("write_file", {"path": "shared/q3_customers.csv", "source": "customers"})
    assert w["status"] == "done"
    s = agent(client, "marketing-agent").propose("send_email", {"list": "agency", "file": "shared/q3_customers.csv", "subject": "Q3", "body": "Attached."})
    assert s["verdict"] == "BLOCK" and s["rule"] == "R05"
    client.post("/domain/bank")


def test_beat8_ai_off_gives_the_same_safety_with_fallback_path(client):
    client.post("/ai/toggle?enabled=false")
    d = agent(client, "refund-agent").propose("refund", {"customer": "C-1042", "month": "March", "match": "batch"},
                                              user_instruction="Refund C-1042's duplicate March charges")
    assert d["verdict"] == "BLOCK" and d["decision_path"] == "fallback"
    client.post("/ai/toggle?enabled=true")


def test_beat9_audit_tamper_detected(client):
    agent(client, "ops-agent").propose("update_contact", {"customer": "C-0007", "phone": "1"}, on_behalf_of="meera")
    assert client.post("/audit/verify").json()["ok"]
    main.engine().state.execute("UPDATE audit_log SET decision='BLOCK' WHERE seq=1")
    assert client.post("/audit/verify").json() == {"ok": False, "first_broken_seq": 1}


def test_restart_mid_demo_keeps_state_consistent(tmp_path):
    from tests.helpers import make_proposal
    e = Engine("bank", data_dir=tmp_path)
    e.propose(make_proposal("ops-agent", "update_contact", {"customer": "C-0007", "phone": "1"}))
    e.propose(make_proposal("refund-agent", "refund", {"customer": "C-1042", "month": "March", "match": "batch"}))
    e2 = Engine("bank", data_dir=tmp_path)           # the gateway process restarts
    assert audit.verify(e2.state)["ok"] and len(e2.list_decisions()) == 2
    c = e2.real_conn()
    assert c.execute("SELECT phone FROM customers WHERE id='C-0007'").fetchone()[0] == "1"


def test_demo_reset_restores_initial_state(client):
    agent(client, "ops-agent").propose("update_contact", {"customer": "C-0007", "phone": "1"}, on_behalf_of="meera")
    assert client.post("/demo/reset").json()["reset"] == ["bank", "hospital", "shop"]
    assert client.get("/actions").json() == []


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
