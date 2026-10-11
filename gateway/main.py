import os
import subprocess
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from . import ai, approvals, audit, config, outbox, replay, safe_version, shadow
from .approvals import GateError
from .engine import Engine
from .events import Bus
from .schemas import ApprovalRequest, Event

@asynccontextmanager
async def lifespan(_):
    outbox.start_worker(lambda: ENGINES.values())
    yield


app = FastAPI(title="SEALGATE", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"],
                   allow_methods=["*"], allow_headers=["*"])

ENGINES: dict[str, Engine] = {}
CURRENT = {"domain": "bank"}
BUS = Bus()


def get_engine(d: str) -> Engine:
    if d not in ENGINES:
        ENGINES[d] = Engine(d)
    ENGINES[d].bus = BUS
    return ENGINES[d]


def engine() -> Engine:
    return get_engine(CURRENT["domain"])


@app.exception_handler(GateError)
async def gate_error(_, exc: GateError):
    from fastapi.responses import JSONResponse
    return JSONResponse(status_code=exc.status, content={"detail": exc.message})


def human(x_user: str | None, x_token: str | None) -> dict:
    return approvals.authenticate(x_user, x_token)


@app.get("/health")
def health():
    return {"status": "ok", "domain": CURRENT["domain"]}


@app.post("/propose")
def propose(body: dict):
    try:
        return engine().propose(body)
    except ValidationError as e:
        raise HTTPException(422, detail=e.errors(include_url=False, include_context=False, include_input=False))


@app.get("/status/{decision_id}")
def status(decision_id: str):
    d = engine().get_decision(decision_id)
    if not d:
        raise HTTPException(404, "no such decision")
    return d


@app.get("/actions")
def actions(limit: int = 50):
    return engine().list_decisions(limit)


@app.get("/action/{decision_id}")
def action(decision_id: str):
    d = engine().get_decision(decision_id)
    if not d:
        raise HTTPException(404, "no such decision")
    return d


@app.post("/approve")
def approve(req: ApprovalRequest, x_user: str | None = Header(None), x_token: str | None = Header(None)):
    return approvals.approve(engine(), human(x_user, x_token), req.decision_id, req.note)


@app.post("/reject")
def reject(req: ApprovalRequest, x_user: str | None = Header(None), x_token: str | None = Header(None)):
    return approvals.reject(engine(), human(x_user, x_token), req.decision_id, req.note)


@app.post("/execute/{decision_id}")
def execute(decision_id: str, x_user: str | None = Header(None), x_token: str | None = Header(None)):
    human(x_user, x_token)
    return engine().execute(decision_id)


@app.post("/demo/insert-invoices")
def demo_insert_invoices():
    return {"inserted": engine().demo_insert_invoices()}


@app.get("/audit")
def get_audit(limit: int = 200):
    return audit.entries(engine().state, limit)


@app.post("/audit/verify")
def audit_verify():
    return audit.verify(engine().state)


@app.post("/policy/reload")
def policy_reload():
    return {"policy_hash": engine().reload_policy()}


@app.post("/ai/toggle")
def ai_toggle(enabled: bool | None = None):
    new = (not ai.enabled()) if enabled is None else enabled
    ai.set_enabled(new)
    return {"enabled": ai.enabled(), "provider": ai.provider()}


@app.get("/ai/status")
def ai_status():
    return {"enabled": ai.enabled(), "provider": ai.provider(), "available": ai.available()}


@app.post("/safe-version/{decision_id}")
def accept_safe_version(decision_id: str, x_user: str | None = Header(None), x_token: str | None = Header(None)):
    return safe_version.accept(engine(), human(x_user, x_token), decision_id)


@app.get("/shadow/{sid}")
def shadow_view(sid: str):
    return shadow.view(engine(), sid)


@app.post("/promote/{sid}")
def shadow_promote(sid: str, x_user: str | None = Header(None), x_token: str | None = Header(None)):
    return shadow.promote(engine(), human(x_user, x_token), sid)


@app.post("/discard/{sid}")
def shadow_discard(sid: str, x_user: str | None = Header(None), x_token: str | None = Header(None)):
    return shadow.discard(engine(), human(x_user, x_token), sid)


@app.post("/audit/replay/{seq}")
def audit_replay(seq: int):
    return replay.replay(engine(), seq)


@app.post("/agents/{agent}/unfreeze")
def agent_unfreeze(agent: str, x_user: str | None = Header(None), x_token: str | None = Header(None)):
    u = human(x_user, x_token)
    if not u.get("can_approve"):
        raise GateError(403, "user is not authorised")
    engine().unfreeze(agent)
    return {"agent": agent, "frozen": False}




@app.post("/domain/{name}")
def switch_domain(name: str):
    if name not in config.DOMAINS:
        raise HTTPException(404, "unknown domain")
    CURRENT["domain"] = name
    e = engine()
    e.emit("domain", None, domain=name, org=e.policy.org)
    return {"domain": name, "org": e.policy.org, "policy_hash": e.policy.hash}


@app.get("/domain")
def current_domain():
    e = engine()
    return {"domain": CURRENT["domain"], "org": e.policy.org, "policy_hash": e.policy.hash,
            "domains": list(config.DOMAINS)}


@app.get("/events")
async def events(request: Request, replay: int = 0, last_event_id: str | None = Header(None)):
    engine()
    start = int(last_event_id) if last_event_id and last_event_id.isdigit() else 0
    return StreamingResponse(BUS.stream(replay=min(max(replay, 0), 200), last_id=start), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.post("/chat")
def chat(body: dict):
    """Agents post their chat lines here; the dashboard receives them as events."""
    BUS.publish(Event(type="chat", ts=int(__import__("time").time()),
                      data={"from": str(body.get("from", "agent")), "agent": str(body.get("agent", "")),
                            "text": str(body.get("text", ""))[:2000]}))
    return {"ok": True}


def _spawn(name: str, text: str | None = None) -> dict:
    """Start a scripted scenario as a separate process that holds only agent signing keys."""
    from agents import scenarios
    if name not in scenarios.SCENARIOS:
        raise HTTPException(404, "unknown scenario")
    want = scenarios.DOMAIN_OF[name]
    if CURRENT["domain"] != want:
        switch_domain(want)
    env = _agent_env()
    args = [sys.executable, "-m", "agents.run", name] + (["--text", text] if text else [])
    p = subprocess.Popen(args, cwd=str(config.ROOT), env=env)
    return {"started": name, "pid": p.pid, "domain": want}


AGENT = {"mode": None}      # None = decide from configuration; "llm" or "scripted"


def _llm_configured() -> bool:
    return os.environ.get("AI_PROVIDER", "none").lower() in ("openrouter", "gemini", "ollama") and bool(os.environ.get("AI_MODEL"))


def _agent_mode() -> str:
    return AGENT["mode"] or ("llm" if _llm_configured() else "scripted")


def _agent_env() -> dict:
    """The agent process gets its signing keys and its own model credentials, nothing of the gateway's."""
    keep = ("PATH", "SYSTEMROOT", "TEMP", "TMP", "AI_PROVIDER", "AI_MODEL", "AI_API_KEY", "AI_TIMEOUT_SECONDS", "OLLAMA_URL")
    env = {k: v for k, v in os.environ.items() if k.startswith("AGENT_KEY_") or k in keep}
    env["GATEWAY_URL"] = os.environ.get("PUBLIC_GATEWAY_URL", "http://127.0.0.1:8000")
    return env


@app.get("/agent/mode")
def agent_mode_get():
    return {"mode": _agent_mode(), "llm_configured": _llm_configured(), "provider": os.environ.get("AI_PROVIDER", "none"),
            "model": os.environ.get("AI_MODEL", "")}


@app.post("/agent/mode")
def agent_mode_set(body: dict):
    m = str(body.get("mode", ""))
    if m not in ("llm", "scripted"):
        raise HTTPException(422, "mode must be 'llm' or 'scripted'")
    AGENT["mode"] = m
    return agent_mode_get()


@app.post("/agent/step")
def agent_step(body: dict):
    """The live agent reports each step (prompts, model replies, thoughts, tool calls) here for the live feed."""
    BUS.publish(Event(type="agent", ts=int(__import__("time").time()),
                      data={"run": str(body.get("run", ""))[:40], "kind": str(body.get("kind", ""))[:30],
                            "text": str(body.get("text", ""))[:6000], "data": body.get("data") or {}}))
    return {"ok": True}


@app.post("/demo/chat")
def demo_chat(body: dict):
    """Every typed request goes to the live language-model agent; the keyword router is only the scripted-mode fallback."""
    from agents import scenarios
    text = str(body.get("text", ""))[:1000].strip()
    if not text:
        raise HTTPException(422, "empty request")
    if _agent_mode() == "llm":
        p = subprocess.Popen([sys.executable, "-m", "agents.llm_agent", "--domain", CURRENT["domain"], "--text", text],
                             cwd=str(config.ROOT), env=_agent_env())
        return {"started": "llm-agent", "pid": p.pid, "domain": CURRENT["domain"], "mode": "llm"}
    name, _ = scenarios.from_text(text)
    if not name:
        BUS.publish(Event(type="chat", ts=0, data={"from": "gate", "agent": "", "text": "Scripted mode only understands refunds, contact updates, vendor changes, invoice payments, reports and mailings. Switch the agent to Live LLM to ask anything."}))
        return {"started": None, "mode": "scripted"}
    return _spawn(name, text)


LAB = {"last": None}


@app.post("/lab/run")
def lab_run(mode: str = "ALL", ai_checks: bool = False):
    from lab import runner
    modes = runner.MODES if mode.upper() == "ALL" else tuple(m for m in mode.upper() if m in runner.MODES)
    if not modes:
        raise HTTPException(422, "mode must be A, B, C or ALL")
    LAB["last"] = runner.run_suite(modes=modes, with_ai=ai_checks)
    return LAB["last"]


@app.get("/lab/last")
def lab_last():
    return LAB["last"] or {"summary": None}


@app.get("/lab/suite")
def lab_suite():
    from lab import runner
    return {"commit": runner.suite_commit(), "cases": runner.load_suite()}


@app.post("/lab/case")
def lab_case(body: dict):
    from lab import runner
    return runner.run_custom(body)


@app.post("/demo/reset")
def demo_reset():
    """Restore the initial demo state: fresh fictional data and an empty audit log for every domain."""
    from . import reset
    for e in ENGINES.values():
        e.close()
    ENGINES.clear()
    reset.reset_all(config.DATA_DIR)
    BUS.history.clear()
    CURRENT["domain"] = "bank"
    return {"reset": list(config.DOMAINS)}



# ---------------------------------------------------------------------------------------------- read-only views
@app.get("/orgs")
def orgs():
    out = []
    for d in config.DOMAINS:
        e = get_engine(d)
        out.append({"domain": d, "org": e.policy.org, "version": e.policy_version_number(), "hash": e.policy.hash,
                    "verified": True, "current": d == CURRENT["domain"]})
    return out


@app.get("/policy")
def policy_view(domain: str | None = None):
    import datetime
    e = get_engine(domain or CURRENT["domain"])
    pol, path = e.policy, config.POLICY_DIR / f"{(domain or CURRENT['domain'])}.yaml"
    m = pol.model
    return {"domain": pol.domain, "org": pol.org, "version": e.policy_version_number(), "hash": pol.hash,
            "updated": datetime.datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="minutes"),
            "yaml": path.read_text(encoding="utf-8"),
            "limits": {"envelopes": m.envelopes, "tiers": m.tiers, "protected": m.protected,
                       "tier_overrides": m.tier_overrides, "shadow_mode": m.shadow_mode},
            "labels": {"labels": m.labels, "destinations": m.destinations, "catalog_version": pol.label_catalog_ver},
            "budgets": m.budgets,
            "counts": {"labels": len(m.labels), "envelopes": len(m.envelopes), "budgets": len(m.budgets),
                       "agents": len(m.agents), "protected": len(m.protected)}}


@app.get("/agents")
def agents_view():
    """Every registered agent across the organisations, with live status and budget use."""
    from . import budgets, shadow as shadow_mod
    from . import clock
    out = []
    for d in config.DOMAINS:
        e = get_engine(d)
        conn = e.real_conn()
        try:
            for name, cfg in e.policy.agents.items():
                status = "FROZEN" if e.is_frozen(name) else ("SHADOW" if shadow_mod.active_session(e, name) else "ACTIVE")
                pct = 0
                for act in cfg.get("actions", []):
                    for _, key, limit in budgets.keys_for(e.policy, name, act):
                        pct = max(pct, round(100 * budgets.used(conn, key, clock.now()) / limit))
                out.append({"agent": name, "domain": d, "org": e.policy.org, "actions": cfg.get("actions", []),
                            "acts_for": cfg.get("acts_for", ""), "status": status, "budget_pct": min(pct, 100)})
        finally:
            conn.close()
    return out


@app.get("/sheet/{decision_id}")
def approval_sheet(decision_id: str):
    """Everything an approver needs to see on the approval sheet, assembled by the gateway (never by the agent)."""
    from .policy_loader import load_users
    e = engine()
    rec = e.get_record(decision_id)
    if not rec:
        raise HTTPException(404, "no such decision")
    users = load_users()
    req = rec["requester"]
    ttl = int(e.policy.model.tiers.get("approval_ttl_seconds", 900))
    d = rec["decision"]
    return {"decision": d, "requester": req, "requester_name": users.get(req, {}).get("name", req),
            "requester_role": users.get(req, {}).get("roles", {}).get(e.domain, ""),
            "expires_ts": d.created_ts + ttl, "ttl_seconds": ttl, "args": rec["proposal"].get("args", {}),
            "instruction": rec["proposal"].get("user_instruction", "")}


@app.get("/audit/{seq}/evidence")
def audit_evidence(seq: int):
    from . import evidence
    return evidence.build(engine(), seq)


@app.post("/demo/{scenario}")
def demo_scenario(scenario: str):
    return _spawn(scenario)
