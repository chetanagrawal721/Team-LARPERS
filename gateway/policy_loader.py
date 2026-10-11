"""Per-organisation policy files. Fails closed on malformed policy; yaml.safe_load only."""
import hashlib
import json
import pathlib

import yaml
from pydantic import BaseModel, ConfigDict, ValidationError

from . import config

LEVELS = ["PUBLIC", "INTERNAL", "PII", "SECRET"]


class PolicyError(Exception):
    pass


class PolicyModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    org: str
    domain: str
    db: str
    currency: str = "INR"
    internal_domains: list[str] = []
    agents: dict[str, dict]
    roles: dict[str, list[str]]
    actions: dict[str, dict]
    labels: dict[str, str]
    destinations: dict[str, str]
    envelopes: dict[str, dict] = {}
    tiers: dict = {}
    tier_overrides: list[dict] = []
    protected: list[str] = []
    budgets: dict[str, dict] = {}
    shadow_mode: dict = {}
    honeytokens: list[str] = []


def canonical_hash(raw) -> str:
    text = json.dumps(raw, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode()).hexdigest()


class Policy:
    def __init__(self, raw: dict):
        try:
            self.model = PolicyModel(**raw)
        except ValidationError as e:
            raise PolicyError(f"invalid policy: {e}") from e
        for lvl in list(self.model.labels.values()) + list(self.model.destinations.values()):
            if lvl not in LEVELS + ["UNTRUSTED"]:
                raise PolicyError(f"unknown label level {lvl!r}")
        self.raw = raw
        self.hash = canonical_hash(raw)

    @property
    def domain(self) -> str:
        return self.model.domain

    @property
    def org(self) -> str:
        return self.model.org

    @property
    def agents(self) -> dict:
        return self.model.agents

    @property
    def labels(self) -> dict:
        return self.model.labels

    @property
    def destinations(self) -> dict:
        return self.model.destinations

    @property
    def label_catalog_ver(self) -> str:
        """Version of the label catalog: hash of labels + destination clearances."""
        return canonical_hash({"labels": self.labels, "destinations": self.destinations})[:16]

    @property
    def rules_hash(self) -> str:
        """Policy version excluding the label catalog, so policy drift and label drift are told apart."""
        return canonical_hash({k: v for k, v in self.raw.items() if k not in ("labels", "destinations")})

    def envelope_default(self, action: str) -> dict:
        e = dict(self.model.envelopes.get(action, {}))
        return {"max_rows": e.get("max_rows"),
                "max_amount_minor": int(e["max_amount"] * 100) if "max_amount" in e else None}

    def action_def(self, action: str) -> dict:
        return self.model.actions.get(action, {})

    def is_protected(self, action: str) -> bool:
        return action in self.model.protected

    def is_honeytoken(self, action: str) -> bool:
        return action in self.model.honeytokens

    def label_for(self, table: str, column: str | None = None) -> str:
        """Strict default: unlabelled columns are INTERNAL."""
        if column and f"{table}.{column}" in self.labels:
            return self.labels[f"{table}.{column}"]
        return self.labels.get(f"{table}.*", "INTERNAL")

    def to_json(self) -> str:
        return json.dumps(self.raw, sort_keys=True, separators=(",", ":"))


def load_text(text: str) -> Policy:
    try:
        raw = yaml.safe_load(text)
    except yaml.YAMLError as e:
        raise PolicyError(f"malformed YAML: {e}") from e
    if not isinstance(raw, dict):
        raise PolicyError("policy must be a mapping")
    return Policy(raw)


def load(domain: str, path: pathlib.Path | None = None) -> Policy:
    path = path or (config.POLICY_DIR / f"{domain}.yaml")
    return load_text(pathlib.Path(path).read_text(encoding="utf-8"))


def load_users() -> dict:
    raw = yaml.safe_load((config.ROOT / "gateway" / "users.yaml").read_text(encoding="utf-8"))
    return raw["users"]
