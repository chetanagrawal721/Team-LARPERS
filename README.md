# 🔏 SEALGATE

**Effect-sealed authorization for AI agents** — VORTEXA 3.0, problem C-01 ActionGate.

> We approve what an action will really do — not what it says. And we seal that approval, so nothing else can run.

Every agent action is first run on a **sandbox copy** to measure its real effect (rows, people, amounts, labels). That effect is compared with what the user actually asked for (the *envelope*), decided by deterministic rules (ALLOW / HOLD / BLOCK), and an approval is a **seal** bound to that exact effect. At execution the gateway re-measures inside one transaction; if anything differs, nothing runs and the reason is named (`effect_drift`, `args_drift`, `policy_drift`, `label_drift`, `state_drift`, `replay`, `expired`).

Also: smallest safe version, Shadow Mode, data labels, resource-keyed budgets, transactional outbox, hash-chained audit log with replay, escalate-only AI with a rules-only fallback, and a paired, pre-registered Attack Lab.

Documents: [design](docs/SEALGATE_Final_Solution.md) · [build playbook](docs/SEALGATE_Build_Playbook.md) · [project journal](docs/PROJECT_JOURNAL.md) · [engineering logbook](DEV_LOGBOOK.md) · [API](docs/api.md) · [fixtures](docs/fixtures.md)

## Setup (Windows with Git Bash, macOS, Linux)
Python 3.11+ and Node 20+ are needed.
```bash
python -m venv .venv
source .venv/Scripts/activate        # macOS/Linux: source .venv/bin/activate
pip install -r gateway/requirements.txt
cp .env.example .env                 # then replace the change-me values (demo keys only; never commit .env)
(cd frontend && npm install)
git config core.hooksPath .githooks  # authorship guard
```
For the frontend to sign in as a demo approver, create `frontend/.env.local` (untracked):
```
VITE_DEMO_TOKENS={"priya":"<USER_TOKEN_PRIYA>","rahul":"<USER_TOKEN_RAHUL>","anita":"<USER_TOKEN_ANITA>","meera":"<USER_TOKEN_MEERA>"}
```

### Optional AI
Works fully offline without AI (the log then shows `fallback`). To turn it on, set in `.env`:
`AI_PROVIDER=gemini|openrouter|ollama`, `AI_MODEL=<model>`, `AI_API_KEY=<key>` (Ollama needs no key). AI can only make a decision stricter.

## Run
```bash
./run.sh            # gateway on :8000, frontend on :5173 → open http://localhost:5173
./reset_demo.sh     # back to the initial demo state (fresh data, empty audit log)
pytest -q           # all tests (about 70 s; includes the 3-mode Attack Lab)
python -m lab.runner   # the paired attack suite on its own
```

## Demo script (about 3 minutes)
Everything is live: every request goes to a language model (set `AI_PROVIDER`, `AI_MODEL`, `AI_API_KEY` in `.env`, or just run Ollama). Nothing is scripted. An agent first asks you for **access** in the chat, the gateway measures its proposal in a sandbox, and a person approves or rejects the result.

| # | Action | What to say |
|---|---|---|
| 1 | **Ask an agent** → "What can you help me with?" | The model answers general questions itself; no agent is involved. |
| 2 | "Update customer C-0007's phone number to +91-9811122233" → **Grant access** → on the Live Gate **Approve**, then **Execute** | Ordinary work: the agent asks, the gateway measures one row, a person approves. Even an allowed action waits for a person. |
| 3 | **Attack Lab → Live attacks → Execute** on "Duplicate-charge ticket" | A short, narrow request plus a long ticket with a buried instruction. The model is fooled into refunding the whole batch; the sandbox measures 212 rows against the 1 customer asked for; the gateway blocks it and offers the smallest safe version. |
| 4 | Open **Live activity** | Every gateway check, then the sandbox result row by row, each row APPROVED or DENIED. |
| 5 | Open **Prompts** → **Show whole prompt** | The exact text the model received and what it answered. |
| 6 | **Agents** page | What each agent does, cannot do, its tools and its own prompt. |
| 7 | Pay the pending invoices, approve with two people, **Add 3,960 matching invoices**, **Execute** | Same request, same arguments, but the data changed. The seal breaks; nothing runs. |
| 8 | Toggle **AI assist** off and repeat a block | AI makes us stricter, never looser (`rules only` in the log). |
| 9 | **Audit** → **Verify** | Every decision, including refusals, is tamper-evident and replayable. |
| 10 | **Attack Lab → Benchmark suite → Run suite** | Pre-registered paired evidence in three modes. |

More prompts to try are in the chat panel ("Try these prompts"): questions, normal work, requests that should be blocked, and prompts that test the agent (invented ids, missing details, attempts to extract its prompt).

## Architecture in one paragraph
Agents are separate processes that hold only a signing key and can only `POST /propose`. Only the gateway process opens the databases, mail and payment channels. Business data lives in one SQLite file per domain (`gateway/data/*.db`, generated, never committed); gateway state (audit chain, seals, approvals, shadow sessions) lives in `<domain>_state.db`.

## Known limits (stated openly)
- Labels cannot see personal data rewritten into free text; the AI paraphrase sentry is best-effort and can only hold.
- The gateway sees only data it served; covert channels are out of scope.
- External systems cannot always be dry-run; irreversible sends go through an outbox after commit.
- Envelope quality depends on the clarity of the instruction (vague requests get the strict policy default).
- Sandboxes are file copies; production would use transactions, savepoints or database branching.
- Demo authentication (`X-User` + token) is not a production design.
- The audit chain does not by itself detect truncation of the newest entries.

All data in this repository is fictional.
