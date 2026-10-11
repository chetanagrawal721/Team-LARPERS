import pytest

from gateway import envelope, policy_loader, resolver
from gateway.resolver import Ctx
from gateway.resolvers import bank
from gateway.schemas import Envelope
from gateway.seed import bank_seed


@pytest.fixture(scope="module")
def real_db(tmp_path_factory):
    return bank_seed.seed(tmp_path_factory.mktemp("env") / "bank.db")


@pytest.fixture(scope="module")
def policy():
    return policy_loader.load("bank")


def effect(real_db, policy, action, args, tmp_path):
    return resolver.resolve(bank.RESOLVERS[action], real_db, args, Ctx(policy=policy, now=1),
                            scratch_dir=tmp_path).effect


def test_inside_for_single_customer(real_db, policy, tmp_path):
    e = effect(real_db, policy, "refund", {"customer": "C-1042", "month": "March"}, tmp_path)
    env = envelope.default_for(policy, "refund", {"customer": "C-1042", "month": "March"})
    assert envelope.check(e, env, policy).inside


def test_outside_other_customers(real_db, policy, tmp_path):
    args = {"customer": "C-1042", "month": "March", "match": "batch"}
    e = effect(real_db, policy, "refund", args, tmp_path)
    chk = envelope.check(e, envelope.default_for(policy, "refund", args), policy)
    assert not chk.inside and len(chk.offending_rows["refunds"]) == 209


def test_outside_amount(real_db, policy, tmp_path):
    e = effect(real_db, policy, "transfer", {"batch": "pending"}, tmp_path)
    env = Envelope(scope={}, max_amount_minor=1_000_000, source="policy_default")
    chk = envelope.check(e, env, policy)
    assert not chk.inside and chk.over_amount == 3_000_000


def test_outside_destination(real_db, policy, tmp_path):
    e = effect(real_db, policy, "transfer", {"batch": "pending"}, tmp_path)
    env = Envelope(scope={}, allowed_destinations=["internal_email"], source="policy_default")
    chk = envelope.check(e, env, policy)
    assert not chk.inside and chk.offending_recipients


def test_empty_effect_is_inside(real_db, policy, tmp_path):
    e = effect(real_db, policy, "refund", {"customer": "C-0007", "month": "March"}, tmp_path)
    assert e.rows == {} and envelope.check(e, envelope.default_for(policy, "refund", {"customer": "C-0007"}), policy).inside


def test_missing_scope_key_gives_strictest_envelope(policy):
    env = envelope.default_for(policy, "refund", {"month": "March"})
    assert env.max_rows == 1 and env.source == "policy_default"


def test_row_limit_exceeded_inside_scope(real_db, policy, tmp_path):
    e = effect(real_db, policy, "refund", {"customer": "C-1042", "month": "March"}, tmp_path)
    env = Envelope(scope={"customer": "C-1042"}, max_rows=2, source="policy_default")
    chk = envelope.check(e, env, policy)
    assert not chk.inside and chk.over_rows == 1 and len(chk.offending_rows["refunds"]) == 1
