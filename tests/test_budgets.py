import threading

import pytest

from gateway import budgets, clock, policy_loader
from gateway.seed import bank_seed
from gateway.seed.common import connect

NOW = 1_750_000_000


@pytest.fixture
def conn(tmp_path):
    return connect(bank_seed.seed(tmp_path / "bank.db"))


@pytest.fixture(scope="module")
def policy():
    return policy_loader.load("bank")


def charge(conn, policy, agent, amount=100000, now=NOW):
    return budgets.check_and_charge_atomic(conn, policy, agent, "refund", amount, now)


def test_under_budget(conn, policy):
    assert not any(charge(conn, policy, "refund-agent")["exceeded"] for _ in range(3))


def test_salami_holds_at_the_exceeding_refund(conn, policy):
    results = [charge(conn, policy, "refund-agent")["exceeded"] for _ in range(60)]
    assert results.index(True) == 50          # the 51st Rs 1,000 refund crosses the Rs 50,000 per-agent limit


def test_split_across_agents_hits_resource_budget(conn, policy):
    agents = ["refund-agent", "refund-agent-2", "refund-agent-3"]
    hit = None
    for i in range(120):
        if charge(conn, policy, agents[i % 3])["exceeded"]:
            hit = i
            break
    assert hit == 100    # each agent is still under its own limit; the shared resource budget (Rs 1 lakh) trips


def test_window_resets(conn, policy):
    for _ in range(50):
        charge(conn, policy, "refund-agent")
    assert charge(conn, policy, "refund-agent")["exceeded"]
    assert not charge(conn, policy, "refund-agent", now=NOW + 3700)["exceeded"]


def test_concurrent_charges_never_exceed(tmp_path, policy):
    path = bank_seed.seed(tmp_path / "bank.db")
    ok = []

    def worker():
        c = connect(path)
        for _ in range(30):
            if not budgets.check_and_charge_atomic(c, policy, "refund-agent", "refund", 100000, NOW)["exceeded"]:
                ok.append(1)

    ts = [threading.Thread(target=worker) for _ in range(4)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert len(ok) == 50


def test_blocked_actions_not_charged(engine):
    from tests.helpers import make_proposal
    engine.propose(make_proposal("refund-agent", "refund", {"customer": "C-1042", "month": "March", "match": "batch"}))
    c = engine.real_conn()
    assert c.execute("SELECT COUNT(*) FROM budgets").fetchone()[0] == 0
