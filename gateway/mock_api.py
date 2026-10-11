"""Mock gateway returning fixed example responses, so frontend and agents can build against the contract."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .schemas import Decision, Effect, Envelope, EnvelopeCheck

app = FastAPI(title="SEALGATE (mock)")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"],
                   allow_methods=["*"], allow_headers=["*"])


def example_decision() -> Decision:
    return Decision(
        id="demo-1", verdict="BLOCK", rule="R06",
        reason="Refund touches 61 customers; request named 1",
        baseline_verdict="ALLOW", decision_path="rules+ai", status="blocked", tier="T2",
        agent="refund-agent", action="refund", agent_claim="refund 1 customer",
        effect=Effect(action_type="refund", rows={"refunds": [f"RF-{i}" for i in range(1, 4)]},
                      amount_minor=980000_00, reversible="compensating", labels=["INTERNAL"]),
        envelope=Envelope(scope={"customer": "C-1042", "month": "March"}, max_rows=5,
                          max_amount_minor=2000000, source="ai_from_instruction"),
        envelope_check=EnvelopeCheck(inside=False, reasons=["209 rows outside scope"]),
        safe_version={"description": "3 refunds, Rs 6,400", "args": {"customer": "C-1042", "month": "March"}},
        rules_fired=["R06"], policy_hash="0" * 64)


@app.get("/health")
def health():
    return {"status": "ok", "mock": True}


@app.post("/propose")
def propose() -> Decision:
    return example_decision()


@app.get("/status/{id}")
def status(id: str) -> Decision:
    return example_decision()


@app.get("/action/{id}")
def action(id: str) -> Decision:
    return example_decision()
