"""One-transaction sealed execution (C5). Re-measure, compare with the seal, run, write the outbox, commit - or roll back."""
import json

from . import audit, budgets, clock, resolver, resolvers, seal
from .approvals import GateError
from .resolver import Ctx, ResolverError
from .schemas import Decision

FAULT = None   # test hook: callable invoked inside the transaction after the action ran (simulates a crash)


def _record_void(engine, rec: dict, d: Decision, drift: str, detail: str = "") -> Decision:
    d.verdict, d.status, d.drift = "VOID", "void", drift
    d.reason = f"seal broken: {drift}" + (f" ({detail})" if detail else "")
    d.rule = "R6"
    engine.save_decision(d)
    audit.append(engine.state, int(clock.now()), d.agent, d.action,
                 {"decision_id": d.id, "drift": drift, "detail": detail}, "VOID", "R6", d.decision_path,
                 engine.policy.hash)
    engine.emit("void", d.id, drift=drift, detail=detail, agent=d.agent, action=d.action)
    return d


def _requeue(engine, rec: dict, d: Decision) -> None:
    """After a void the action is evaluated afresh and returns to HOLD (or is blocked) for a new decision."""
    try:
        nd = engine.reanalyse(rec, parent_id=d.id)
        d.reason += f"; re-evaluated as {nd.id} ({nd.verdict})"
        engine.save_decision(d)
    except Exception as e:  # never let a requeue failure hide the void
        d.reason += f"; re-evaluation failed: {e}"
        engine.save_decision(d)


def execute_sealed(engine, decision_id: str) -> Decision:
    with engine.lock:
        rec = engine.get_record(decision_id)
        if not rec:
            raise GateError(404, "no such decision")
        d: Decision = rec["decision"]
        token, used = seal.load(engine.state, decision_id)
        if token is None:
            raise GateError(409, "decision has no seal (not approved)")
        p = rec["proposal"]
        pol = engine.policy
        # cheap checks first: signature, expiry, replay, args, policy, label catalog
        fresh = {"nonce_used": used, "action_hash": seal.action_hash(p["agent"], p["action"], p["args"]),
                 "policy_ver": pol.rules_hash, "label_catalog_ver": pol.label_catalog_ver}
        mode = engine.mode
        if mode == "A":
            fresh = {}                                  # allowlist only: nothing is re-checked
        elif mode == "B":
            fresh = {"nonce_used": used, "action_hash": fresh["action_hash"]}   # argument-bound approval only
        drift = seal.check(token, fresh) if mode != "A" else "OK"
        if drift == "replay":
            # the original decision stays DONE; the refused second attempt is logged as its own record
            nd = d.model_copy(update={"id": engine.new_id(), "created_ts": int(clock.now())})
            engine.save_decision(nd, p, requester=rec["requester"], parent_id=d.id, meta=rec["meta"])
            return _record_void(engine, rec, nd, "replay", "seal already used")
        if drift != "OK":
            _record_void(engine, rec, d, drift)
            _requeue(engine, rec, d)
            return d
        # execute inside one transaction on the real database
        conn = engine.real_conn()
        try:
            conn.execute("BEGIN IMMEDIATE")
            try:
                if mode != "A" and conn.execute("SELECT 1 FROM used_seals WHERE nonce=?", (token["nonce"],)).fetchone():
                    conn.execute("ROLLBACK")
                    nd = d.model_copy(update={"id": engine.new_id()})
                    return _record_void(engine, rec, nd, "replay", "seal nonce already consumed")
                res = resolvers.get(engine.domain, p["action"])
                ctx = Ctx(policy=pol, agent=p["agent"], human=rec["requester"], now=int(clock.now()),
                          decision_id=d.id)
                m = resolver.measure(res, conn, p["args"], ctx)
                if FAULT:
                    FAULT()
                fresh2 = {"effect_hash": resolver.effect_hash(m.effect),
                          "label_path_hash": resolver.label_path_hash(m.effect), "state_ver": m.state_ver}
                drift = seal.check(token, fresh2) if mode == "C" else "OK"
                if drift != "OK":
                    conn.execute("ROLLBACK")
                    _record_void(engine, rec, d, drift, _describe(rec, m.effect, pol))
                    _requeue(engine, rec, d)
                    return d
                if mode == "C" and p["action"] in {a for b in pol.model.budgets.values() for a in [b.get("action")]}:
                    bud = budgets.charge(conn, pol, p["agent"], p["action"], m.effect.amount_minor)
                    if bud["exceeded"] and d.verdict == "ALLOW":
                        conn.execute("ROLLBACK")
                        d.status, d.verdict, d.rule = "pending", "HOLD", "R08"
                        d.reason = "cumulative budget exceeded at execution"
                        d.approvals_needed = max(1, d.approvals_needed)
                        engine.save_decision(d)
                        return d
                if mode != "A":
                    conn.execute("INSERT INTO used_seals (nonce, decision_id, ts) VALUES (?,?,?)",
                                 (token["nonce"], d.id, int(clock.now())))
                conn.execute("COMMIT")
            except Exception:
                try:
                    conn.execute("ROLLBACK")
                except Exception:
                    pass
                raise
        finally:
            conn.close()
        seal.mark_used(engine.state, d.id)
        d.status = "done"
        d.drift = None
        engine.save_decision(d)
        audit.append(engine.state, int(clock.now()), d.agent, d.action,
                     {"decision_id": d.id, "executed": True, "effect_hash": token["effect_hash"],
                      "rows": {t: len(v) for t, v in m.effect.rows.items()}, "approvers": token["approvers"]},
                     "DONE", "R6", d.decision_path, pol.hash)
        engine.emit("execution", d.id, status="done", rows={t: len(v) for t, v in m.effect.rows.items()},
                    agent=d.agent, action=d.action)
        return d


def _describe(rec: dict, fresh_effect, pol) -> str:
    old = rec["decision"].effect
    if not old:
        return ""
    primary = pol.action_def(old.action_type).get("primary_table")
    a = len(old.rows.get(primary, [])) if primary else sum(len(v) for v in old.rows.values())
    b = len(fresh_effect.rows.get(primary, [])) if primary else sum(len(v) for v in fresh_effect.rows.values())
    return f"{a} -> {b} rows" if a != b else ""
