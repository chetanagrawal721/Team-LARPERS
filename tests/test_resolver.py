import pathlib

import pytest

from gateway import policy_loader, resolver
from gateway.resolver import Ctx, ResolverError
from gateway.resolvers import bank
from gateway.seed import bank_seed
from gateway.seed.common import db_hash


@pytest.fixture(scope="module")
def real_db(tmp_path_factory):
    return bank_seed.seed(tmp_path_factory.mktemp("res") / "bank.db")


@pytest.fixture(scope="module")
def ctx():
    return Ctx(policy=policy_loader.load("bank"), agent="refund-agent", human="meera", now=1_750_000_000)


def run(real_db, ctx, action, args, tmp_path):
    return resolver.resolve(bank.RESOLVERS[action], real_db, args, ctx, scratch_dir=tmp_path)


def test_single_update(real_db, ctx, tmp_path):
    m = run(real_db, ctx, "update_contact", {"customer": "C-0007", "phone": "+91-9800000007"}, tmp_path)
    assert m.effect.rows == {"customers": ["C-0007"]}
    assert m.effect.row_meta["customers"]["C-0007"]["op"] == "modified"


def test_broad_refund_212_rows_61_customers(real_db, ctx, tmp_path):
    m = run(real_db, ctx, "refund", {"customer": "C-1042", "month": "March", "match": "batch"}, tmp_path)
    assert len(m.effect.rows["refunds"]) == 212
    custs = {v["customer_id"] for v in m.effect.row_meta["refunds"].values()}
    assert len(custs) == 61 and m.effect.amount_minor == 98_000_000


def test_narrow_refund_three_rows(real_db, ctx, tmp_path):
    m = run(real_db, ctx, "refund", {"customer": "C-1042", "month": "March"}, tmp_path)
    assert len(m.effect.rows["refunds"]) == 3 and m.effect.amount_minor == 640000
    assert m.effect.reversible == "compensating"


def test_cascade_visible(real_db, ctx, tmp_path):
    class Delete(resolver.Resolver):
        action = "x"
        tables = ("transactions", "refunds")

        def apply(self, conn, args, ctx):
            conn.execute("INSERT INTO refunds VALUES ('RF-Z','T-000001','C-0007',1,1)")
            conn.execute("DELETE FROM refunds WHERE id='RF-Z'")
            conn.execute("INSERT INTO refunds VALUES ('RF-Y','T-000001','C-0007',1,1)")
            conn.execute("DELETE FROM transactions WHERE id='T-000001'")
            return {}

    m = resolver.resolve(Delete(), real_db, {}, ctx, scratch_dir=tmp_path)
    assert m.effect.rows == {"transactions": ["T-000001"]}  # RF-Y was added then cascaded away: net no row
    assert m.effect.row_meta["transactions"]["T-000001"]["op"] == "removed"


def test_real_db_untouched(real_db, ctx, tmp_path):
    before = db_hash(real_db)
    run(real_db, ctx, "refund", {"customer": "C-1042", "month": "March", "match": "batch"}, tmp_path)
    run(real_db, ctx, "transfer", {"batch": "pending"}, tmp_path)
    assert db_hash(real_db) == before


def test_effect_hash_stable_and_sensitive(real_db, ctx, tmp_path):
    a = run(real_db, ctx, "refund", {"customer": "C-1042", "month": "March"}, tmp_path)
    b = run(real_db, ctx, "refund", {"customer": "C-1042", "month": "March"}, tmp_path)
    c = run(real_db, ctx, "refund", {"customer": "C-2210", "month": "March"}, tmp_path)
    assert resolver.effect_hash(a.effect) == resolver.effect_hash(b.effect) != resolver.effect_hash(c.effect)
    assert a.state_ver == b.state_ver


def test_unknown_action(real_db, ctx):
    from gateway import resolvers
    with pytest.raises(ResolverError):
        resolvers.get("bank", "drop_table")


def test_injection_is_inert(real_db, ctx, tmp_path):
    with pytest.raises(ResolverError):
        run(real_db, ctx, "refund", {"customer": "C-1' OR 1=1 --", "month": "March"}, tmp_path)
    with pytest.raises(ResolverError):
        run(real_db, ctx, "transfer", {"batch": "pending", "vendor": "V-01' OR '1'='1"}, tmp_path)


def test_transfer_forty_rows(real_db, ctx, tmp_path):
    m = run(real_db, ctx, "transfer", {"batch": "pending"}, tmp_path)
    assert len(m.effect.rows["invoices"]) == 40 and len(m.effect.rows["transactions"]) == 40
    assert m.effect.amount_minor == 4_000_000 and m.effect.reversible == "none"


def test_no_string_built_sql_with_agent_input():
    for f in pathlib.Path("gateway/resolvers").glob("*.py"):
        for line in f.read_text().splitlines():
            if 'f"SELECT' in line or "f'SELECT" in line:
                pytest.fail(f"{f}: {line}")
