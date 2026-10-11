"""Frozen API contract (Milestone 0.3). Changes after 0.3 are 'last-moment changes' and must be logged."""
from typing import Literal

from pydantic import BaseModel, Field

Verdict = Literal["ALLOW", "HOLD", "BLOCK", "VOID", "DONE"]
Status = Literal["done", "pending", "approved", "blocked", "void", "rejected", "shadow", "allowed"]
DriftType = Literal["args_drift", "effect_drift", "label_drift", "policy_drift",
                    "state_drift", "replay", "expired", "bad_signature"]


class Proposal(BaseModel):
    agent: str
    action: str
    args: dict
    intent: str = ""
    user_instruction: str = ""          # original human request (for envelope)
    on_behalf_of: str = ""              # human the agent acts for; "" -> policy default
    nonce: str
    ts: int
    sig: str
    model_config = {"extra": "forbid"}


class Effect(BaseModel):
    action_type: str
    rows: dict[str, list[str]] = {}
    row_meta: dict[str, dict[str, dict]] = {}   # table -> pk -> key attributes (customer, amount, ...)
    table_sizes: dict[str, int] = {}            # size of each affected table before the action
    recipients: list[str] = []
    amount_minor: int = 0
    currency: str = "INR"
    destinations: list[str] = []
    reversible: Literal["snapshot", "compensating", "none"] = "snapshot"
    labels: list[str] = []
    label_path: list[str] = []
    label_catalog_ver: str = ""


class Envelope(BaseModel):
    scope: dict = {}
    max_rows: int | None = None
    max_amount_minor: int | None = None
    allowed_destinations: list[str] = []
    source: Literal["ai_from_instruction", "policy_default"]


class EnvelopeCheck(BaseModel):
    inside: bool
    offending_rows: dict[str, list[str]] = {}
    offending_recipients: list[str] = []
    over_amount: int = 0
    over_rows: int = 0
    reasons: list[str] = []


class Decision(BaseModel):
    id: str
    verdict: Verdict
    rule: str
    reason: str
    baseline_verdict: Verdict            # what a mode-B gate would say
    decision_path: Literal["rules-only", "rules+ai", "fallback"]
    effect: Effect | None = None
    envelope: Envelope | None = None
    envelope_check: EnvelopeCheck | None = None
    safe_version: dict | None = None
    status: Status = "pending"
    tier: str = ""
    approvals_needed: int = 0
    approvals: list[str] = []
    rules_fired: list[str] = []
    drift: DriftType | None = None
    ai_reason: str = ""
    shadow_session: str | None = None
    agent: str = ""
    action: str = ""
    agent_claim: str = ""
    policy_hash: str = ""
    created_ts: int = 0


class ApprovalRequest(BaseModel):
    decision_id: str
    note: str = ""
    model_config = {"extra": "forbid"}


class Event(BaseModel):
    type: Literal["decision", "approval", "execution", "void", "chat", "shadow",
                  "audit", "freeze", "domain", "ai", "agent", "pipeline", "sandbox"]
    ts: int
    decision_id: str | None = None
    data: dict = Field(default_factory=dict)
