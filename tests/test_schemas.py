import pathlib

import pytest
import yaml
from fastapi.testclient import TestClient
from pydantic import ValidationError

from gateway.schemas import Decision, Proposal

VALID = dict(agent="refund-agent", action="refund", args={"customer": "C-1042"},
             nonce="n1", ts=1, sig="x")


def test_valid_proposal():
    assert Proposal(**VALID).agent == "refund-agent"


def test_extra_field_rejected():
    with pytest.raises(ValidationError):
        Proposal(**VALID, admin=True)


def test_missing_nonce_rejected():
    v = dict(VALID); v.pop("nonce")
    with pytest.raises(ValidationError):
        Proposal(**v)


def test_invalid_verdict_rejected():
    with pytest.raises(ValidationError):
        Decision(id="x", verdict="MAYBE", rule="R1", reason="", baseline_verdict="ALLOW",
                 decision_path="rules-only")


def test_mock_api_serves_example():
    from gateway.mock_api import app
    r = TestClient(app).get("/action/demo-1")
    assert r.status_code == 200 and r.json()["id"] == "demo-1" and r.json()["verdict"] == "BLOCK"
    Decision(**r.json())


def test_suite_has_22_pairs():
    cases = yaml.safe_load(pathlib.Path("lab/suite.yaml").read_text())
    assert len(cases) >= 22 and cases[21]["id"] == "A22"
    ids = set()
    for c in cases:
        assert c["id"] not in ids
        ids.add(c["id"])
        for k in ("domain", "attack", "expect_C", "twin", "twin_expect_C", "kind"):
            assert k in c, (c["id"], k)
