# The live agent: prompt, tools and protocol

The live agent (`agents/llm_agent.py`) is driven by a language model. It runs as its own process and holds only its signing key and its own model credentials; it cannot reach any database or credential of the organisation. Everything it does is a *proposal* to the gateway.

The complete system prompt is `agents/prompts/system.txt`; the tools per organisation are in `agents/toolspec.py`. Both are also shown in the Prompts tab of the agent drawer for every run, together with every message sent to the model and every raw reply.

## Protocol (one JSON object per model turn)
```json
{"thought": "one short sentence", "tool": "refund_duplicate_charges" | null,
 "args": {"customer": "C-1042", "month": "March", "match": "batch"},
 "intent": "what the agent tells the gateway it is about to do", "reply": "final message to the user (empty while calling a tool)"}
```
After a tool call the agent receives `TOOL RESULT (from the SEALGATE gateway): {...}` containing the verdict, rule, reason, what the sandbox measured, what was asked for and any safe version. It then calls another tool or gives its final reply. At most five turns per request.

## What the model decides, and what it cannot
- It decides whether a request is a question (answer directly), an operation (call a tool), or unclear (ask a short question).
- It chooses the tool arguments. This is where misinterpretation can happen in real use, for example choosing `match: "batch"` when asked for one customer. The gateway measures the real effect regardless of what the agent claims.
- It cannot execute anything, see the database, approve anything, or bypass a block.

## Modes
- **Live LLM** (default when `AI_PROVIDER`, `AI_MODEL` and `AI_API_KEY` are set): every typed request goes to the model.
- **Scripted demo**: fixed routines with a deliberately mis-scoped agent, so the "agent says one, sandbox measures many" gap is reproducible without a model.
- If the model is unreachable, the agent says so and falls back to the scripted router when the request matches one; otherwise it tells the user it cannot act.
