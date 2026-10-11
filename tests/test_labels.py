import pytest

from gateway import labels, policy_loader, resolver
from gateway.resolver import Ctx
from gateway.resolvers import bank
from gateway.seed import bank_seed


@pytest.fixture(scope="module")
def real_db(tmp_path_factory):
    return bank_seed.seed(tmp_path_factory.mktemp("lab") / "bank.db")


@pytest.fixture(scope="module")
def policy():
    return policy_loader.load("bank")


def run(real_db, policy, action, args, tmp_path):
    return resolver.resolve(bank.RESOLVERS[action], real_db, args, Ctx(policy=policy, now=1), scratch_dir=tmp_path)


def test_pii_detected(real_db, policy, tmp_path):
    e = run(real_db, policy, "update_contact", {"customer": "C-0007", "phone": "1"}, tmp_path).effect
    assert "PII" in e.labels


def test_secret_detected(policy):
    assert policy.label_for("customers", "account_no") == "SECRET"
    assert labels.max_level(["PII", "SECRET", "INTERNAL"]) == "SECRET"


def test_untrusted_source(real_db, policy, tmp_path):
    e = run(real_db, policy, "payee_change",
            {"vendor": "V-17", "new_account": "ICICI-0009083", "source": "inbox:E-9001"}, tmp_path).effect
    assert "UNTRUSTED" in e.labels and "inbox.E-9001" in e.label_path[0]


def test_verified_form_is_trusted(real_db, policy, tmp_path):
    e = run(real_db, policy, "payee_change",
            {"vendor": "V-17", "new_account": "HDFC-0004411", "source": "form:F-100"}, tmp_path).effect
    assert "UNTRUSTED" not in e.labels


def test_form_with_mismatching_account_is_untrusted(real_db, policy, tmp_path):
    e = run(real_db, policy, "payee_change",
            {"vendor": "V-17", "new_account": "EVIL-1", "source": "form:F-100"}, tmp_path).effect
    assert "UNTRUSTED" in e.labels


def test_external_destination(policy):
    assert labels.classify_address(policy, "x@agency.com") == "external_email"
    assert labels.classify_address(policy, "a@sahyadribank.example") == "internal_email"


def test_unlabelled_column_defaults_internal(policy):
    assert policy.label_for("brand_new_table", "col") == "INTERNAL"


def test_clearance(policy):
    assert labels.uncleared_destinations(policy, ["PII"], ["external_email"]) == ["external_email"]
    assert labels.uncleared_destinations(policy, ["PII"], ["rbi_reporting"]) == []
    assert labels.unknown_destinations(policy, ["ftp_server"]) == ["ftp_server"]


def test_label_catalog_version_in_effect(real_db, policy, tmp_path):
    e = run(real_db, policy, "refund", {"customer": "C-1042", "month": "March"}, tmp_path).effect
    assert e.label_catalog_ver == policy.label_catalog_ver
