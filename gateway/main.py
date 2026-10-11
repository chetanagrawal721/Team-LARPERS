from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from . import audit, config
from .engine import Engine

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


@app.get("/health")
def health():
    return {"status": "ok", "domain": CURRENT["domain"]}


@app.post("/propose")
def propose(body: dict):
    try:
        return engine().propose(body)
    except ValidationError as e:
        raise HTTPException(422, detail=e.errors(include_url=False, include_context=False, include_input=False))


@app.get("/audit")
def get_audit(limit: int = 200):
    return audit.entries(engine().state, limit)


@app.post("/audit/verify")
def audit_verify():
    return audit.verify(engine().state)


@app.post("/policy/reload")
def policy_reload():
    return {"policy_hash": engine().reload_policy()}
