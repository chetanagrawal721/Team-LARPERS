"""A live agent driven by a language model. Run as its own process: python -m agents.llm_agent --domain bank --text "..."

Every step is reported to the gateway's live feed (prompts, replies, thoughts, tool calls, results), so a person can watch
exactly what the agent sees and decides. If no model is reachable it says so and falls back to the scripted router."""
import argparse
import pathlib
import sys
import time
import uuid

import httpx

from . import config, llm, scenarios, toolspec
from .tools import Agent

MAX_TURNS = 5
PROMPT_FILE = pathlib.Path(__file__).parent / "prompts" / "system.txt"
ORGS = {"bank": "Sahyadri Bank", "hospital": "Pune Care Hospital", "shop": "KartBazaar"}


class Run:
    def __init__(self, client, domain: str, text: str):
        self.client, self.domain, self.text = client, domain, text
        self.id = "run-" + uuid.uuid4().hex[:8]

    def step(self, kind: str, text: str = "", **data) -> None:
        try:
            self.client.post("/agent/step", json={"run": self.id, "kind": kind, "text": text, "data": data})
        except httpx.HTTPError:
            pass

    def say(self, text: str) -> None:
        try:
            self.client.post("/chat", json={"from": "agent", "agent": "Assistant", "text": text})
        except httpx.HTTPError:
            pass


def system_prompt(domain: str) -> str:
    return PROMPT_FILE.read_text(encoding="utf-8").format(org=ORGS.get(domain, domain), tools=toolspec.render(domain))


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
    if d["verdict"] == "HOLD":
        out["needs_human_approvals"] = d.get("approvals_needed")
    return out


def call_tool(run: Run, tool: dict, args: dict, intent: str, client) -> dict:
    allowed = set(tool["params"])
    clean = {k: v for k, v in (args or {}).items() if k in allowed and v not in (None, "")}
    clean.update(tool.get("fixed", {}))
    agent = Agent(tool["agent"], client=client, wait_seconds=0)
    run.step("tool_call", f"{tool['name']}({', '.join(f'{k}={v!r}' for k, v in clean.items())})",
             tool=tool["name"], agent=tool["agent"], action=tool["action"], args=clean, intent=intent)
    d = agent.propose(tool["action"], clean, intent=intent, user_instruction=run.text, on_behalf_of=tool.get("on_behalf_of", ""))
    run.step("tool_result", f"Gateway: {d['verdict']} ({d['rule']}): {d['reason']}", decision=d["id"], verdict=d["verdict"], status=d["status"])
    return d


def fallback(run: Run, why: str, client) -> None:
    run.step("fallback", f"Language model unavailable: {why}. Using the scripted request router instead.")
    name, text = scenarios.from_text(run.text)
    if name and scenarios.DOMAIN_OF.get(name) == run.domain:
        run.say(f"The language model is not available ({why}), so I am matching your request to a built-in routine instead.")
        scenarios.run(name, scenarios.Context(client=client, wait_seconds=0), text=run.text)
    else:
        run.say(f"I could not reach the language model ({why}), and this request does not match any built-in routine, so I can't act on it. "
                "Try again in a moment, or use one of the scenarios.")


def run_agent(domain: str, text: str, client=None) -> dict:
    client = client or httpx.Client(base_url=config.GATEWAY_URL, timeout=15.0)
    run = Run(client, domain, text)
    system = system_prompt(domain)
    messages = [{"role": "system", "content": system}, {"role": "user", "content": text}]
    run.step("start", f"New request: {text}", domain=domain, system_prompt=system, tools=toolspec.render(domain))
    last = None
    for turn in range(1, MAX_TURNS + 1):
        run.step("llm_request", f"Asking the language model (turn {turn})", turn=turn, messages=messages)
        raw = None
        for attempt in (1, 2):
            try:
                raw = llm.chat(messages)
            except llm.LLMError as e:
                if attempt == 1:
                    time.sleep(0.5)
                    continue
                run.step("error", str(e), turn=turn)
                fallback(run, str(e), client)
                return {"fallback": True}
            run.step("llm_response", "Language model replied", turn=turn, raw=raw)
            try:
                obj = llm.parse_json(raw)
                break
            except ValueError:
                run.step("error", "The reply was not valid JSON; asking the model to try again", turn=turn)
                messages += [{"role": "assistant", "content": raw},
                             {"role": "user", "content": "Your reply was not a single valid JSON object. Reply again with only the JSON object described in the instructions."}]
                obj = None
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
                last = call_tool(run, tool, obj.get("args") or {}, str(obj.get("intent") or ""), client)
                result = summarise(last)
            except httpx.HTTPError as e:
                run.step("error", f"The gateway could not be reached: {e}")
                run.say("I could not reach the safety gateway, so nothing was done.")
                return {"error": "gateway"}
        messages += [{"role": "assistant", "content": raw},
                     {"role": "user", "content": "TOOL RESULT (from the SEALGATE gateway): " + str(result).replace("'", '"') +
                      "\nNow either call another tool or give your final reply to the user."}]
    run.say("I stopped after several steps. Please check the Live Gate for the current state of this request.")
    return {"error": "too many turns"}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--domain", default="bank")
    ap.add_argument("--text", required=True)
    ns = ap.parse_args(argv)
    try:
        run_agent(ns.domain, ns.text)
    except httpx.HTTPError as e:
        print(f"gateway unreachable: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
