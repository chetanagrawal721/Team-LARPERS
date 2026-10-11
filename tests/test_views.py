"""Read-only views behind the redesigned screens: organisations, policy, agents, approval sheet, evidence trail."""
from tests.helpers import make_proposal

PRIYA = {"X-User": "priya", "X-Token": "t-priya"}
ANITA = {"X-User": "anita", "X-Token": "t-anita"}


def test_orgs_lists_every_organisation_with_a_policy_version(client):
    o = client.get("/orgs").json()
    assert [x["domain"] for x in o] == ["bank", "hospital", "shop"]
    assert all(x["version"] >= 1 and len(x["hash"]) == 64 for x in o) and sum(x["current"] for x in o) == 1


def test_policy_view_has_yaml_and_key_facts(client):
    p = client.get("/policy").json()
    assert p["org"] == "Sahyadri Bank" and "refund-agent" in p["yaml"] and p["counts"]["agents"] == 4
    assert p["limits"]["envelopes"]["refund"]["max_rows"] == 5 and p["labels"]["labels"]["customers.phone"] == "PII"
    assert client.get("/policy?domain=hospital").json()["org"] == "Pune Care Hospital"


def test_agents_view_reflects_freeze_and_budget(client):
    client.post("/propose", json=make_proposal("ops-agent", "export_all_credentials", {}))
    rows = {(a["domain"], a["agent"]): a for a in client.get("/agents").json()}
    assert rows[("bank", "ops-agent")]["status"] == "FROZEN" and rows[("bank", "refund-agent")]["status"] == "ACTIVE"
    assert ("hospital", "records-agent") in rows and ("shop", "marketing-agent") in rows


def test_sheet_shows_requester_and_expiry(client):
    d = client.post("/propose", json=make_proposal("ops-agent", "transfer", {"batch": "pending", "vendor": "V-05"}, on_behalf_of="rahul")).json()
    s = client.get(f"/sheet/{d['id']}").json()
    assert s["requester"] == "rahul" and s["requester_role"] == "branch_manager" and s["expires_ts"] > d["created_ts"]
    assert s["decision"]["approvals_needed"] == 1


def test_evidence_trail_for_a_blocked_refund(client):
    d = client.post("/propose", json=make_proposal("refund-agent", "refund", {"customer": "C-1042", "month": "March", "match": "batch"})).json()
    seq = [e for e in client.get("/audit").json() if "R06" == e["rule"]][0]["seq"]
    ev = client.get(f"/audit/{seq}/evidence").json()
    keys = [s["key"] for s in ev["steps"]]
    assert keys == ["Request", "Envelope", "Measured effect", "Policy", "Approval", "Seal", "Execution"]
    assert ev["result"] == "BLOCKED" and "212" in [s for s in ev["steps"] if s["key"] == "Measured effect"][0]["text"]
    assert [s for s in ev["steps"] if s["key"] == "Policy"][0]["state"] == "failed"


def test_evidence_trail_covers_approval_seal_and_execution(client):
    d = client.post("/propose", json=make_proposal("ops-agent", "transfer", {"batch": "pending", "vendor": "V-05"}, on_behalf_of="rahul")).json()
    client.post("/approve", json={"decision_id": d["id"]}, headers=PRIYA)
    client.post(f"/execute/{d['id']}", headers=PRIYA)
    seq = [e for e in client.get("/audit").json() if e["action"] == "transfer" and e["decision"] == "HOLD"][0]["seq"]
    ev = client.get(f"/audit/{seq}/evidence").json()
    st = {s["key"]: s for s in ev["steps"]}
    assert ev["result"] == "EXECUTED" and "Priya" in st["Approval"]["text"] and st["Seal"]["state"] == "done" and st["Execution"]["state"] == "done"


def test_evidence_for_a_gate_refusal(client):
    p = make_proposal("refund-agent", "lookup", {"customer": "C-1042"})
    p["args"]["customer"] = "C-9999"
    client.post("/propose", json=p)
    seq = client.get("/audit").json()[0]["seq"]
    ev = client.get(f"/audit/{seq}/evidence").json()
    assert ev["steps"][0]["state"] == "failed" and ev["rule"] == "R01"


def test_refund_rows_carry_customer_names(client):
    d = client.post("/propose", json=make_proposal("refund-agent", "refund", {"customer": "C-1042", "month": "March", "match": "batch"})).json()
    metas = d["effect"]["row_meta"]["refunds"].values()
    assert all(m.get("name") for m in metas)
