"""Paired attack-suite runner (Milestone 9.1). Every attack and its benign twin run in modes A, B and C, each on a
freshly seeded database. Results are reported exactly as produced, including misses."""
import copy
import datetime
import json
import pathlib
import shutil
import subprocess
import tempfile
import time
import uuid

import yaml

from agents import tools
from gateway import ai, approvals, budgets
from gateway.approvals import GateError
from gateway.engine import Engine
from gateway.policy_loader import Policy, load_users

ROOT = pathlib.Path(__file__).resolve().parent.parent
SUITE = ROOT / "lab" / "suite.yaml"
STOPPED = ("BLOCK", "HOLD", "REFUSED", "STRUCTURAL")
MODES = ("A", "B", "C")
APPROVER_ORDER = ["priya", "rahul", "anita"]


def load_suite(path=None) -> list[dict]:
    return yaml.safe_load(pathlib.Path(path or SUITE).read_text(encoding="utf-8"))


def stopped(outcome: str) -> bool:
    return outcome in STOPPED or outcome.startswith("VOID")


def benign_ok(outcome: str) -> bool:
    return not (outcome in ("BLOCK", "REFUSED", "FAIL") or outcome.startswith("VOID") or outcome.startswith("FAIL"))


class Workspace:
    """Seeds each domain once and hands out fresh copies, so every case starts from identical data."""

    def __init__(self):
        self.root = pathlib.Path(tempfile.mkdtemp(prefix="sealgate-lab-"))
        self.templates: dict[str, pathlib.Path] = {}

    def template(self, domain: str) -> pathlib.Path:
        if domain not in self.templates:
            import importlib
            mod = importlib.import_module(f"gateway.seed.{domain}_seed")
            self.templates[domain] = mod.seed(self.root / f"template-{domain}.db")
        return self.templates[domain]

    def engine(self, domain: str, mode: str) -> Engine:
        d = self.root / f"run-{uuid.uuid4().hex[:8]}"
        d.mkdir()
        from gateway.policy_loader import load as load_policy
        pol = load_policy(domain)
        shutil.copy(self.template(domain), d / pol.model.db)
        return Engine(domain, data_dir=d, policy=pol, mode=mode)

    def cleanup(self):
        shutil.rmtree(self.root, ignore_errors=True)


# ---------------------------------------------------------------------------------------------------------
def make_proposal(agent, action, args, user_instruction="", on_behalf_of="", intent="", tamper=False) -> dict:
    import os
    body = {"agent": agent, "action": action, "args": copy.deepcopy(args), "intent": intent,
            "user_instruction": user_instruction, "on_behalf_of": on_behalf_of, "nonce": uuid.uuid4().hex,
            "ts": int(time.time())}
    key = os.environ.get("AGENT_KEY_" + agent.upper().replace("-", "_"), "")
    body["sig"] = tools.sign(key, body) if key else "unsigned"
    if tamper:
        body["args"] = dict(body["args"], customer="C-9999")
    return body


def propose(engine, spec: dict, **over):
    return engine.propose(make_proposal(spec["agent"], spec["action"], spec.get("args", {}),
                                        spec.get("user_instruction", ""), spec.get("on_behalf_of", ""),
                                        tamper=spec.get("tamper") == "args_after_signing", **over))


def requester_of(engine, decision_id: str) -> str:
    return engine.get_record(decision_id)["requester"]


def approve_fully(engine, d):
    """Approve with as many distinct, authorised, non-requester users as the decision needs."""
    users = load_users()
    req = requester_of(engine, d.id)
    for name in APPROVER_ORDER:
        if name == req:
            continue
        cur = engine.get_decision(d.id)
        if cur.status != "pending":
            break
        approvals.approve(engine, {"id": name, **users[name]}, d.id)
    return engine.get_decision(d.id)


def mutate(engine, d, mutation: str):
    rec = engine.get_record(d.id)
    if mutation == "insert_invoices":
        engine.demo_insert_invoices()
    elif mutation == "rewrite_args_customer":
        p = rec["proposal"]
        p["args"]["customer"] = "C-2210"
        engine.state.execute("UPDATE decisions SET proposal_json=? WHERE id=?", (json.dumps(p), d.id))
    elif mutation == "rewrite_args_amount":
        p = rec["proposal"]
        p["args"].pop("vendor", None)
        engine.state.execute("UPDATE decisions SET proposal_json=? WHERE id=?", (json.dumps(p), d.id))
    elif mutation == "change_policy":
        raw = copy.deepcopy(engine.policy.raw)
        raw["envelopes"]["transfer"]["max_amount"] = 12345
        engine.policy = Policy(raw)
    elif mutation == "relabel_column":
        raw = copy.deepcopy(engine.policy.raw)
        raw["labels"]["invoices.*"] = "PII"
        engine.policy = Policy(raw)


def outcome_of_execute(out) -> str:
    return f"VOID:{out.drift}" if out.verdict == "VOID" else "ALLOW"


def run_spec(engine: Engine, case: dict, spec: dict) -> str:
    kind = case["kind"]
    if kind == "structural":
        if spec["check"] == "agents_have_no_db_path":
            bad = [f for f in (ROOT / "agents").rglob("*.py")
                   if any(x in f.read_text().lower() for x in ("sqlite", ".db"))]
            return "FAIL:agent-has-db-path" if bad else "STRUCTURAL"
        return "STRUCTURAL" if engine.real_path.exists() else "FAIL:gateway-has-no-db"
    if kind == "stream":
        return run_stream(engine, spec)
    if spec.get("touched_pii"):
        engine.record_touched(spec["agent"], ["PII"])
    if "steps" in spec:
        d = None
        for st in spec["steps"]:
            d = propose(engine, dict(st, user_instruction=spec.get("user_instruction", "")))
        return d.verdict
    if kind == "single":
        return propose(engine, spec).verdict
    if kind == "ai_garbage":
        ai.STATE["force"] = "garbage"
        try:
            d = propose(engine, spec)
        finally:
            ai.STATE["force"] = None
        return d.verdict if (d.verdict == "ALLOW" or d.decision_path == "fallback") else "FAIL:ai-path"
    if kind == "self_approval":
        d = propose(engine, spec)
        if d.verdict != "HOLD":
            return d.verdict
        users = load_users()
        who = spec["approver"]
        try:
            approvals.approve(engine, {"id": who, **users[who]}, d.id)
        except GateError:
            return "REFUSED"
        return "HOLD" if who != requester_of(engine, d.id) else "ALLOW"
    # approval-gap kinds: defer execution so the world can change between approval and execution
    engine.auto_execute = False
    d = propose(engine, spec)
    if d.verdict == "BLOCK":
        return "BLOCK"
    if d.verdict == "HOLD":
        d = approve_fully(engine, d)
        if d.status != "approved":
            return "HOLD"
    if kind == "approve_then_mutate":
        if spec.get("mutation", case.get("mutation")) not in (None, "none"):
            mutate(engine, d, spec.get("mutation", case.get("mutation")))
        return outcome_of_execute(engine.execute(d.id))
    if kind == "double_execute":
        first = engine.execute(d.id)
        if first.verdict == "VOID":
            return outcome_of_execute(first)
        if spec.get("executions", 2) == 1:
            return "ALLOW"
        return outcome_of_execute(engine.execute(d.id))
    return d.verdict


def run_stream(engine: Engine, spec: dict) -> str:
    """Synthetic stream of identical small refunds charged on the budget ledger (the same code C uses for R08)."""
    if engine.mode != "C":
        return "ALLOW"
    agents = spec.get("agents") or [spec["agent"]]
    conn = engine.real_conn()
    try:
        for i in range(spec["count"]):
            res = budgets.check_and_charge_atomic(conn, engine.policy, agents[i % len(agents)], spec["action"],
                                                  spec["amount_minor"])
            if res["exceeded"]:
                return "HOLD"
    finally:
        conn.close()
    return "ALLOW"


def run_case(ws: Workspace, case: dict, mode: str) -> dict:
    domain = case["domain"] if case["domain"] in ("bank", "hospital", "shop") else "bank"
    res = {}
    for part in ("attack", "twin"):
        eng = ws.engine(domain, mode)
        try:
            res[part] = run_spec(eng, case, case[part])
        except Exception as e:                    # a crash must never look like a pass
            res[part] = f"FAIL:{type(e).__name__}"
    return res


def suite_commit() -> dict:
    try:
        out = subprocess.run(["git", "log", "-1", "--format=%H|%cI", "--", "lab/suite.yaml"], cwd=ROOT,
                             capture_output=True, text=True, timeout=5).stdout.strip()
        h, _, t = out.partition("|")
        return {"hash": h or "uncommitted", "time": t}
    except Exception:
        return {"hash": "unknown", "time": ""}


def run_suite(modes=MODES, cases=None, save: bool = True, with_ai: bool = False) -> dict:
    """Deterministic by default: the live AI is switched off for the run unless `with_ai` is set (slower, can vary)."""
    suite = cases if cases is not None else load_suite()
    ws = Workspace()
    started = time.time()
    previous = ai.STATE["force"]
    ai.STATE["force"] = None if with_ai else "off"
    try:
        rows = []
        for case in suite:
            row = {"id": case["id"], "domain": case["domain"], "title": case.get("title", ""), "kind": case["kind"],
                   "expected": {"A": case.get("expect_A"), "B": case.get("expect_B"), "C": case.get("expect_C"),
                                "twin_C": case.get("twin_expect_C")}}
            for m in modes:
                row[m] = run_case(ws, case, m)
            rows.append(row)
    finally:
        ai.STATE["force"] = previous
        ws.cleanup()
    summary = {}
    for m in modes:
        summary[m] = {"attacks_stopped": sum(stopped(r[m]["attack"]) for r in rows), "attacks_total": len(rows),
                      "benign_allowed": sum(benign_ok(r[m]["twin"]) for r in rows), "benign_total": len(rows)}
    misses = []
    if "C" in modes:
        for r in rows:
            if not stopped(r["C"]["attack"]):
                misses.append({"id": r["id"], "title": r["title"], "what": "attack not stopped in mode C",
                               "outcome": r["C"]["attack"]})
            elif r["C"]["attack"] != r["expected"]["C"]:
                misses.append({"id": r["id"], "title": r["title"], "what": "outcome differs from pre-registered expectation",
                               "outcome": r["C"]["attack"], "expected": r["expected"]["C"]})
            if not benign_ok(r["C"]["twin"]):
                misses.append({"id": r["id"], "title": r["title"], "what": "benign twin wrongly stopped in mode C",
                               "outcome": r["C"]["twin"]})
            elif r["C"]["twin"] != r["expected"]["twin_C"]:
                misses.append({"id": r["id"], "title": r["title"], "what": "twin outcome differs from expectation",
                               "outcome": r["C"]["twin"], "expected": r["expected"]["twin_C"]})
    result = {"suite_commit": suite_commit(), "ran_at": datetime.datetime.now().isoformat(timespec="seconds"),
              "seconds": round(time.time() - started, 1), "ai": "live" if with_ai else "off", "summary": summary, "cases": rows, "misses": misses,
              "known_limits": ["data moved through channels the gateway never sees", "PII paraphrased into free text is best-effort"]}
    if save:
        out = ROOT / "lab" / f"results_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        out.write_text(json.dumps(result, indent=2), encoding="utf-8")
        result["file"] = out.name
    return result


def run_custom(custom: dict) -> dict:
    """'Add your own case': one attack run in all three modes. Keys: domain, agent, action, args, user_instruction."""
    case = {"id": "CUSTOM", "domain": custom.get("domain", "bank"), "kind": "single", "title": "custom case",
            "attack": {k: custom.get(k, "") for k in ("agent", "action", "args", "user_instruction", "on_behalf_of")},
            "twin": {"agent": custom.get("agent", ""), "action": "lookup", "args": {}}}
    case["attack"]["args"] = custom.get("args") or {}
    ws = Workspace()
    previous = ai.STATE["force"]
    ai.STATE["force"] = None if custom.get("ai") == "on" else "off"
    try:
        return {m: run_spec(ws.engine(case["domain"], m), case, case["attack"]) for m in MODES}
    finally:
        ai.STATE["force"] = previous
        ws.cleanup()


if __name__ == "__main__":
    out = run_suite()
    print(json.dumps(out["summary"], indent=2))
    for m in out["misses"]:
        print("MISS", m)
