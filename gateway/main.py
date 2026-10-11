from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from . import ai, approvals, audit, outbox
from .approvals import GateError
from .engine import Engine
from .schemas import ApprovalRequest

app = FastAPI(title="SEALGATE")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"],
                   allow_methods=["*"], allow_headers=["*"])

ENGINES: dict[str, Engine] = {}
CURRENT = {"domain": "bank"}


def engine() -> Engine:
    d = CURRENT["domain"]
    if d not in ENGINES:
        ENGINES[d] = Engine(d)
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
