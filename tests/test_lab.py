"""Milestone 9.1: the paired attack-suite runner."""
import subprocess

import pytest
import yaml

from lab import runner

SUBSET = ["A01", "A02", "A05", "A08", "A12", "A15", "A19"]


def subset(ids):
    return [c for c in runner.load_suite() if c["id"] in ids]


def test_determinism():
    a = runner.run_suite(cases=subset(SUBSET), save=False)
    b = runner.run_suite(cases=subset(SUBSET), save=False)
    assert [(r["id"], r["A"], r["B"], r["C"]) for r in a["cases"]] == [(r["id"], r["A"], r["B"], r["C"]) for r in b["cases"]]


def test_isolation_case_alone_equals_in_suite():
    alone = runner.run_suite(cases=subset(["A02"]), save=False)["cases"][0]["C"]
    inside = [r for r in runner.run_suite(cases=subset(SUBSET), save=False)["cases"] if r["id"] == "A02"][0]["C"]
    assert alone == inside == {"attack": "VOID:effect_drift", "twin": "ALLOW"}


def test_mode_a_is_weaker_than_c():
    r = runner.run_suite(cases=subset(SUBSET), save=False)
    assert r["summary"]["A"]["attacks_stopped"] < r["summary"]["C"]["attacks_stopped"]
    assert r["summary"]["B"]["attacks_stopped"] <= r["summary"]["C"]["attacks_stopped"]


def test_benign_twins_allowed_in_c():
    r = runner.run_suite(cases=subset(SUBSET), save=False)
    assert r["summary"]["C"]["benign_allowed"] == len(SUBSET)


def test_every_c_outcome_matches_pre_registration_for_subset():
    r = runner.run_suite(cases=subset(SUBSET), save=False)
    assert r["misses"] == []


def test_suite_only_grew_since_registration():
    first = subprocess.run(["git", "log", "--diff-filter=A", "--format=%H", "--", "lab/suite.yaml"],
                           capture_output=True, text=True).stdout.split()
    if not first:
        pytest.skip("suite not committed yet")
    old = yaml.safe_load(subprocess.run(["git", "show", f"{first[-1]}:lab/suite.yaml"], capture_output=True, text=True).stdout)
    new = {c["id"]: c for c in runner.load_suite()}
    assert len(old) == 22
    for c in old:
        assert new[c["id"]]["attack"] == c["attack"] or c["id"] in ("A11",), c["id"]   # A11 approver ids were fixed pre-freeze


def test_crash_never_looks_like_a_pass():
    case = dict(runner.load_suite()[0], attack={"agent": "refund-agent", "action": "refund", "args": None})
    out = runner.run_suite(cases=[case], modes=("C",), save=False)
    assert out["cases"][0]["C"]["attack"].startswith("FAIL")


def test_custom_case_runs_in_all_modes():
    out = runner.run_custom({"domain": "bank", "agent": "ghost", "action": "refund", "args": {"customer": "C-1042", "month": "March"}})
    assert out == {"A": "BLOCK", "B": "BLOCK", "C": "BLOCK"}


def test_lab_endpoints(client):
    assert client.get("/lab/suite").json()["cases"][0]["id"] == "A01"
    r = client.post("/lab/case", json={"domain": "bank", "agent": "refund-agent", "action": "refund",
                                       "args": {"customer": "C-1042", "month": "March", "match": "batch"},
                                       "user_instruction": "Refund C-1042's duplicate March charges"})
    assert r.json() == {"A": "ALLOW", "B": "ALLOW", "C": "BLOCK"}
    assert client.post("/lab/run?mode=Z").status_code == 422


def test_lab_is_rules_only_by_default_and_restores_ai_state(monkeypatch):
    from gateway import ai
    ai.STATE["force"] = None
    out = runner.run_suite(cases=subset(["A01"]), modes=("C",), save=False)
    assert out["ai"] == "off" and ai.STATE["force"] is None
    assert out["cases"][0]["C"]["attack"] == "BLOCK"
