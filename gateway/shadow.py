"""Shadow Mode (S2): a held, suspicious agent keeps working against a sandbox. Its actions are recorded and a human
reviews the *total* diff once, then promotes (replay on the real DB, real diff must equal sandbox diff) or discards."""
import json
import uuid

from . import audit, clock, resolver, resolvers, sandbox
from .approvals import GateError
from .resolver import Ctx, snapshot
from .seed.common import connect

TIER_RANK = {"T0": 0, "T1": 1, "T2": 2, "T3": 3}


def _cfg(engine) -> dict:
    return engine.policy.model.shadow_mode or {}


def active_session(engine, agent: str):
    return engine.state.execute("SELECT * FROM shadow_sessions WHERE agent=? AND status='active'", (agent,)).fetchone()


def _work_path(engine, sid: str):
    return engine.scratch / f"{sid}.db"


def _base_path(engine, sid: str):
    return engine.scratch / f"{sid}.base.db"


def _snap_all(conn, tables) -> dict:
    return {t: snapshot(conn, t) for t in tables}


def diff_rows(before: dict, after: dict) -> dict:
    """{table: {pk: (op, row-after)}} for rows that differ between two snapshots."""
    out: dict = {}
    for t in after:
        b, a = before.get(t, {}), after[t]
        for pk in sorted(a.keys() - b.keys()):
            out.setdefault(t, {})[pk] = ("added", a[pk])
        for pk in sorted(b.keys() - a.keys()):
            out.setdefault(t, {})[pk] = ("removed", None)
        for pk in sorted(k for k in a.keys() & b.keys() if a[k] != b[k]):
            out.setdefault(t, {})[pk] = ("modified", a[pk])
    return out


def _jsonable(diff: dict) -> dict:
    return {t: {pk: [op, row] for pk, (op, row) in rows.items()} for t, rows in diff.items()}


def _create(engine, d, human: str) -> str:
    sid = "S-" + uuid.uuid4().hex[:8]
    sandbox.copy(engine.real_path, engine.scratch, name=f"{sid}.base.db")
    sandbox.copy(engine.real_path, engine.scratch, name=f"{sid}.db")
    engine.state.execute(
        "INSERT INTO shadow_sessions (id, agent, requester, status, reason, db_path, trigger_decision, created_ts, base_hash)"
        " VALUES (?,?,?,?,?,?,?,?,?)",
        (sid, d.agent, human, "active", f"{d.rule}: {d.reason}", str(_work_path(engine, sid)), d.id,
         int(clock.now()), ""))
    audit.append(engine.state, int(clock.now()), d.agent, "shadow_start",
                 {"session": sid, "trigger": d.id, "rule": d.rule}, "HOLD", d.rule, d.decision_path,
                 engine.policy.hash)
    engine.emit("shadow", d.id, session=sid, event="started", agent=d.agent)
    return sid


def route(engine, d, p, human: str, inp: dict, measured) -> bool:
    """Called after a decision is made. Returns True when the action was diverted into a shadow session."""
    sess = active_session(engine, p.agent)
    cfg = _cfg(engine)
    if sess is None:
        if not (cfg.get("on_hold") and d.verdict == "HOLD" and d.rule in cfg.get("rules", ["R07"])):
            return False
        sid = _create(engine, d, human)
        trigger = True
    else:
        if d.verdict == "BLOCK" or measured is None:
            return False
        sid, trigger = sess["id"], False
    _record_step(engine, sid, d, p, human, measured)
    d.shadow_session = sid
    d.status = "shadow"
    if not trigger:
        d.verdict = "ALLOW"       # the held agent is not told; its work simply continues in the sandbox
    engine.save_decision(d)
    return True


def _record_step(engine, sid: str, d, p, human: str, measured) -> None:
    now = int(clock.now())
    conn = connect(_work_path(engine, sid))
    try:
        res = resolvers.get(engine.domain, p.action)
        conn.execute("BEGIN")
        m = resolver.measure(res, conn, p.args, Ctx(policy=engine.policy, agent=p.agent, human=human, now=now,
                                                    decision_id=d.id))
        conn.execute("COMMIT")
    finally:
        conn.close()
    seq = engine.state.execute("SELECT COUNT(*) FROM shadow_steps WHERE session_id=?", (sid,)).fetchone()[0] + 1
    engine.state.execute(
        "INSERT INTO shadow_steps (session_id, seq, action, args_json, effect_json, ts) VALUES (?,?,?,?,?,?)",
        (sid, seq, p.action, json.dumps(p.args, sort_keys=True),
         json.dumps({"effect": m.effect.model_dump(), "decision_id": d.id, "state_ver": m.state_ver, "now": now,
                     "tier": d.tier, "agent": p.agent, "human": human}, sort_keys=True, default=str), now))
    audit.append(engine.state, now, p.agent, "shadow_step",
                 {"session": sid, "seq": seq, "action": p.action, "decision_id": d.id}, "HOLD", "R07",
                 d.decision_path, engine.policy.hash)
    engine.emit("shadow", d.id, session=sid, event="step", seq=seq, action=p.action)


def _steps(engine, sid: str) -> list[dict]:
    out = []
    for r in engine.state.execute("SELECT * FROM shadow_steps WHERE session_id=? ORDER BY seq", (sid,)):
        x = json.loads(r["effect_json"])
        out.append({"seq": r["seq"], "action": r["action"], "args": json.loads(r["args_json"]), **x})
    return out


def _approvals(engine, sid: str) -> list[str]:
    return sorted({r["user"] for r in engine.state.execute(
        "SELECT user FROM approvals WHERE decision_id=? AND action='promote'", (sid,))})


def view(engine, sid: str) -> dict:
    s = engine.state.execute("SELECT * FROM shadow_sessions WHERE id=?", (sid,)).fetchone()
    if not s:
        raise GateError(404, "no such shadow session")
    steps = _steps(engine, sid)
    tables = engine.business_tables()
    diff = {}
    if s["status"] == "active":
        b, w = connect(_base_path(engine, sid)), connect(_work_path(engine, sid))
        try:
            diff = diff_rows(_snap_all(b, tables), _snap_all(w, tables))
        finally:
            b.close()
            w.close()
    needed = 2 if any(st["tier"] == "T3" for st in steps) else 1
    return {"id": sid, "agent": s["agent"], "requester": s["requester"], "status": s["status"], "reason": s["reason"],
            "trigger_decision": s["trigger_decision"], "steps": steps, "diff": _jsonable(diff),
            "totals": {"steps": len(steps), "amount_minor": sum(st["effect"]["amount_minor"] for st in steps),
                       "rows": sum(len(v) for t in diff.values() for v in [t])},
            "approvals": _approvals(engine, sid), "approvals_needed": needed}


def _finish_session(engine, sid: str, status: str, decision_status: str) -> None:
    engine.state.execute("UPDATE shadow_sessions SET status=? WHERE id=?", (status, sid))
    for st in _steps(engine, sid):
        dec = engine.get_decision(st["decision_id"])
        if dec:
            dec.status = decision_status
            engine.save_decision(dec)
    sandbox.cleanup(_work_path(engine, sid))
    sandbox.cleanup(_base_path(engine, sid))


def discard(engine, user: dict, sid: str) -> dict:
    with engine.lock:
        s = engine.state.execute("SELECT * FROM shadow_sessions WHERE id=?", (sid,)).fetchone()
        if not s:
            raise GateError(404, "no such shadow session")
        if s["status"] != "active":
            raise GateError(409, f"session is {s['status']}")
        if not user.get("can_approve"):
            raise GateError(403, "user is not authorised")
        _finish_session(engine, sid, "discarded", "rejected")
        audit.append(engine.state, int(clock.now()), user["id"], "shadow_discard", {"session": sid}, "BLOCK", "R07",
                     "rules-only", engine.policy.hash)
        engine.emit("shadow", None, session=sid, event="discarded")
        return {"id": sid, "status": "discarded"}


def promote(engine, user: dict, sid: str) -> dict:
    with engine.lock:
        s = engine.state.execute("SELECT * FROM shadow_sessions WHERE id=?", (sid,)).fetchone()
        if not s:
            raise GateError(404, "no such shadow session")
        if s["status"] != "active":
            raise GateError(409, f"session is {s['status']}")
        if user["id"] == s["requester"]:
            raise GateError(403, "requesters cannot approve their own requests")
        if not user.get("can_approve"):
            raise GateError(403, "user is not authorised to promote")
        if user["id"] not in _approvals(engine, sid):
            engine.state.execute("INSERT INTO approvals (decision_id, user, action, ts, note) VALUES (?,?,?,?,?)",
                                 (sid, user["id"], "promote", int(clock.now()), ""))
        v = view(engine, sid)
        if len(v["approvals"]) < v["approvals_needed"]:
            return {"id": sid, "status": "pending", "approvals": v["approvals"], "needed": v["approvals_needed"]}
        return _replay_on_real(engine, sid, s, v)


def _replay_on_real(engine, sid: str, s, v: dict) -> dict:
    tables = engine.business_tables()
    base, work = connect(_base_path(engine, sid)), connect(_work_path(engine, sid))
    try:
        sandbox_diff = diff_rows(_snap_all(base, tables), _snap_all(work, tables))
    finally:
        base.close()
        work.close()
    conn = engine.real_conn()
    drift = None
    try:
        conn.execute("BEGIN IMMEDIATE")
        before = _snap_all(conn, tables)
        for st in v["steps"]:
            res = resolvers.get(engine.domain, st["action"])
            m = resolver.measure(res, conn, st["args"], Ctx(policy=engine.policy, agent=st["agent"], human=st["human"],
                                                            now=st["now"], decision_id=st["decision_id"]))
            if m.state_ver != st["state_ver"]:
                drift = "state_drift"
                break
        if drift is None and diff_rows(before, _snap_all(conn, tables)) != sandbox_diff:
            drift = "effect_drift"
        if drift:
            conn.execute("ROLLBACK")
        else:
            conn.execute("COMMIT")
    except Exception:
        try:
            conn.execute("ROLLBACK")
        except Exception:
            pass
        raise
    finally:
        conn.close()
    now = int(clock.now())
    if drift:
        _finish_session(engine, sid, "void", "void")
        audit.append(engine.state, now, s["agent"], "shadow_promote", {"session": sid, "drift": drift}, "VOID", "R6",
                     "rules-only", engine.policy.hash)
        engine.emit("void", None, session=sid, drift=drift)
        return {"id": sid, "status": "void", "drift": drift}
    _finish_session(engine, sid, "promoted", "done")
    audit.append(engine.state, now, s["agent"], "shadow_promote",
                 {"session": sid, "steps": len(v["steps"]), "approvers": v["approvals"]}, "DONE", "R7", "rules-only",
                 engine.policy.hash)
    engine.emit("shadow", None, session=sid, event="promoted")
    return {"id": sid, "status": "promoted", "steps": len(v["steps"])}
