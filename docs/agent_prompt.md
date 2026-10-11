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

## How a request flows (nothing starts on its own)
1. The model reads the request (and any pasted document) and decides: answer, ask a question, or call a tool.
2. A tool call is checked first: required parameters present, values from the allowed choices, and every identifier (customer, vendor, patient, e-mail) must appear in the request or the document. A made-up identifier is rejected and the model is told to ask instead.
3. The agent that owns the tool **asks for access in the chat**. A person grants or denies. Nothing has reached the gateway yet.
4. On grant, the agent signs and sends the proposal. The gateway measures it in a sandbox and decides ALLOW, HOLD or BLOCK.
5. Even ALLOW waits for a person to approve the measured effect (rule R13). A blocked proposal is never executed; a person can mark it as reviewed or use the smallest safe version.
6. The agent waits for that human decision and then tells the user what happened.

The gateway receives only the user's request as the instruction (never the pasted document), so a buried instruction cannot widen what counts as "asked for".

## Models and reliability
The model is called with retries and back-off on rate limits, server errors and timeouts. If a hosted provider keeps failing, the next one is used (default fallback: a local Ollama model). Every retry and switch is shown in the live activity. If every provider fails the agent says so and does nothing; there is no scripted fallback.
