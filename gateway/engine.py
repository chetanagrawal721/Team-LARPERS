"""SEALGATE engine: one instance per domain. Orchestrates verify -> identify -> see -> judge -> seal -> execute -> log."""
import json
import threading
import uuid

from . import audit, clock, config, registry, verify
from .db import init_state
from .policy_loader import Policy, load as load_policy
from .schemas import Decision, Event, Proposal


class Engine:
    def __init__(self, domain: str, data_dir=None, policy: Policy | None = None, mode: str = "C"):
        self.domain = domain
        self.data_dir = config.DATA_DIR if data_dir is None else data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.policy = policy or load_policy(domain)
        self.mode = mode
        self.lock = threading.RLock()
        self.state = init_state(self.data_dir / f"{domain}_state.db")
        self.bus = None
        self._store_policy_version()

    # ---- helpers -----------------------------------------------------------------
    def _store_policy_version(self) -> None:
        self.state.execute("INSERT OR IGNORE INTO policy_versions (hash, policy_json, ts) VALUES (?,?,?)",
                           (self.policy.hash, self.policy.to_json(), int(clock.now())))

    def reload_policy(self) -> str:
        with self.lock:
            self.policy = load_policy(self.domain)
            self._store_policy_version()
            audit.append(self.state, int(clock.now()), "gateway", "policy_reload",
                         {"policy_hash": self.policy.hash}, "ALLOW", "-", "rules-only", self.policy.hash)
            return self.policy.hash

    def emit(self, type_: str, decision_id: str | None = None, **data) -> None:
        if self.bus is not None:
            self.bus.publish(Event(type=type_, ts=int(clock.now()), decision_id=decision_id, data=data))

    def new_id(self) -> str:
        return "D-" + uuid.uuid4().hex[:8]

    # ---- decision persistence ------------------------------------------------------
    def save_decision(self, d: Decision, proposal: dict | None = None, requester: str = "",
                      parent_id: str | None = None) -> None:
        exists = self.state.execute("SELECT 1 FROM decisions WHERE id=?", (d.id,)).fetchone()
        if exists:
            self.state.execute("UPDATE decisions SET decision_json=?, status=? WHERE id=?",
                               (d.model_dump_json(), d.status, d.id))
        else:
            self.state.execute(
                "INSERT INTO decisions (id, created_ts, agent, action, requester, proposal_json, decision_json,"
                " status, parent_id) VALUES (?,?,?,?,?,?,?,?,?)",
                (d.id, d.created_ts, d.agent, d.action, requester,
                 json.dumps(proposal or {}, sort_keys=True), d.model_dump_json(), d.status, parent_id))

    def get_decision(self, decision_id: str) -> Decision | None:
        r = self.state.execute("SELECT decision_json FROM decisions WHERE id=?", (decision_id,)).fetchone()
        return Decision.model_validate_json(r["decision_json"]) if r else None

    def list_decisions(self, limit: int = 50) -> list[Decision]:
        rows = self.state.execute("SELECT decision_json FROM decisions ORDER BY created_ts DESC, rowid DESC LIMIT ?",
                                  (limit,)).fetchall()
        return [Decision.model_validate_json(r["decision_json"]) for r in rows]

    def refuse(self, p_raw: dict, agent: str, action: str, rule: str, reason: str, payload_extra: dict | None = None,
               decision_path: str = "rules-only") -> Decision:
        """Record and return a BLOCK decision (every refusal is logged, R8)."""
        d = Decision(id=self.new_id(), verdict="BLOCK", rule=rule, reason=reason, baseline_verdict="BLOCK",
                     decision_path=decision_path, status="blocked", agent=agent, action=action,
                     rules_fired=[rule], policy_hash=self.policy.hash, created_ts=int(clock.now()))
        payload = {"proposal": {k: v for k, v in p_raw.items() if k != "sig"}, "reason": reason}
        payload.update(payload_extra or {})
        audit.append(self.state, d.created_ts, agent, action, payload, "BLOCK", rule, decision_path,
                     self.policy.hash)
        self.save_decision(d, p_raw)
        self.emit("decision", d.id, verdict="BLOCK", rule=rule, reason=reason, agent=agent, action=action)
        return d

    # ---- propose (stage 1: identity; later stages are added by later milestones) --------
    def propose(self, p_raw: dict) -> Decision:
        with self.lock:
            p = Proposal(**p_raw)
            if p.agent not in self.policy.agents:
                return self.refuse(p_raw, p.agent, p.action, "R02", f"unknown agent {p.agent!r}")
            ok, why = verify.verify_proposal(self.state, p)
            if not ok:
                return self.refuse(p_raw, p.agent, p.action, "R01", why)
            return self._analyse(p, p_raw)

    def _analyse(self, p: Proposal, p_raw: dict) -> Decision:
        if self.policy.is_honeytoken(p.action):
            return self.refuse(p_raw, p.agent, p.action, "R03", "honeytoken action called")
        if not registry.knows(self.policy, p.agent, p.action):
            return self.refuse(p_raw, p.agent, p.action, "R02", f"action {p.action!r} not allowed for agent")
        d = Decision(id=self.new_id(), verdict="HOLD", rule="PENDING", reason="analysis not yet available",
                     baseline_verdict="ALLOW", decision_path="rules-only", status="pending", agent=p.agent,
                     action=p.action, policy_hash=self.policy.hash, created_ts=int(clock.now()))
        audit.append(self.state, d.created_ts, p.agent, p.action, {"proposal": p_raw}, d.verdict, d.rule,
                     d.decision_path, self.policy.hash)
        self.save_decision(d, p_raw)
        return d
