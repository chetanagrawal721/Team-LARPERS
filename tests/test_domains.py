"""Milestone 7.2: hospital and e-commerce domains run through the same engine (policy + seed + resolvers only)."""
import pytest

from gateway import safe_version
from gateway.engine import Engine
from gateway.policy_loader import load_users
from tests.helpers import make_proposal

USERS = load_users()


def U(name):
    return {"id": name, **USERS[name]}


@pytest.fixture
def hospital(tmp_path):
    return Engine("hospital", data_dir=tmp_path)


@pytest.fixture
def shop(tmp_path):
    return Engine("shop", data_dir=tmp_path)


def go(e, agent, action, args, **kw):
    return e.propose(make_proposal(agent, action, args, **kw))


SHAH = "dr.shah@punecare.example"


def test_report_with_340_patients_blocked(hospital):
    d = go(hospital, "records-agent", "send_report", {"patient": "P-0001", "to": SHAH, "attachment": "batch_all"},
           user_instruction="Share Ramesh's report with Dr. Shah")
    assert d.verdict == "BLOCK" and d.rule == "R06" and len(d.effect.rows["disclosed"]) == 340
    assert d.safe_version and d.safe_version["rows"] == {"disclosed": 1} and d.safe_version["verdict"] == "ALLOW"


def test_safe_version_accept_sends_one_patient(hospital):
    d = go(hospital, "records-agent", "send_report", {"patient": "P-0001", "to": SHAH, "attachment": "batch_all"})
    nd = safe_version.accept(hospital, U("rahul"), d.id)
    assert nd.status == "done"
    c = hospital.real_conn()
    assert c.execute("SELECT COUNT(*) FROM outbox").fetchone()[0] == 1


def test_single_patient_report_to_internal_doctor_allowed(hospital):
    d = go(hospital, "records-agent", "send_report", {"patient": "P-0001", "to": SHAH})
    assert d.verdict == "ALLOW" and d.status == "done"


def test_report_to_external_blocked_no_safe_version(hospital):
    d = go(hospital, "records-agent", "send_report", {"patient": "P-0001", "to": "intake@outside-lab.example"})
    assert d.verdict == "BLOCK" and d.rule == "R05" and d.safe_version is None


def test_fk_cascade_delete_blocked_twin_held(hospital):
    d = go(hospital, "records-agent", "delete_record", {"patient": "P-0100"})
    assert d.verdict == "BLOCK" and d.rule == "R06"
    assert set(d.effect.rows) == {"patients", "reports", "appointments"} and len(d.effect.rows["appointments"]) == 12
    t = go(hospital, "records-agent", "delete_record", {"patient": "P-0300"})
    assert t.verdict == "HOLD" and t.tier == "T2"


def test_file_relay_blocked_and_provenance_shown(shop):
    w = go(shop, "support-agent", "write_file", {"path": "shared/q3_customers.csv", "source": "customers"})
    assert w.verdict == "ALLOW" and w.status == "done"
    d = go(shop, "marketing-agent", "send_email", {"list": "agency", "file": "shared/q3_customers.csv",
                                                   "subject": "Q3", "body": "Attached."})
    assert d.verdict == "BLOCK" and d.rule == "R05" and "PII" in d.effect.labels
    assert any("shared/q3_customers.csv" in x for x in d.effect.label_path)
    assert d.safe_version and d.safe_version["verdict"] == "ALLOW"


def test_newsletter_allowed(shop):
    d = go(shop, "marketing-agent", "send_email", {"list": "newsletter", "subject": "Offers", "body": "Offers are live."})
    assert d.verdict == "ALLOW" and len(d.effect.recipients) == 60


def test_list_expands_to_37_externals(shop):
    d = go(shop, "marketing-agent", "send_email", {"list": "staff_all", "subject": "Update", "body": "Team update."},
           user_instruction="Email the staff update to the internal team")
    assert d.verdict == "BLOCK" and d.rule == "R06" and len(d.envelope_check.offending_recipients) == 37
    assert d.safe_version and len(d.safe_version["recipients"]) == 20
    ok = go(shop, "marketing-agent", "send_email", {"list": "staff_internal", "subject": "Update", "body": "Team update."})
    assert ok.verdict == "ALLOW"


def test_paraphrase_fallback_holds_after_pii_access(shop):
    shop.record_touched("support-agent", ["PII"])
    d = go(shop, "support-agent", "send_email", {"list": "agency", "subject": "Buyers",
                                                 "body": "Asha Kulkarni of Pune spent 50k."})
    assert d.verdict == "HOLD" and d.rule == "R11" and d.decision_path == "fallback"


def test_domain_switch_gives_each_policy(client):
    hashes = {}
    for name in ("shop", "hospital", "bank"):
        r = client.post(f"/domain/{name}").json()
        hashes[name] = r["policy_hash"]
        assert r["domain"] == name
    assert len(set(hashes.values())) == 3
    assert client.post("/domain/nowhere").status_code == 404


def test_core_modules_untouched_by_domains():
    import pathlib
    text = "".join(pathlib.Path(f"gateway/{m}.py").read_text() for m in ("rules", "seal", "execute"))
    assert "hospital" not in text and "shop" not in text
