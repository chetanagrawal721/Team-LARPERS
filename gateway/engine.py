"""SEALGATE engine: one instance per domain. Orchestrates verify -> identify -> see -> judge -> seal -> execute -> log."""
import importlib
import json
import pathlib
import threading
import uuid

from . import audit, budgets, clock, config, envelope as envelope_mod, registry, resolver, resolvers, verify
from .db import init_state
from .decide import baseline_verdict, decide
from .policy_loader import Policy, load as load_policy
from .resolver import Ctx, ResolverError
from .schemas import Decision, Envelope, EnvelopeCheck, Event, Proposal
from .seed.common import connect


class Engine:
    def __init__(self, domain: str, data_dir=None, policy: Policy | None = None, mode: str = "C"):
        self.domain = domain
        self.data_dir = pathlib.Path(config.DATA_DIR if data_dir is None else data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.policy = policy or load_policy(domain)
        self.mode = mode
        self.lock = threading.RLock()
        self.state = init_state(self.data_dir / f"{domain}_state.db")
        self.bus = None
        self.real_path = self.data_dir / self.policy.model.db
        self.scratch = self.data_dir / "sandbox"
        self.scratch.mkdir(exist_ok=True)
        if not self.real_path.exists():
            self.reset_domain_data()
        self._store_policy_version()

    # ---- data ----------------------------------------------------------------------
    def reset_domain_data(self) -> None:
        """Re-create the fictional database for this domain (deterministic seed)."""
        seed = importlib.import_module(f"gateway.seed.{self.domain}_seed")
        seed.seed(self.real_path)

    def real_conn(self):
        return connect(self.real_path)

    # ---- helpers -------------------------------------------------------------------
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

    # ---- agents: freeze ------------------------------------------------------------
    def is_frozen(self, agent: str) -> bool:
        return self.state.execute("SELECT 1 FROM frozen_agents WHERE agent=?", (agent,)).fetchone() is not None

    def freeze(self, agent: str, reason: str) -> None:
        self.state.execute("INSERT OR REPLACE INTO frozen_agents (agent, reason, ts) VALUES (?,?,?)",
                           (agent, reason, int(clock.now())))
        self.emit("freeze", agent=agent, reason=reason)

    def unfreeze(self, agent: str) -> None:
        self.state.execute("DELETE FROM frozen_agents WHERE agent=?", (agent,))

    # ---- decision persistence ------------------------------------------------------
    def save_decision(self, d: Decision, proposal: dict | None = None, requester: str = "",
                      parent_id: str | None = None, meta: dict | None = None) -> None:
        exists = self.state.execute("SELECT 1 FROM decisions WHERE id=?", (d.id,)).fetchone()
        if exists:
            self.state.execute("UPDATE decisions SET decision_json=?, status=? WHERE id=?",
                               (d.model_dump_json(), d.status, d.id))
        else:
            self.state.execute(
                "INSERT INTO decisions (id, created_ts, agent, action, requester, proposal_json, decision_json,"
                " status, parent_id, meta_json) VALUES (?,?,?,?,?,?,?,?,?,?)",
                (d.id, d.created_ts, d.agent, d.action, requester,
                 json.dumps(proposal or {}, sort_keys=True), d.model_dump_json(), d.status, parent_id,
                 json.dumps(meta or {}, sort_keys=True)))

    def get_decision(self, decision_id: str) -> Decision | None:
        r = self.state.execute("SELECT decision_json FROM decisions WHERE id=?", (decision_id,)).fetchone()
        return Decision.model_validate_json(r["decision_json"]) if r else None

    def get_record(self, decision_id: str) -> dict | None:
        r = self.state.execute("SELECT * FROM decisions WHERE id=?", (decision_id,)).fetchone()
        if not r:
            return None
        rec = dict(r)
        rec["proposal"] = json.loads(rec.pop("proposal_json") or "{}")
        rec["meta"] = json.loads(rec.pop("meta_json") or "{}")
        rec["decision"] = Decision.model_validate_json(rec.pop("decision_json"))
        return rec

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

    # ---- propose ---------------------------------------------------------------------
    def propose(self, p_raw: dict) -> Decision:
        with self.lock:
            p = Proposal(**p_raw)
            if p.agent not in self.policy.agents:
                return self.refuse(p_raw, p.agent, p.action, "R02", f"unknown agent {p.agent!r}")
            ok, why = verify.verify_proposal(self.state, p)
            if not ok:
                return self.refuse(p_raw, p.agent, p.action, "R01", why)
            return self._analyse(p, p_raw)

    def ai_advice(self, p: Proposal, effect, env) -> dict:
        """Escalate-only advisor. Replaced by the AI layer in Phase 5; until then the fallback path is used."""
        return {"escalation": "NONE", "status": "off", "reason": ""}

    def build_envelope(self, p: Proposal) -> Envelope:
        return envelope_mod.default_for(self.policy, p.action, p.args)

    def _analyse(self, p: Proposal, p_raw: dict) -> Decision:
        pol = self.policy
        human = registry.resolve_human(pol, p.agent, p.on_behalf_of)
        honey = pol.is_honeytoken(p.action)
        if honey:
            self.freeze(p.agent, f"called honeytoken {p.action}")
        known = registry.knows(pol, p.agent, p.action) or honey
        perms = registry.effective_permissions(pol, p.agent, human)
        inp = {"agent": p.agent, "action": p.action, "human": human, "sig_ok": True, "known": known,
               "honeytoken": honey, "frozen": self.is_frozen(p.agent) and not honey,
               "permitted": honey or p.action in perms,
               "self_change": p.action == "grant_role" and p.args.get("target") in pol.agents,
               "effect": None, "envelope": None, "check": None, "budget_exceeded": False,
               "ai": {"escalation": "NONE", "status": "n/a", "reason": ""}}
        early = (not known) or honey or inp["frozen"] or (not inp["permitted"]) or inp["self_change"]
        if early:
            return self._finish(p, p_raw, human, inp, None, None)
        did = self.new_id()
        try:
            res = resolvers.get(self.domain, p.action)
            measured = resolver.resolve(res, self.real_path, p.args,
                                        Ctx(policy=pol, agent=p.agent, human=human, now=int(clock.now()),
                                            decision_id=did), scratch_dir=self.scratch)
        except ResolverError as e:
            return self.refuse(p_raw, p.agent, p.action, "R99", f"invalid request: {e}")
        effect = measured.effect
        env = self.build_envelope(p)
        chk = envelope_mod.check(effect, env, pol)
        conn = self.real_conn()
        try:
            bud = budgets.check(conn, pol, p.agent, p.action, effect.amount_minor)
        finally:
            conn.close()
        ai = self.ai_advice(p, effect, env)
        inp.update(effect=effect.model_dump(), envelope=env.model_dump(), check=chk.model_dump(),
                   budget_exceeded=bud["exceeded"], budget=bud["snapshot"], ai=ai,
                   intent_unverified=bool(p.intent) and ai.get("status") != "ok")
        return self._finish(p, p_raw, human, inp, measured, did)

    def _finish(self, p: Proposal, p_raw: dict, human: str, inp: dict, measured, did: str | None) -> Decision:
        pol = self.policy
        out = decide(inp, pol)
        base = baseline_verdict(inp, pol)
        effect = measured.effect if measured else None
        status = {"ALLOW": "allowed", "HOLD": "pending", "BLOCK": "blocked"}[out["verdict"]]
        d = Decision(
            id=did or self.new_id(), verdict=out["verdict"], rule=out["rule"], reason=out["reason"],
            baseline_verdict=base, decision_path=out["decision_path"], effect=effect,
            envelope=Envelope(**inp["envelope"]) if inp.get("envelope") else None,
            envelope_check=EnvelopeCheck(**inp["check"]) if inp.get("check") else None,
            status=status, tier=out["tier"], approvals_needed=out["approvals_needed"],
            rules_fired=out["rules_fired"], ai_reason=(inp.get("ai") or {}).get("reason", ""),
            agent=p.agent, action=p.action, agent_claim=p.intent, policy_hash=pol.hash,
            created_ts=int(clock.now()))
        meta = {"human": human, "state_ver": measured.state_ver if measured else "",
                "effect_hash": resolver.effect_hash(effect) if effect else "",
                "label_path_hash": resolver.label_path_hash(effect) if effect else "",
                "label_catalog_ver": pol.label_catalog_ver}
        payload = {"proposal": {k: v for k, v in p_raw.items() if k != "sig"}, "inputs": inp, "outcome": out,
                   "meta": meta}
        audit.append(self.state, d.created_ts, p.agent, p.action, payload, d.verdict, d.rule, d.decision_path,
                     pol.hash)
        self.save_decision(d, p_raw, requester=human, meta=meta)
        self.emit("decision", d.id, verdict=d.verdict, rule=d.rule, reason=d.reason, agent=p.agent,
                  action=p.action, tier=d.tier)
        return d
