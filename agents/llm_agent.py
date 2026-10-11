"""The live agent: a language model that coordinates the specialist agents of one organisation.

Run as its own process (the gateway starts it): python -m agents.llm_agent --domain bank --text "..." [--attachment-file f]

Nothing here is scripted. The model reads the request (and any attached document), decides on a tool, and the agent that owns
the tool ASKS FOR ACCESS in the chat. Only after a person grants it is a signed proposal sent to the SEALGATE gateway, which
measures the real effect in a sandbox. Even an allowed action then waits for a person's approval. Every prompt, reply,
retry and decision is reported to the live feed."""
import argparse
import json
import os
import pathlib
import sys
import time
import uuid

import httpx

from . import config, llm, toolspec
from .tools import Agent

MAX_TURNS = 6
PROMPT_FILE = pathlib.Path(__file__).parent / "prompts" / "system.txt"
ORGS = {"bank": "Sahyadri Bank", "hospital": "Pune Care Hospital", "shop": "KartBazaar"}


def _wait_seconds(name: str, default: float) -> float:
    return float(os.environ.get(name, default))


class Run:
    def __init__(self, client, domain: str, text: str, run_id: str | None = None, attachment: str = ""):
        self.client, self.domain, self.text, self.attachment = client, domain, text, attachment
        self.id = run_id or "run-" + uuid.uuid4().hex[:8]

    def step(self, kind: str, text: str = "", **data) -> None:
        try:
            self.client.post("/agent/step", json={"run": self.id, "kind": kind, "text": text, "data": data})
        except httpx.HTTPError:
            pass

    def say(self, text: str, agent: str = "Assistant") -> None:
        try:
            self.client.post("/chat", json={"from": "agent", "agent": agent, "text": text, "run": self.id})
        except httpx.HTTPError:
            pass


def system_prompt(domain: str) -> str:
    ex_user, ex_reply = toolspec.EXAMPLES.get(domain, ('"hello"', "{}"))
    return PROMPT_FILE.read_text(encoding="utf-8").format(
        org=ORGS.get(domain, domain), roster=toolspec.roster(domain), tools=toolspec.render(domain),
        example_user=ex_user, example_reply=ex_reply)


def user_message(text: str, attachment: str) -> str:
    if not attachment.strip():
        return text
    return f"{text}\n\n----- ATTACHED CONTENT (pasted by the user) -----\n{attachment.strip()}\n----- END OF ATTACHED CONTENT -----"


def summarise(d: dict) -> dict:
    """What the model is told about a gateway verdict (the gateway's own words, no database content)."""
    e = d.get("effect") or {}
    rows = {t: len(v) for t, v in (e.get("rows") or {}).items()}
    out = {"verdict": d["verdict"], "status": d["status"], "rule": d["rule"], "reason": d["reason"],
           "measured_in_sandbox": {"rows_by_table": rows, "amount_rupees": (e.get("amount_minor") or 0) // 100,
                                   "recipients": len(e.get("recipients") or [])},
           "asked_for": (d.get("envelope") or {}).get("scope")}
    if d.get("safe_version"):
        out["safe_version"] = d["safe_version"]["description"]
    if d["status"] in ("pending", "approved"):
        out["needs_human_approvals"] = d.get("approvals_needed")
    return out


# ---------------------------------------------------------------------------------------- human gates
def request_access(run: Run, tool: dict, args: dict, intent: str, client, auto: bool) -> tuple[bool, str]:
    """The agent asks for access in the chat and waits for a person. Returns (granted, who or reason)."""
    agent = next((a for a in toolspec.AGENTS[run.domain] if a["id"] == tool["agent"]), {"name": tool["agent"]})
    body = {"run": run.id, "agent": tool["agent"], "agent_name": agent["name"], "tool": tool["name"], "action": tool["action"],
            "args": args, "intent": intent, "prompt": toolspec.agent_prompt(run.domain, tool["agent"]), "auto": auto}
    rid = client.post("/agent/access", json=body).json()["id"]
    run.step("access_wait", f"{agent['name']} is asking for access to run {tool['name']}. Waiting for a person to grant it.", access=rid)
    deadline = time.time() + _wait_seconds("AGENT_ACCESS_WAIT", 900)
    while time.time() < deadline:
        s = client.get(f"/agent/access/{rid}").json()
        if s["status"] == "granted":
            run.step("access_granted", f"{s.get('by', 'A person')} granted {agent['name']} access.", access=rid)
            return True, s.get("by", "")
        if s["status"] == "denied":
            run.step("access_denied", f"{s.get('by', 'A person')} denied {agent['name']} access.", access=rid)
            return False, s.get("by", "")
        time.sleep(1.0)
    run.step("access_timeout", "Nobody answered the access request in time.", access=rid)
    return False, "nobody answered in time"


def wait_for_human(run: Run, d: dict, client) -> dict:
    """After the gateway has measured the action, a person still decides. Poll until the decision is final."""
    if d["status"] not in ("pending", "approved"):
        return d
    run.say(f"Waiting for a person to decide on {d['id']} in the Live Gate (approve, reject or review the measured effect).", agent=d["agent"])
    run.step("waiting_human", f"Decision {d['id']} is waiting for a human approval.", decision=d["id"])
    deadline = time.time() + _wait_seconds("AGENT_DECISION_WAIT", 600)
    last = d["status"]
    while time.time() < deadline:
        time.sleep(1.5)
        cur = client.get(f"/status/{d['id']}").json()
        if cur["status"] != last:
            run.step("decision_update", f"Decision {d['id']} is now: {cur['status']}", decision=d["id"], status=cur["status"])
            last = cur["status"]
        if cur["status"] not in ("pending", "approved"):
            return cur
    run.step("waiting_human", "Still waiting for a person; the agent stops waiting here.", decision=d["id"])
    return d


def call_tool(run: Run, tool: dict, args: dict, intent: str, client, auto_access: bool) -> tuple[dict | None, dict]:
    """Validate, ask for access, propose to the gateway, and wait for the human decision. Returns (decision, result for the model)."""
    given = {k: v for k, v in (args or {}).items() if v not in (None, "")}
    clean = {k: v for k, v in given.items() if k in tool["params"]}
    source = run.text + "\n" + run.attachment
    problems = toolspec.validate(run.domain, tool, given, source)
    if problems:
        run.step("rejected_call", "The call was not sent: " + " ".join(problems), tool=tool["name"], args=clean)
        return None, {"error": "the call was not sent: " + " ".join(problems)}
    clean.update(tool.get("fixed", {}))
    agent_name = next((a["name"] for a in toolspec.AGENTS[run.domain] if a["id"] == tool["agent"]), tool["agent"])
    run.step("agent_active", f"{agent_name} takes over (its own prompt is shown in the Prompts tab)", agent=tool["agent"],
             prompt=toolspec.agent_prompt(run.domain, tool["agent"]))
    granted, who = request_access(run, tool, clean, intent, client, auto_access)
    if not granted:
        return None, {"error": f"a person denied this agent access ({who}). Do not retry; tell the user."}
    agent = Agent(tool["agent"], client=client, wait_seconds=0)
    run.step("tool_call", f"{tool['name']}({', '.join(f'{k}={v!r}' for k, v in clean.items())})",
             tool=tool["name"], agent=tool["agent"], action=tool["action"], args=clean, intent=intent)
    d = agent.propose(tool["action"], clean, intent=intent, user_instruction=run.text, on_behalf_of=tool.get("on_behalf_of", ""))
    run.step("tool_result", f"Gateway: {d['verdict']} ({d['rule']}): {d['reason']}", decision=d["id"], verdict=d["verdict"], status=d["status"])
    d = wait_for_human(run, d, client)
    return d, summarise(d)


# ------------------------------------------------------------------------------------------------ loop
def run_agent(domain: str, text: str, client=None, attachment: str = "", run_id: str | None = None, auto_access: bool = False) -> dict:
    client = client or httpx.Client(base_url=config.GATEWAY_URL, timeout=15.0)
    run = Run(client, domain, text, run_id, attachment)
    system = system_prompt(domain)
    messages = [{"role": "system", "content": system}, {"role": "user", "content": user_message(text, attachment)}]
    run.step("start", f"New request: {text}", domain=domain, system_prompt=system, tools=toolspec.render(domain),
             roster=toolspec.roster(domain), attachment=attachment,
             agents={a["id"]: toolspec.agent_prompt(domain, a["id"]) for a in toolspec.AGENTS[domain]})
    last = None
    for turn in range(1, MAX_TURNS + 1):
        run.step("llm_request", f"Asking the language model (turn {turn})", turn=turn, messages=messages)
        obj, raw = None, ""
        for attempt in (1, 2):
            try:
                raw, meta = llm.chat_ex(messages, report=lambda t, **k: run.step("llm_notice", t, turn=turn, **k))
            except llm.LLMError as e:
                run.step("error", str(e), turn=turn)
                run.say(f"I could not get an answer from any language model ({e}). Nothing was done. Please try again in a moment.")
                return {"error": "llm"}
            run.step("llm_response", f"Language model replied ({meta['provider']} · {meta['model']})", turn=turn, raw=raw, **meta)
            try:
                obj = llm.parse_json(raw)
                break
            except ValueError:
                run.step("error", "The reply was not valid JSON; asking the model to try again", turn=turn)
                messages += [{"role": "assistant", "content": raw},
                             {"role": "user", "content": "Your reply was not a single valid JSON object. Reply again with only the JSON object described in the instructions."}]
        if obj is None:
            run.say("I could not understand my own reply format just now. Please try rephrasing your request.")
            return {"error": "bad json"}
        if obj.get("thought"):
            run.step("thought", str(obj["thought"]), turn=turn)
        tool_name = obj.get("tool")
        if not tool_name:
            reply = str(obj.get("reply") or "").strip() or "I have nothing to add."
            run.step("answer", reply, turn=turn)
            run.say(reply)
            return {"reply": reply, "decision": last}
        tool = toolspec.find(domain, str(tool_name))
        if tool is None:
            result = {"error": f"unknown tool {tool_name!r}. Available tools: {[t['name'] for t in toolspec.TOOLS.get(domain, [])]}"}
            run.step("error", result["error"], turn=turn)
        else:
            try:
                d, result = call_tool(run, tool, obj.get("args") or {}, str(obj.get("intent") or ""), client, auto_access)
                last = d or last
            except httpx.HTTPError as e:
                run.step("error", f"The gateway could not be reached: {e}")
                run.say("I could not reach the safety gateway, so nothing was done.")
                return {"error": "gateway"}
        messages += [{"role": "assistant", "content": raw},
                     {"role": "user", "content": "TOOL RESULT (from the SEALGATE gateway): " + json.dumps(result, ensure_ascii=False) +
                      "\nNow either call another tool or give your final reply to the user."}]
    run.say("I stopped after several steps. Please check the Live Gate for the current state of this request.")
    return {"error": "too many turns"}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--domain", default="bank")
    ap.add_argument("--text", required=True)
    ap.add_argument("--attachment-file")
    ap.add_argument("--run-id")
    ap.add_argument("--auto-access", action="store_true", help="the user pressed Execute on a prepared prompt, which grants access")
    ns = ap.parse_args(argv)
    attachment = pathlib.Path(ns.attachment_file).read_text(encoding="utf-8") if ns.attachment_file else ""
    try:
        run_agent(ns.domain, ns.text, attachment=attachment, run_id=ns.run_id, auto_access=ns.auto_access)
    except httpx.HTTPError as e:
        print(f"gateway unreachable: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
