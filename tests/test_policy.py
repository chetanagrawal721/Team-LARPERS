import copy
import pathlib

import pytest
import yaml

from gateway import policy_loader, registry
from gateway.policy_loader import PolicyError


def raw():
    return yaml.safe_load(pathlib.Path("gateway/policy/bank.yaml").read_text())


def test_load_valid_bank_policy():
    p = policy_loader.load("bank")
    assert len(p.hash) == 64 and p.org == "Sahyadri Bank"


def test_known_agent_action():
    p = policy_loader.load("bank")
    assert registry.knows(p, "refund-agent", "refund")


def test_unknown_agent():
    assert not registry.knows(policy_loader.load("bank"), "ghost", "refund")


def test_known_agent_unlisted_action():
    assert not registry.knows(policy_loader.load("bank"), "refund-agent", "transfer")


def test_unknown_destination():
    p = policy_loader.load("bank")
    assert not registry.destination_allowed(p, "ftp_server")
    assert registry.destination_allowed(p, "internal_email")


def test_malformed_yaml_fails_closed():
    with pytest.raises(PolicyError):
        policy_loader.load_text("agents: [unclosed")
    with pytest.raises(PolicyError):
        policy_loader.load_text("org: x\n")


def test_hash_stability_and_sensitivity():
    r = raw()
    shuffled = dict(reversed(list(r.items())))
    assert policy_loader.Policy(r).hash == policy_loader.Policy(shuffled).hash
    r2 = copy.deepcopy(r)
    r2["envelopes"]["refund"]["max_amount"] = 99999
    assert policy_loader.Policy(r2).hash != policy_loader.Policy(r).hash


def test_confused_deputy():
    p = policy_loader.load("bank")
    assert "transfer" in registry.effective_permissions(p, "ops-agent", "rahul") or True
    assert "transfer" not in registry.effective_permissions(p, "ops-agent", "priya")
    assert "transfer" in registry.effective_permissions(p, "ops-agent", "rahul")


def test_no_unsafe_yaml_load():
    for f in pathlib.Path("gateway").rglob("*.py"):
        assert "yaml.load(" not in f.read_text(), f
