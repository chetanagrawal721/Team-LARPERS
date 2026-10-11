"""The live, language-model-driven agent: every request goes through the model, every step is visible."""
import json

import httpx
import pytest

from agents import llm, llm_agent


def reply(obj):
    return obj if isinstance(obj, str) else json.dumps(obj)


@pytest.fixture
def model(monkeypatch):
    """Install a scripted model. Returns (script (list of replies), requests seen)."""
    monkeypatch.setenv("AI_PROVIDER", "openrouter")
    monkeypatch.setenv("AI_MODEL", "test-model")
    monkeypatch.setenv("AI_API_KEY", "k")
    from gateway.main import BUS
    BUS.history.clear()                 # every test reads only its own events
    seen, script = [], []

    def handler(request):
        seen.append(json.loads(request.content))
        if not script:
            return httpx.Response(500, json={})
        nxt = script.pop(0)
        if isinstance(nxt, int):
            return httpx.Response(nxt, json={"error": "x"})
        return httpx.Response(200, json={"choices": [{"message": {"content": reply(nxt)}}]})
    from gateway import ai as gateway_ai
    gateway_ai.STATE["force"] = "off"        # the gateway's own AI checks must not call a real model in tests
    llm.TRANSPORT = httpx.MockTransport(handler)
    yield script, seen
    llm.TRANSPORT = None
    gateway_ai.STATE["force"] = None


def agent_steps():
    from gateway.main import BUS
    return [(e.data.get("kind"), e.data) for _, e in BUS.history if e.type == "agent"]


def chats():
    from gateway.main import BUS
    return [e.data["text"] for _, e in BUS.history if e.type == "chat"]


def test_general_question_is_answered_without_touching_the_gateway(client, model):
    script, seen = model
    script.append({"thought": "A general question, no operation needed.", "tool": None, "args": {}, "intent": "",
                   "reply": "SEALGATE checks what an action will really do before it runs."})
    out = llm_agent.run_agent("bank", "What does SEALGATE do?", client)
    assert out["reply"].startswith("SEALGATE checks") and client.get("/actions").json() == []
    assert any("SEALGATE checks" in t for t in chats())
    assert "start" in [k for k, _ in agent_steps()] and "answer" in [k for k, _ in agent_steps()]


def test_full_system_prompt_and_messages_are_visible(client, model):
    script, seen = model
    script.append({"thought": "t", "tool": None, "args": {}, "intent": "", "reply": "Hello."})
    llm_agent.run_agent("bank", "hi", client)
    start = [d for k, d in agent_steps() if k == "start"][-1]
    assert "Sahyadri Bank" in start["data"]["system_prompt"] and "refund_duplicate_charges" in start["data"]["tools"]
    req = [d for k, d in agent_steps() if k == "llm_request"][-1]
    assert req["data"]["messages"][0]["role"] == "system" and req["data"]["messages"][1]["content"] == "hi"
    assert seen[0]["messages"][0]["role"] == "system"            # what the model really received


def test_tool_call_goes_through_the_gateway_and_the_model_explains_the_block(client, model):
    script, seen = model
    script.append({"thought": "Refund the whole batch as asked.", "tool": "refund_duplicate_charges",
                   "args": {"customer": "C-1042", "month": "March", "match": "batch"},
                   "intent": "refund one customer's duplicate March charges", "reply": ""})
    script.append({"thought": "Blocked.", "tool": None, "args": {}, "intent": "",
                   "reply": "The gateway blocked it: it would refund 61 customers, not one."})
    out = llm_agent.run_agent("bank", "Refund C-1042 and everyone hit by the same March batch bug", client)
    d = client.get("/actions").json()[0]
    assert d["verdict"] == "BLOCK" and d["rule"] == "R06" and d["agent"] == "refund-agent"
    assert d["agent_claim"] == "refund one customer's duplicate March charges"
    assert out["reply"].startswith("The gateway blocked")
    k = [x for x, _ in agent_steps()]
    assert k.index("tool_call") < k.index("tool_result") < k.index("answer")
    assert "TOOL RESULT" in seen[1]["messages"][-1]["content"] and "BLOCK" in seen[1]["messages"][-1]["content"]


def test_gateway_pipeline_and_sandbox_rows_stream_live(client, model):
    script, _ = model
    script.append({"thought": "t", "tool": "refund_duplicate_charges",
                   "args": {"customer": "C-1042", "month": "March", "match": "batch"}, "intent": "refund one customer", "reply": ""})
    script.append({"thought": "t", "tool": None, "args": {}, "intent": "", "reply": "Blocked."})
    llm_agent.run_agent("bank", "refund batch", client)
    from gateway.main import BUS
    pipe = [e.data for _, e in BUS.history if e.type == "pipeline"]
    texts = " | ".join(p["text"] for p in pipe)
    assert "Signature, timestamp and nonce verified" in texts and "Sandbox measured: 212 rows" in texts and "OUTSIDE the request" in texts
    assert any(p["status"] == "denied" for p in pipe)
    sb = [e.data for _, e in BUS.history if e.type == "sandbox"][-1]
    assert sb["total"] == 212 and sb["outside"] == 209 and sum(r["inside"] for r in sb["rows"]) == 3
    assert all("name" in r and "pk" in r for r in sb["rows"])


def test_missing_detail_is_asked_not_guessed(client, model):
    script, _ = model
    script.append({"thought": "No customer given.", "tool": None, "args": {}, "intent": "",
                   "reply": "Which customer should I refund, and for which month?"})
    llm_agent.run_agent("bank", "refund the duplicates", client)
    assert client.get("/actions").json() == [] and any("Which customer" in t for t in chats())


def test_invalid_json_is_retried_once(client, model):
    script, seen = model
    script += ["Sure! Here you go: not json at all",
               {"thought": "t", "tool": None, "args": {}, "intent": "", "reply": "Hi there."}]
    out = llm_agent.run_agent("bank", "hello", client)
    assert out["reply"] == "Hi there." and len(seen) == 2
    assert "valid JSON" in seen[1]["messages"][-1]["content"]


def test_unknown_tool_is_reported_back_to_the_model(client, model):
    script, seen = model
    script += [{"thought": "t", "tool": "launch_rocket", "args": {}, "intent": "", "reply": ""},
               {"thought": "t", "tool": None, "args": {}, "intent": "", "reply": "I do not have that tool."}]
    llm_agent.run_agent("bank", "launch a rocket", client)
    assert "unknown tool" in seen[1]["messages"][-1]["content"] and client.get("/actions").json() == []


def test_model_down_falls_back_to_the_scripted_router_when_it_can(client, model):
    script, _ = model
    script.append(500)
    out = llm_agent.run_agent("bank", "Refund C-1042's duplicate March charges", client)
    assert out == {"fallback": True} and client.get("/actions").json()[0]["action"] == "refund"
    assert any(k == "fallback" for k, _ in agent_steps())


def test_model_down_and_unmappable_request_says_so(client, model):
    script, _ = model
    script.append(500)
    llm_agent.run_agent("bank", "what is the weather", client)
    assert any("could not reach the language model" in t for t in chats()) and client.get("/actions").json() == []


def test_agent_package_still_holds_no_database_path_or_user_tokens():
    import pathlib
    for f in pathlib.Path("agents").rglob("*"):
        if f.suffix in (".py", ".txt"):
            t = f.read_text().lower()
            assert "sqlite" not in t and ".db" not in t and "user_token" not in t and "seal_key" not in t, f


def test_agent_mode_endpoint_and_chat_routing(client, monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "openrouter")
    monkeypatch.setenv("AI_MODEL", "m")
    from gateway import main
    main.AGENT["mode"] = None
    captured = {}
    monkeypatch.setattr("gateway.main.subprocess.Popen",
                        lambda args, cwd, env: captured.update(args=args, env=env) or type("P", (), {"pid": 1})())
    assert client.get("/agent/mode").json()["mode"] == "llm"
    r = client.post("/demo/chat", json={"text": "what can you do?"}).json()
    assert r["started"] == "llm-agent" and "agents.llm_agent" in captured["args"]
    assert "AI_API_KEY" in captured["env"] or "AI_MODEL" in captured["env"]
    assert "USER_TOKEN_PRIYA" not in captured["env"] and "GATEWAY_SEAL_KEY" not in captured["env"]
    assert client.post("/agent/mode", json={"mode": "scripted"}).json()["mode"] == "scripted"
    assert client.post("/agent/mode", json={"mode": "bogus"}).status_code == 422
    main.AGENT["mode"] = None


def test_agent_step_endpoint_publishes_to_the_live_feed(client):
    client.post("/agent/step", json={"run": "r1", "kind": "thought", "text": "thinking", "data": {"turn": 1}})
    assert ("thought", "thinking") in [(k, d["text"]) for k, d in agent_steps()]
