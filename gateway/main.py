import os
import subprocess
import sys

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from . import ai, approvals, audit, config, outbox, replay, safe_version, shadow
from .approvals import GateError
from .engine import Engine
from .events import Bus
from .schemas import ApprovalRequest, Event

app = FastAPI(title="SEALGATE")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"],
                   allow_methods=["*"], allow_headers=["*"])

ENGINES: dict[str, Engine] = {}
CURRENT = {"domain": "bank"}
BUS = Bus()


def engine() -> Engine:
    d = CURRENT["domain"]
    if d not in ENGINES:
        ENGINES[d] = Engine(d)
    ENGINES[d].bus = BUS
    return ENGINES[d]


@app.exception_handler(GateError)
async def gate_error(_, exc: GateError):
    from fastapi.responses import JSONResponse
    return JSONResponse(status_code=exc.status, content={"detail": exc.message})


def human(x_user: str | None, x_token: str | None) -> dict:
    return approvals.authenticate(x_user, x_token)


@app.on_event("startup")
def _startup():
    outbox.start_worker(lambda: ENGINES.values())


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


@app.get("/agents")
def agents():
    e = engine()
    return [{"agent": a, "frozen": e.is_frozen(a)} for a in e.policy.agents]


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
async def events(request: Request, last_event_id: str | None = Header(None)):
    engine()
    start = int(last_event_id) if last_event_id and last_event_id.isdigit() else 0
    return StreamingResponse(BUS.stream(last_id=start), media_type="text/event-stream",
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
    env = {k: v for k, v in os.environ.items() if k.startswith("AGENT_KEY_") or k in ("PATH", "SYSTEMROOT", "TEMP", "TMP")}
    env["GATEWAY_URL"] = os.environ.get("PUBLIC_GATEWAY_URL", "http://127.0.0.1:8000")
    args = [sys.executable, "-m", "agents.run", name] + (["--text", text] if text else [])
    p = subprocess.Popen(args, cwd=str(config.ROOT), env=env)
    return {"started": name, "pid": p.pid, "domain": want}


@app.post("/demo/chat")
def demo_chat(body: dict):
    from agents import scenarios
    text = str(body.get("text", ""))[:500]
    name, _ = scenarios.from_text(text)
    if not name:
        BUS.publish(Event(type="chat", ts=0, data={"from": "gate", "agent": "", "text": "I can only run the demo requests: refunds, contact updates, vendor changes, invoice payments, reports and mailings."}))
        return {"started": None}
    return _spawn(name, text)


@app.post("/demo/{scenario}")
def demo_scenario(scenario: str):
    return _spawn(scenario)


LAB = {"last": None}


@app.post("/lab/run")
def lab_run(mode: str = "ALL"):
    from lab import runner
    modes = runner.MODES if mode.upper() == "ALL" else tuple(m for m in mode.upper() if m in runner.MODES)
    if not modes:
        raise HTTPException(422, "mode must be A, B, C or ALL")
    LAB["last"] = runner.run_suite(modes=modes)
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
