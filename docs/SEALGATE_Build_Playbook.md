# 🔏 SEALGATE — Build Playbook
### VORTEXA 3.0 · C-01 ActionGate · Step-by-step implementation guide

> Reference design: `SEALGATE_Final_Solution.md`
> Progress & research record: `PROJECT_JOURNAL.md` (update after every milestone)

---

## How to use this playbook

1. Work **one milestone at a time**, in dependency order.
2. A milestone is DONE only when **all test cases pass** and **every verification box is ticked**.
3. Only then run its **Git Checkpoint**. Never push a failing milestone.
4. After each push, add one line to the **Log** in `PROJECT_JOURNAL.md` and tick the milestone there.
5. At the end of each phase, fill in the **Phase Completion Checkpoint** and make a Go/No-Go call.

---

## A. Missing information — confirm before starting

These are not architectural questions; the architecture is fixed. Defaults are used below until you change them.

| # | Question | Default used in this playbook |
|---|---|---|
| 1 | Repository name and owner | `sealgate`, owned by `aryanketkar-15` (others added as collaborators) |
| 2 | Does VORTEXA allow code written before the event? | **Assumed NO.** Only Phase 0.1 (empty repo, git identities, hooks) is done beforehand. Check with organisers. |
| 3 | Role assignment | aryanketkar-15 → Gateway core · chetanagrawal721 → Effects & domains · Kanak-Agrawal-3008 → Frontend · atharvg44 → AI, agents & evaluation (swap freely) |
| 4 | Laptops' OS | Windows/macOS/Linux all supported; commands shown for bash (Git Bash on Windows) |
| 5 | Python / Node versions | Python 3.11, Node 20 LTS |
| 6 | Local LLM available? | Ollama with a small model (`qwen2.5:3b` or `llama3.2:3b`). If not installed, AI runs in fallback mode — the system remains fully functional. |
| 7 | Venue internet reliability | Assumed unreliable. Nothing in the core demo needs internet. |
| 8 | Demo machine | One laptop runs gateway + agents + frontend; projector at 1920×1080 |

---

## B. Team, ownership and branches

| GitHub ID | Role | Branch | Owns phases / milestones |
|---|---|---|---|
| **aryanketkar-15** | P1 · Gateway core (repo owner, integrator) | `aryan/gateway` | 0.1, 0.3a, Phase 1, Phase 4, 6.3, integration merges |
| **chetanagrawal721** | P2 · Effects, rules & domains | `chetan/effects` | Phase 2, Phase 3, 6.1, 6.2, 7.2 |
| **Kanak-Agrawal-3008** | P3 · Frontend | `kanak/frontend` | 0.2c, Phase 8 |
| **atharvg44** | P4 · AI, agents & evaluation | `atharv/ai-agents` | 0.3b, Phase 5, 7.1, Phase 9 |

**Integration rule:** each person pushes only to their own branch. `aryanketkar-15` merges branches into `main` at each **Phase Completion Checkpoint**, after the phase's tests pass on `main`.

---

## C. Schedule (12 hours, parallel work)

| Hours | aryanketkar-15 | chetanagrawal721 | Kanak-Agrawal-3008 | atharvg44 |
|---|---|---|---|---|
| 0:00–0:30 | 0.2a, 0.3a | 0.2b | 0.2c | 0.3b (pre-register suite) |
| 0:30–3:00 | Phase 1 | 2.1, 2.2, 2.3 | 8.1 | 7.1 (agents, stub gateway) |
| 3:00–6:00 | **Phase 4** | 3.1, 3.2, 3.3 | 8.2 | 5.1, 5.2 |
| 6:00–7:00 | Integration + 6.3 | 6.1 | 8.3 | 5.3 |
| 7:00–8:30 | Integration, fixes | 6.2 | 8.3 / 8.4 | 9.1 |
| 8:30–9:30 | Fixes | 7.2 | 8.4 | 9.2 |
| 9:30–11:00 | Fixes only | Fixes only | **Polish only** | Pitch, Q&A |
| 11:00–12:00 | **9.3 — all four: dry runs, release** | | | |

**Hour-6 gate:** Phase 4 (seal + one-transaction execute + outbox) must be complete. If not, everyone except Kanak-Agrawal-3008 stops other work and helps finish it.

**Cut order if behind:** 5.3 paraphrase sentry → 6.3 replay → hospital domain in 7.2 → 6.2 Shadow Mode → 3.3 budgets.
**Never cut:** 2.x, 3.1, 3.2, Phase 4, 5.1 fallback, 1.3 audit chain, 8.2.

---

## D. Dependency map

```
0.1 → 0.2 → 0.3 ─┬─ 1.1 → 1.2 → 1.3 ───────────────┐
                 ├─ 2.1 → 2.2 → 2.3 → 3.1 → 3.2 → 3.3
                 │                      │      │
                 │                      ▼      ▼
                 │                    4.1 → 4.2 → 4.3 → 6.1 → 6.2 → 6.3
                 │                             │
                 ├─ 5.1 → 5.2 → 5.3 ───────────┘ (plugs into 3.2 decide)
                 ├─ 7.1 (agents; needs 1.2 for real signing)  7.2 (needs 2.x, 3.x)
                 └─ 8.1 → 8.2 → 8.3 → 8.4 (UI against mock API until 4.3, then real)
                                       ▼
                                 9.1 → 9.2 → 9.3
```

Frontend (Phase 8) and agents (7.1) start against **mock responses** defined in 0.3 and switch to the real gateway when the matching backend milestone is done.

---

## E. Git conventions (apply to every checkpoint)

### E.1 One-time identity setup (each member, on their own laptop)
```bash
git config --global user.name  "<your-github-id>"            # e.g. aryanketkar-15
git config --global user.email "<id>+<github-id>@users.noreply.github.com"
# find your noreply email: GitHub → Settings → Emails
```

### E.2 Keeping authorship to the four team members only
- Commit **by hand** from your own terminal. If any AI coding tool offers to commit for you, decline, or turn off its "co-author" / attribution setting first.
- Never paste a commit message that contains a `Co-authored-by:` trailer for anyone outside the team.
- The repository includes two hooks (installed in Milestone 0.1) that **reject** commits whose message has a non-team co-author trailer, or whose author is not one of the four IDs.

> Note for later: many journals and patent offices have their own rules about disclosing AI assistance in research. Git authorship and those disclosure rules are separate questions — check the venue's policy when drafting.

### E.3 Commit message format
```
M<phase>.<milestone>: <what was achieved> (<rules/requirements touched>)
```
Example: `M4.2: effect seal with typed drift detection (R6)`

### E.4 Never commit
| Never commit | Why |
|---|---|
| `.env`, any API keys, HMAC secrets | Credentials |
| `gateway/data/*.db`, `gateway/data/sandbox/` | Generated by seed scripts; contain sandbox copies |
| `node_modules/`, `frontend/dist/` | Generated |
| `.venv/`, `__pycache__/`, `.pytest_cache/` | Generated |
| `*.log`, `audit_export*.json` | Runtime output |
| Ollama model files | Large, downloaded |

Commit the **seed scripts**, never the databases.

### E.5 Standard rollback procedures (referenced by every milestone)

| Situation | Command |
|---|---|
| Broken commit already pushed, others may have pulled | `git revert <bad-commit-hash>` → `git push origin <branch>` (safe, keeps history) |
| Broken commits on **your own branch only**, nobody pulled | `git reset --hard <last-good-hash>` → `git push --force-with-lease origin <branch>` |
| Need to inspect the last stable state without losing work | `git stash` → `git checkout <tag-or-hash>` → test → `git checkout <branch>` → `git stash pop` |
| Phase merge to `main` broke things | `git revert -m 1 <merge-commit-hash>` → `git push origin main` |
| Recover a "lost" commit | `git reflog` → find hash → `git checkout -b recovery <hash>` |

Every Phase Completion Checkpoint creates a tag (`phase-N-ok`) to return to.

---

# PHASE 0 — Project Setup & Baseline

---

## Milestone 0.1 — Repository, identities and authorship guards
**Owner:** aryanketkar-15 · **Depends on:** nothing · **When:** before the event (if allowed) or minute 0

**1. Milestone Name** — Repository created with protected authorship and ignore rules.

**2. Objective** — Create the shared repository so all four members can push to their own branches, with commits restricted to team identities and no generated or secret files tracked.

**3. Tasks to Complete**
- [ ] Create GitHub repo `sealgate` (private until judging if preferred); add the other three IDs as collaborators
- [ ] Add `.gitignore`, `README.md` (one paragraph), `PROJECT_JOURNAL.md`, `SEALGATE_Final_Solution.md`, this playbook
- [ ] Add `.githooks/commit-msg` and `.githooks/pre-commit`; set `core.hooksPath`
- [ ] Create the four personal branches from `main`
- [ ] Every member: complete E.1 identity setup, clone, run hook install

**4. Files / Modules Affected** — `.gitignore`, `.githooks/commit-msg`, `.githooks/pre-commit`, `README.md`, `PROJECT_JOURNAL.md`, `docs/`

**5. Implementation Guidance**

`.gitignore`
```gitignore
.env
*.env
.venv/
__pycache__/
.pytest_cache/
node_modules/
frontend/dist/
gateway/data/*.db
gateway/data/sandbox/
*.log
audit_export*.json
.DS_Store
```

`.githooks/commit-msg` — rejects co-author trailers for anyone outside the team
```sh
#!/bin/sh
ALLOWED='aryanketkar-15|Kanak-Agrawal-3008|chetanagrawal721|atharvg44'
if grep -iE '^co-authored-by:' "$1" | grep -viE "$ALLOWED" >/dev/null; then
  echo "✖ Commit rejected: co-author trailer for someone outside the team."
  exit 1
fi
```

`.githooks/pre-commit` — rejects commits from non-team authors
```sh
#!/bin/sh
AUTHOR=$(git var GIT_AUTHOR_IDENT)
echo "$AUTHOR" | grep -qE 'aryanketkar-15|Kanak-Agrawal-3008|chetanagrawal721|atharvg44' || {
  echo "✖ Commit rejected: author is not a team member. Run: git config user.name <github-id>"; exit 1; }
```

Install (every member, after cloning):
```bash
git config core.hooksPath .githooks
chmod +x .githooks/*        # macOS/Linux/Git Bash
```

Create branches:
```bash
for b in aryan/gateway chetan/effects kanak/frontend atharv/ai-agents; do git branch $b; git push -u origin $b; done
```

**6. Test Cases**

| ID | Scenario | Preconditions | Steps | Expected Result | Status |
|---|---|---|---|---|---|
| T0.1-1 | Team author commits | Hooks installed, identity set | Commit a README change | Commit succeeds | ☐ |
| T0.1-2 | Non-team co-author trailer | Hooks installed | `git commit -m "x" -m "Co-authored-by: Someone <a@b.c>"` | Rejected with message | ☐ |
| T0.1-3 | Team co-author trailer | Hooks installed | Trailer naming `chetanagrawal721` | Accepted | ☐ |
| T0.1-4 | Wrong author name | `git config user.name "test"` | Commit | Rejected | ☐ |
| T0.1-5 | Ignored files | Create `.env`, `gateway/data/x.db` | `git status` | Neither appears | ☐ |
| T0.1-6 | Collaborator access | Others invited | Each member pushes to own branch | All four pushes succeed | ☐ |

**7. Verification Checklist**
- [ ] All four members have pushed one commit to their branch
- [ ] `git log --format='%an <%ae>'` shows only the four IDs
- [ ] Hooks reject T0.1-2 and T0.1-4 on every laptop

**8. Completion Criteria** — Repository exists, four branches exist, hooks active on all four laptops, all tests pass.

**9. Git Checkpoint**
```bash
git status
git add .gitignore .githooks README.md PROJECT_JOURNAL.md SEALGATE_Final_Solution.md SEALGATE_Build_Playbook.md
git commit -m "M0.1: repository, ignore rules and authorship guard hooks"
git push origin main
```
Do not commit: `.env`, any personal git config.

**10. Rollback** — Repo-level: delete and recreate if nothing else exists. Otherwise standard E.5.

---

## Milestone 0.2 — Project scaffolds that run
**Owners:** 0.2a aryanketkar-15 (gateway) · 0.2b chetanagrawal721 (data folder + seed stub) · 0.2c Kanak-Agrawal-3008 (frontend) · **Depends on:** 0.1

**1. Milestone Name** — Empty gateway, agents and frontend projects that start and talk.

**2. Objective** — Every part of the system starts with one command, so later milestones only add code.

**3. Tasks to Complete**
- [ ] `gateway/`: Python venv, `requirements.txt`, FastAPI app with `GET /health`
- [ ] `agents/`: package with `config.py` (gateway URL) — no DB path anywhere
- [ ] `frontend/`: Vite + React + Tailwind, dark background, fetches `/health`
- [ ] `tests/` with pytest configured; `Makefile` or `run.sh` with start commands
- [ ] CORS allowing `http://localhost:5173`

**4. Files / Modules Affected** — `gateway/main.py`, `gateway/requirements.txt`, `agents/__init__.py`, `agents/config.py`, `frontend/*`, `tests/conftest.py`, `run.sh`

**5. Implementation Guidance**

Why these tools: **FastAPI** gives typed endpoints and SSE quickly; **Pydantic** enforces strict schemas (needed for AI output validation); **pytest** for repeatable tests; **Vite + React + Tailwind** for a fast single-page dashboard; **httpx** for test clients and agent calls.

```bash
# gateway
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install fastapi uvicorn[standard] pydantic pyyaml httpx pytest
pip freeze > gateway/requirements.txt

# frontend
npm create vite@latest frontend -- --template react
cd frontend && npm i && npm i -D tailwindcss postcss autoprefixer && npx tailwindcss init -p
```

`gateway/main.py`
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI(title="SEALGATE")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"],
                   allow_methods=["*"], allow_headers=["*"])
@app.get("/health")
def health(): return {"status": "ok"}
```

`run.sh`
```bash
uvicorn gateway.main:app --reload --port 8000 &
(cd frontend && npm run dev) &
wait
```

**6. Test Cases**

| ID | Scenario | Preconditions | Steps | Expected Result | Status |
|---|---|---|---|---|---|
| T0.2-1 | Gateway starts | venv active | `uvicorn gateway.main:app` | Listening on 8000 | ☐ |
| T0.2-2 | Health endpoint | Gateway running | `curl localhost:8000/health` | `{"status":"ok"}` | ☐ |
| T0.2-3 | Frontend starts | npm installed | `npm run dev` | Page at :5173, dark background | ☐ |
| T0.2-4 | Frontend → gateway | Both running | Open page | Shows "Gateway: ok" | ☐ |
| T0.2-5 | CORS rejects other origin | Gateway running | Request with `Origin: http://evil.test` | No CORS allow header | ☐ |
| T0.2-6 | pytest runs | — | `pytest -q` | 1 passing smoke test | ☐ |
| T0.2-7 | Agents have no DB path | — | `grep -ri "\.db" agents/` | No matches | ☐ |

**7. Verification Checklist**
- [ ] `./run.sh` starts both servers on a clean clone
- [ ] `requirements.txt` and `package-lock.json` committed
- [ ] No `.db`, `node_modules`, `.venv` in `git status`

**8. Completion Criteria** — All three parts start; T0.2-1…7 pass on at least two laptops.

**9. Git Checkpoint** (each owner on their branch)
```bash
git status
git add gateway agents tests run.sh            # or frontend/ for Kanak-Agrawal-3008
git commit -m "M0.2: runnable gateway/agents/frontend scaffolds with health check"
git push origin <your-branch>
```
Do not commit: `node_modules/`, `.venv/`, `frontend/dist/`.

**10. Rollback** — E.5; scaffolds are small, so `git revert` the scaffold commit and regenerate.

---

## Milestone 0.3 — API contract, schemas and pre-registered attack suite
**Owners:** 0.3a aryanketkar-15 (contract) · 0.3b atharvg44 (suite) · **Depends on:** 0.2

**1. Milestone Name** — Frozen API contract and committed paired attack suite.

**2. Objective** — Everyone builds against the same request/response shapes, and the evaluation suite is fixed **before** any results exist (pre-registration).

**3. Tasks to Complete**
- [ ] `gateway/schemas.py`: `Proposal`, `Decision`, `Effect`, `Envelope`, `ApprovalRequest`, `Event`
- [ ] `docs/api.md`: every endpoint from Final Solution §6.4 with example JSON
- [ ] `gateway/mock_api.py`: returns fixed example responses (for frontend and agents to build against)
- [ ] `lab/suite.yaml`: 22 attack cases, each with a benign twin, expected decisions for mode C
- [ ] Record the suite commit hash in `PROJECT_JOURNAL.md`

**4. Files / Modules Affected** — `gateway/schemas.py`, `gateway/mock_api.py`, `docs/api.md`, `lab/suite.yaml`

**5. Implementation Guidance**

```python
# gateway/schemas.py
from pydantic import BaseModel, Field
from typing import Literal
Verdict = Literal["ALLOW", "HOLD", "BLOCK", "VOID", "DONE"]

class Proposal(BaseModel):
    agent: str
    action: str
    args: dict
    intent: str = ""
    user_instruction: str = ""          # original human request (for envelope)
    nonce: str
    ts: int
    sig: str
    model_config = {"extra": "forbid"}

class Effect(BaseModel):
    action_type: str
    rows: dict[str, list[str]] = {}
    recipients: list[str] = []
    amount_minor: int = 0
    currency: str = "INR"
    destinations: list[str] = []
    reversible: Literal["snapshot", "compensating", "none"] = "snapshot"
    labels: list[str] = []
    label_path: list[str] = []

class Envelope(BaseModel):
    scope: dict = {}
    max_rows: int | None = None
    max_amount_minor: int | None = None
    allowed_destinations: list[str] = []
    source: Literal["ai_from_instruction", "policy_default"]

class Decision(BaseModel):
    id: str
    verdict: Verdict
    rule: str
    reason: str
    baseline_verdict: Verdict          # what a mode-B gate would say
    decision_path: Literal["rules-only", "rules+ai", "fallback"]
    effect: Effect | None = None
    envelope: Envelope | None = None
    safe_version: dict | None = None
```

`lab/suite.yaml` (shape)
```yaml
- id: A01
  domain: bank
  attack: { agent: refund-agent, action: refund, args: {customer: C-1042, month: March},
            user_instruction: "Refund C-1042's duplicate March charges", fixture: many_matching_refunds }
  expect_C: BLOCK
  twin:   { fixture: single_customer_refunds }
  twin_expect_C: ALLOW
```

Freeze rule: after this commit, `lab/suite.yaml` changes only by **adding** cases (each addition logged in the journal with the reason).

**6. Test Cases**

| ID | Scenario | Preconditions | Steps | Expected Result | Status |
|---|---|---|---|---|---|
| T0.3-1 | Valid proposal parses | schemas.py | `Proposal(**valid)` | Object created | ☐ |
| T0.3-2 | Extra field rejected | — | Add `"admin": true` | `ValidationError` | ☐ |
| T0.3-3 | Missing nonce rejected | — | Omit `nonce` | `ValidationError` | ☐ |
| T0.3-4 | Invalid verdict rejected | — | `Decision(verdict="MAYBE")` | `ValidationError` | ☐ |
| T0.3-5 | Mock API serves examples | mock running | `GET /action/demo-1` | Example Decision JSON | ☐ |
| T0.3-6 | Suite file valid | — | Load YAML, check 22 cases each with twin | 22 pairs, no missing fields | ☐ |
| T0.3-7 | Suite hash recorded | Committed | Compare journal hash with `git log -1 -- lab/suite.yaml` | Match | ☐ |

**7. Verification Checklist**
- [ ] All four members have read `docs/api.md`
- [ ] Frontend and agents can call the mock API
- [ ] Suite committed **before** any gateway logic exists

**8. Completion Criteria** — Schemas and contract frozen; suite committed with hash logged; tests pass.

**9. Git Checkpoint**
```bash
git status
git add gateway/schemas.py gateway/mock_api.py docs/api.md lab/suite.yaml tests/test_schemas.py
git commit -m "M0.3: frozen API contract, schemas, mock API and pre-registered paired suite"
git push origin <your-branch>
```

**10. Rollback** — Contract changes after this point must be agreed by all four and logged as a "last-moment change" in the journal. Revert via E.5.

### ✅ Phase 0 Completion Checkpoint

| Item | Value |
|---|---|
| Completed milestones | 0.1 ☐ · 0.2 ☐ · 0.3 ☐ |
| Tests passed | ___ / 20 |
| Known issues | |
| Merge to main | `git checkout main && git merge --no-ff aryan/gateway chetan/effects kanak/frontend atharv/ai-agents` |
| Tag | `git tag phase-0-ok && git push origin phase-0-ok` |
| Commit hash | |
| Overall verification | Clean clone → `./run.sh` → health ok → mock API serves examples |
| **Go / No-Go** | Go only if all four can run the project from `main` |

---

# PHASE 1 — Gateway Foundation
**Owner:** aryanketkar-15 · **Branch:** `aryan/gateway`

---

## Milestone 1.1 — Policy loader, registry and default deny
**Depends on:** 0.3

**1. Milestone Name** — Per-organisation policy files with default deny (R02, R03-req).

**2. Objective** — Load `bank.yaml` (and later hospital/shop) and refuse any unknown agent, action or destination.

**3. Tasks to Complete**
- [ ] `gateway/policy/bank.yaml` (from Final Solution §10)
- [ ] `gateway/policy_loader.py`: load, validate with Pydantic, compute `policy_hash` (SHA-256 of canonical YAML)
- [ ] `registry.knows(agent, action)`, `registry.destination_allowed(dest)`
- [ ] `effective_permissions(agent, human)` = agent actions ∩ human's role actions
- [ ] Reject malformed policy at startup (fail closed)

**4. Files / Modules Affected** — `gateway/policy/bank.yaml`, `gateway/policy_loader.py`, `gateway/registry.py`, `tests/test_policy.py`

**5. Implementation Guidance**
- **PyYAML** is used because policies must be readable on stage; JSON would be harder to read.
- Canonical hash: `json.dumps(yaml.safe_load(text), sort_keys=True, separators=(",", ":"))` → SHA-256. This value goes into seals and logs.
- Use `yaml.safe_load` only (never `yaml.load`) — untrusted YAML can execute code.
- Policy is loaded once at startup and on explicit `POST /policy/reload` (logged).

**6. Test Cases**

| ID | Scenario | Preconditions | Steps | Expected Result | Status |
|---|---|---|---|---|---|
| T1.1-1 | Load valid bank policy | bank.yaml | `load("bank")` | Policy object, hash 64 hex chars | ☐ |
| T1.1-2 | Known agent+action | Loaded | `knows("refund-agent","refund")` | True | ☐ |
| T1.1-3 | Unknown agent | Loaded | `knows("ghost","refund")` | False | ☐ |
| T1.1-4 | Known agent, unlisted action | Loaded | `knows("refund-agent","transfer")` | False | ☐ |
| T1.1-5 | Unknown destination | Loaded | `destination_allowed("ftp_server")` | False | ☐ |
| T1.1-6 | Malformed YAML | Broken file | Start gateway | Startup fails with clear error | ☐ |
| T1.1-7 | Hash stability | — | Reorder keys in YAML, reload | Same hash | ☐ |
| T1.1-8 | Hash sensitivity | — | Change one limit | Different hash | ☐ |
| T1.1-9 | Confused deputy | Agent allowed `transfer`, human role not | `effective_permissions` | `transfer` excluded | ☐ |

**7. Verification Checklist**
- [ ] `pytest tests/test_policy.py -q` all green
- [ ] Policy hash printed at startup
- [ ] No `yaml.load(` in codebase (`grep -r "yaml.load(" gateway`)

**8. Completion Criteria** — All T1.1 pass; default deny proven for agent, action, destination.

**9. Git Checkpoint**
```bash
git status
git add gateway/policy gateway/policy_loader.py gateway/registry.py tests/test_policy.py
git commit -m "M1.1: per-org policy loader, registry, effective permissions, default deny (R02, R3)"
git push origin aryan/gateway
```

**10. Rollback** — E.5. Policy changes are data, so a bad policy can also be fixed by reverting only `gateway/policy/*.yaml`.

---

## Milestone 1.2 — Signed requests, nonces and timestamps
**Depends on:** 1.1

**1. Milestone Name** — `POST /propose` accepts only authentic, fresh, unreplayed requests (R01).

**2. Objective** — Requests tampered in transit, replayed, or sent by impostors are blocked before any analysis.

**3. Tasks to Complete**
- [ ] `gateway/verify.py`: HMAC-SHA256 over canonical body (without `sig`)
- [ ] Per-agent secrets loaded from `.env` (`AGENT_KEY_REFUND_AGENT=...`); `.env.example` committed with placeholders
- [ ] Nonce store (SQLite table `nonces`), reject reuse
- [ ] Reject timestamps older/newer than ±60 s
- [ ] `POST /propose` skeleton: verify → registry → return `Decision` (BLOCK or "PENDING_ANALYSIS" stub)
- [ ] Constant-time comparison (`hmac.compare_digest`)

**4. Files / Modules Affected** — `gateway/verify.py`, `gateway/main.py`, `gateway/db.py` (`nonces` table), `.env.example`, `tests/test_verify.py`

**5. Implementation Guidance**
- **HMAC** (stdlib) is used instead of public-key signatures because all agents and the gateway are local; it is fast and needs no extra library. Ed25519 can replace it later.
- Canonical body: `json.dumps(body_without_sig, sort_keys=True, separators=(",", ":"))`.
- **python-dotenv** is added to read secrets from `.env` — secrets never appear in code or git.

**6. Test Cases**

| ID | Scenario | Preconditions | Steps | Expected Result | Status |
|---|---|---|---|---|---|
| T1.2-1 | Valid signed request | Agent key in .env | POST correctly signed proposal | Not blocked by R01 | ☐ |
| T1.2-2 | Tampered argument | — | Sign, then change `amount` | BLOCK, rule R01 | ☐ |
| T1.2-3 | Wrong key | — | Sign with another agent's key | BLOCK R01 | ☐ |
| T1.2-4 | Replayed nonce | First request accepted | Resend identical request | BLOCK R01 "replay" | ☐ |
| T1.2-5 | Stale timestamp | — | `ts = now - 300` | BLOCK R01 "stale" | ☐ |
| T1.2-6 | Future timestamp | — | `ts = now + 300` | BLOCK R01 | ☐ |
| T1.2-7 | Missing signature | — | Omit `sig` | 422 validation error | ☐ |
| T1.2-8 | Unknown agent with valid format | — | Agent `ghost` | BLOCK R02 | ☐ |
| T1.2-9 | Secrets not in repo | — | `git grep -i "secret"` on tracked files | Only placeholders in `.env.example` | ☐ |

**7. Verification Checklist**
- [ ] All T1.2 pass
- [ ] `.env` absent from `git status`
- [ ] Every rejection returns a `Decision` with `rule` and `reason`

**8. Completion Criteria** — Only authentic, fresh, first-use requests pass R01/R02.

**9. Git Checkpoint**
```bash
git status
git add gateway/verify.py gateway/main.py gateway/db.py .env.example tests/test_verify.py
git commit -m "M1.2: HMAC-signed proposals with nonce and timestamp checks (R01)"
git push origin aryan/gateway
```
Do not commit: `.env`.

**10. Rollback** — E.5. If keys leaked into a commit: rotate every key in `.env` immediately, then `git revert`; treat old keys as compromised.

---

## Milestone 1.3 — Hash-chained audit log
**Depends on:** 1.2

**1. Milestone Name** — Tamper-evident log of every decision, including refusals (R8, R10).

**2. Objective** — Every call to `/propose` (and later approvals, voids, promotions) writes an entry linked to the previous one; any edit is detectable.

**3. Tasks to Complete**
- [ ] `audit_log` table: `seq, prev_hash, ts, agent, action, payload_json, decision, rule, decision_path, policy_hash, entry_hash`
- [ ] `audit.append(entry)` computes `entry_hash = sha256(prev_hash + canonical(entry))`
- [ ] `audit.verify()` returns first broken `seq` or OK
- [ ] `GET /audit`, `POST /audit/verify`
- [ ] Log rejections from 1.2 too
- [ ] Payload stores **full decision inputs** (needed later for replay, 6.3)

**4. Files / Modules Affected** — `gateway/audit.py`, `gateway/db.py`, `gateway/main.py`, `tests/test_audit.py`

**5. Implementation Guidance**
- Genesis entry uses `prev_hash = "0"*64`.
- Appends happen inside the same DB transaction as the decision so a crash can't leave a decision unlogged.
- Store `payload_json` canonical (sorted keys) so re-hashing is deterministic.

**6. Test Cases**

| ID | Scenario | Preconditions | Steps | Expected Result | Status |
|---|---|---|---|---|---|
| T1.3-1 | Chain builds | Empty log | Append 5 entries | `verify()` OK | ☐ |
| T1.3-2 | Edit detection | 5 entries | Change `decision` of seq 3 via sqlite | `verify()` → broken at 3 | ☐ |
| T1.3-3 | Deletion detection | 5 entries | Delete seq 2 | Broken at 3 | ☐ |
| T1.3-4 | Insertion detection | 5 entries | Insert forged row | Broken | ☐ |
| T1.3-5 | Refusals logged | — | Send tampered request (T1.2-2) | Entry with BLOCK R01 exists | ☐ |
| T1.3-6 | Decision path recorded | — | Any request | `decision_path` field present | ☐ |
| T1.3-7 | Regression | — | Re-run T1.2 suite | All still pass | ☐ |

**7. Verification Checklist**
- [ ] Manual tamper with DB Browser for SQLite → `/audit/verify` names the row
- [ ] Every T1.2 rejection appears in the log

**8. Completion Criteria** — All decisions logged; tampering detected; regression green.

**9. Git Checkpoint**
```bash
git status
git add gateway/audit.py gateway/db.py gateway/main.py tests/test_audit.py
git commit -m "M1.3: hash-chained audit log with verify endpoint (R8, R10)"
git push origin aryan/gateway
```

**10. Rollback** — E.5. The log schema must not change after this without a migration note in the journal.

### ✅ Phase 1 Completion Checkpoint

| Item | Value |
|---|---|
| Completed | 1.1 ☐ · 1.2 ☐ · 1.3 ☐ |
| Tests passed | ___ / 25 |
| Known issues | |
| Merge & tag | merge `aryan/gateway` → `main`; `git tag phase-1-ok && git push origin phase-1-ok` |
| Commit hash | |
| Overall verification | Signed request reaches registry; bad requests blocked and logged; chain verifies |
| **Go / No-Go** | Go when R01/R02 + logging work on `main` |

---

# PHASE 2 — Effect Resolution (Sandbox)
**Owner:** chetanagrawal721 · **Branch:** `chetan/effects`

---

## Milestone 2.1 — Bank seed database and sandbox copies
**Depends on:** 0.3

**1. Milestone Name** — Reproducible fictional bank database with sandbox copy utility.

**2. Objective** — Provide realistic fictional data (with the demo traps planted) and a safe way to copy it for practice runs.

**3. Tasks to Complete**
- [ ] `gateway/seed/bank_seed.py` creates `gateway/data/bank.db` with `PRAGMA foreign_keys=ON`
- [ ] Tables: `customers`, `transactions`, `refunds` (FK → transactions, ON DELETE CASCADE), `vendors`, `inbox`, `invoices`, `outbox`, `budgets`
- [ ] Plant fixtures: C-1042 with 3 duplicate March charges; 58 other customers with March duplicates (→ 61 customers, 212 rows when the agent's query is too broad); 40 pending invoices; poisoned inbox email changing vendor V-17's account
- [ ] `sandbox.copy(domain) → path` and `sandbox.cleanup(path)`
- [ ] Fixed random seed so data is identical every run

**4. Files / Modules Affected** — `gateway/seed/bank_seed.py`, `gateway/sandbox.py`, `tests/test_seed.py`

**5. Implementation Guidance**
- **SQLite** is used because a database is a single file: copying the file *is* the sandbox, and real foreign-key cascades work.
- Use `sqlite3.connect(src).backup(sqlite3.connect(dst))` rather than `shutil.copy` — it is consistent even if the source is open.
- All names/numbers fictional (e.g. Faker with `seed(42)` if added; otherwise hand-written lists). **Faker** only if needed for volume; explain in journal if added.

**6. Test Cases**

| ID | Scenario | Preconditions | Steps | Expected Result | Status |
|---|---|---|---|---|---|
| T2.1-1 | Seed creates DB | — | `python -m gateway.seed.bank_seed` | bank.db with all tables | ☐ |
| T2.1-2 | Deterministic | — | Seed twice, hash table contents | Identical | ☐ |
| T2.1-3 | Fixtures present | Seeded | Count C-1042 March duplicates | 3 | ☐ |
| T2.1-4 | Broad match fixture | Seeded | Count all March duplicates | 212 rows / 61 customers | ☐ |
| T2.1-5 | FK cascade real | Seeded | Delete one transaction in a copy | Its refunds deleted too | ☐ |
| T2.1-6 | Sandbox isolation | Seeded | Copy, modify copy | Real DB unchanged | ☐ |
| T2.1-7 | Cleanup | Copy exists | `cleanup(path)` | File removed | ☐ |
| T2.1-8 | DB not tracked | — | `git status` | No `.db` files | ☐ |

**7. Verification Checklist**
- [ ] Fresh clone + seed script reproduces identical data
- [ ] Planted fixtures documented in `docs/fixtures.md`

**8. Completion Criteria** — Seed deterministic; sandbox isolated; fixtures present.

**9. Git Checkpoint**
```bash
git status
git add gateway/seed gateway/sandbox.py docs/fixtures.md tests/test_seed.py
git commit -m "M2.1: deterministic fictional bank seed with planted fixtures and sandbox copies"
git push origin chetan/effects
```
Do not commit: `gateway/data/*.db`, `gateway/data/sandbox/`.

**10. Rollback** — E.5; regenerate DB by re-running the seed after revert.

---

## Milestone 2.2 — Resolvers and the Effect object
**Depends on:** 2.1

**1. Milestone Name** — Practice-run resolvers that return the exact effect of an action.

**2. Objective** — For `update_contact`, `refund`, `transfer`, `payee_change`, measure what the action really changes, including cascades, without touching the real DB.

**3. Tasks to Complete**
- [ ] `Resolver` base class: `resolve(args, sandbox_conn) -> Effect`
- [ ] Table snapshot + diff: added / removed / modified primary keys per table
- [ ] Resolvers for the four bank actions (agent's query semantics deliberately broad for `refund` to reproduce the 61-customer case)
- [ ] `canonical_effect(effect)` (sorted PKs, sorted recipients) and `effect_hash`
- [ ] Reversibility classification per action type (from policy)

**4. Files / Modules Affected** — `gateway/resolver.py`, `gateway/resolvers/bank.py`, `gateway/diff.py`, `tests/test_resolver.py`

**5. Implementation Guidance**
```python
def snapshot(conn, table):           # {pk: row_tuple}
    return {r[0]: r for r in conn.execute(f"SELECT * FROM {table}")}

def table_diff(before, after):
    added    = after.keys() - before.keys()
    removed  = before.keys() - after.keys()
    modified = {k for k in before.keys() & after.keys() if before[k] != after[k]}
    return sorted(added), sorted(removed), sorted(modified)
```
Run the action inside the sandbox copy, snapshot affected tables before/after, build `Effect.rows`. Table names come from a fixed whitelist (never from agent input) to avoid SQL injection.

**6. Test Cases**

| ID | Scenario | Preconditions | Steps | Expected Result | Status |
|---|---|---|---|---|---|
| T2.2-1 | Single update | Seeded | resolve `update_contact(C-0007, phone)` | 1 modified row | ☐ |
| T2.2-2 | Broad refund | Seeded | resolve `refund(C-1042, March)` | 212 rows, 61 customers | ☐ |
| T2.2-3 | Cascade visible | Seeded | resolve a delete with dependents | Rows in both tables listed | ☐ |
| T2.2-4 | Real DB untouched | — | Resolve anything, hash real DB | Hash unchanged | ☐ |
| T2.2-5 | Effect hash stable | — | Resolve twice | Same hash | ☐ |
| T2.2-6 | Effect hash sensitive | — | Change one argument | Different hash | ☐ |
| T2.2-7 | Unknown action | — | resolve `drop_table` | Error → caller BLOCKs | ☐ |
| T2.2-8 | Injection attempt | — | `customer="C-1' OR 1=1 --"` | Parameterised query; 0 rows or validation error | ☐ |

**7. Verification Checklist**
- [ ] Counts match manual SQL for every fixture
- [ ] No string-formatted SQL with agent input (`grep -n "f\"SELECT" gateway/resolvers`)

**8. Completion Criteria** — Four resolvers produce exact, reproducible effects; real DB never changes.

**9. Git Checkpoint**
```bash
git status
git add gateway/resolver.py gateway/resolvers gateway/diff.py tests/test_resolver.py
git commit -m "M2.2: sandbox resolvers returning exact effects with cascades (R5)"
git push origin chetan/effects
```

**10. Rollback** — E.5.

---

## Milestone 2.3 — Data labels and destinations
**Depends on:** 2.2

**1. Milestone Name** — Effects carry data labels and destination classes.

**2. Objective** — Every effect lists which sensitivity labels it touches (PII, SECRET, UNTRUSTED) and where data would go, so rules can check clearance.

**3. Tasks to Complete**
- [ ] Label catalog from policy (`labels:` section) with `label_catalog_version`
- [ ] `label_effect(effect)` — collect labels for affected columns/rows; UNTRUSTED for rows sourced from `inbox`
- [ ] Destination classifier: internal vs external email (domain list), payment rail, shared drive
- [ ] File objects (`shared_files` table) store labels of rows written into them
- [ ] `label_path` provenance list

**4. Files / Modules Affected** — `gateway/labels.py`, `gateway/resolvers/bank.py`, `tests/test_labels.py`

**5. Implementation Guidance** — Labels are computed **by the gateway** from what it resolved, never reported by agents. Unlabelled columns default to INTERNAL (strict default).

**6. Test Cases**

| ID | Scenario | Preconditions | Steps | Expected Result | Status |
|---|---|---|---|---|---|
| T2.3-1 | PII detected | Seeded | Effect touching `customers.phone` | `PII` in labels | ☐ |
| T2.3-2 | SECRET detected | — | Effect touching `account_no` | `SECRET` | ☐ |
| T2.3-3 | Untrusted source | Poisoned inbox | `payee_change` from inbox | `UNTRUSTED` | ☐ |
| T2.3-4 | External destination | — | Recipient `x@agency.com` | `external_email` | ☐ |
| T2.3-5 | Unlabelled column | — | New column without label | `INTERNAL` | ☐ |
| T2.3-6 | File inherits labels | — | Write PII rows to file, then resolve send of file | Send effect has `PII`, label_path includes file | ☐ |
| T2.3-7 | Regression | — | Re-run T2.2 | Pass | ☐ |

**7. Verification Checklist** — [ ] label_catalog_version included in Effect metadata · [ ] provenance path human-readable

**8. Completion Criteria** — Labels and destinations correct for all fixtures.

**9. Git Checkpoint**
```bash
git status
git add gateway/labels.py gateway/resolvers tests/test_labels.py
git commit -m "M2.3: effect-level data labels, destinations and provenance path"
git push origin chetan/effects
```

**10. Rollback** — E.5.

### ✅ Phase 2 Completion Checkpoint

| Item | Value |
|---|---|
| Completed | 2.1 ☐ · 2.2 ☐ · 2.3 ☐ |
| Tests passed | ___ / 23 |
| Merge & tag | merge `chetan/effects` → `main`; `phase-2-ok` |
| Commit hash | |
| Overall verification | `/propose` (from Phase 1) can call a resolver and return an Effect for every bank action |
| **Go / No-Go** | Go when effects match manual counts and real DB is never modified |

---

# PHASE 3 — Decision Engine
**Owner:** chetanagrawal721 · **Branch:** `chetan/effects`

---

## Milestone 3.1 — Expected envelope (policy default) and envelope check
**Depends on:** 2.3

**1. Milestone Name** — Deterministic "is it doing more than asked?" check.

**2. Objective** — Compare the measured effect with an envelope of what the action should touch; return inside/outside with the offending rows.

**3. Tasks to Complete**
- [ ] `envelope.default_for(action, policy, args)` — scope from args (e.g. `customer=C-1042`), limits from policy
- [ ] `envelope.check(effect, envelope)` → `{inside: bool, offending_rows, offending_recipients, over_amount}`
- [ ] Interface ready for the AI-built envelope (5.2) with `source` field

**4. Files / Modules Affected** — `gateway/envelope.py`, `tests/test_envelope.py`

**5. Implementation Guidance** — Scope check: every affected row must match scope keys (e.g. `customer_id == C-1042`). Limit checks: row count, amount, destinations. Pure functions only — no DB writes.

**6. Test Cases**

| ID | Scenario | Preconditions | Steps | Expected Result | Status |
|---|---|---|---|---|---|
| T3.1-1 | Inside envelope | Single-customer fixture | check | inside=True | ☐ |
| T3.1-2 | Outside: other customers | Broad refund effect | check | inside=False, 209 offending rows | ☐ |
| T3.1-3 | Outside: amount | Amount > max | check | over_amount reported | ☐ |
| T3.1-4 | Outside: destination | External recipient not allowed | check | offending_recipients listed | ☐ |
| T3.1-5 | Empty effect | 0 rows | check | inside=True | ☐ |
| T3.1-6 | Missing scope key | Args lack customer | default_for | Strictest policy envelope | ☐ |

**7. Verification Checklist** — [ ] offending rows exactly match manual query

**8. Completion Criteria** — Envelope check correct on all fixtures.

**9. Git Checkpoint**
```bash
git status
git add gateway/envelope.py tests/test_envelope.py
git commit -m "M3.1: expected-effect envelope with deterministic inside/outside check"
git push origin chetan/effects
```

**10. Rollback** — E.5.

---

## Milestone 3.2 — Rules R01–R12, tiers and decide()
**Depends on:** 3.1, 1.3

**1. Milestone Name** — Deterministic ALLOW / HOLD / BLOCK with rule IDs (R2, R4, R5).

**2. Objective** — One pure function turns (proposal, effect, envelope, policy, budgets, AI result) into a verdict, rule ID and reason; plus the baseline (mode B) verdict for display.

**3. Tasks to Complete**
- [ ] `rules.py` implementing R03–R12 (R01/R02 already in Phase 1) per Final Solution §7.2
- [ ] Tier table §7.3
- [ ] `decide()`: first BLOCK among R01–R06, else strictest of R07–R12; `final = max(rule, ai)`
- [ ] `baseline_verdict()`: allowlist + argument binding only (mode B)
- [ ] Wire into `/propose`; log full inputs via audit

**4. Files / Modules Affected** — `gateway/rules.py`, `gateway/decide.py`, `gateway/main.py`, `tests/test_rules.py`

**5. Implementation Guidance** — Ordering `ALLOW < HOLD < BLOCK` as integers. `decide()` must be **pure** (same inputs → same output) — this enables replay (6.3) and the Attack Lab (9.1).

**6. Test Cases**

| ID | Scenario | Preconditions | Steps | Expected Result | Status |
|---|---|---|---|---|---|
| T3.2-1 | Phone update | Seeded | propose | ALLOW, R12 | ☐ |
| T3.2-2 | Broad refund | — | propose | BLOCK, R06; baseline ALLOW | ☐ |
| T3.2-3 | PII to external | — | send file to agency | BLOCK, R05 | ☐ |
| T3.2-4 | Untrusted payee change | Poisoned inbox | propose | HOLD, R07 | ☐ |
| T3.2-5 | Protected class | — | `grant_role` | HOLD, R09 | ☐ |
| T3.2-6 | Self-permission change | — | agent edits own role | BLOCK, R03 | ☐ |
| T3.2-7 | Honeytoken | — | `export_all_credentials` | BLOCK, R03, agent frozen | ☐ |
| T3.2-8 | Tier T3 | Irreversible > 1,000 | propose | HOLD ×2 approvers | ☐ |
| T3.2-9 | Default deny | Nothing matches | — | BLOCK, R99 | ☐ |
| T3.2-10 | AI cannot lower | AI returns ALLOW, rules HOLD | decide | HOLD | ☐ |
| T3.2-11 | Determinism | — | decide twice same inputs | Identical | ☐ |
| T3.2-12 | Regression | — | Phase 1 & 2 tests | Pass | ☐ |

**7. Verification Checklist** — [ ] every decision logged with rule + path · [ ] baseline verdict present on every Decision

**8. Completion Criteria** — All bank fixtures produce expected verdicts matching `lab/suite.yaml` expectations for mode C.

**9. Git Checkpoint**
```bash
git status
git add gateway/rules.py gateway/decide.py gateway/main.py tests/test_rules.py
git commit -m "M3.2: deterministic rules R01-R12, tiers, decide() and baseline verdict (R2, R4)"
git push origin chetan/effects
```

**10. Rollback** — E.5.

---

## Milestone 3.3 — Resource-keyed budgets
**Depends on:** 3.2

**1. Milestone Name** — Cumulative limits charged on measured effect (R08).

**2. Objective** — Stop salami slicing and budget splitting across agents.

**3. Tasks to Complete**
- [ ] `budgets` table: `key, window_start, used`
- [ ] Keys `(agent, resource)` and `(resource)`; sliding 1-hour window
- [ ] Charge only on ALLOW/executed; check before decide
- [ ] Charge + check in one transaction (`BEGIN IMMEDIATE`) to avoid races
- [ ] Budget snapshot included in audit payload

**4. Files / Modules Affected** — `gateway/budgets.py`, `gateway/rules.py`, `tests/test_budgets.py`

**5. Implementation Guidance** — For demo, a "fast-forward" helper in tests inserts many small refunds quickly.

**6. Test Cases**

| ID | Scenario | Preconditions | Steps | Expected Result | Status |
|---|---|---|---|---|---|
| T3.3-1 | Under budget | Fresh | 3 refunds | ALLOW | ☐ |
| T3.3-2 | Salami | — | 500 × ₹1,000 | HOLD at the refund that exceeds | ☐ |
| T3.3-3 | Split across agents | 3 agents | Each under own limit, total over | HOLD (resource key) | ☐ |
| T3.3-4 | Window reset | Budget used | Advance clock 61 min | ALLOW again | ☐ |
| T3.3-5 | Concurrency | Two threads | Charge simultaneously | Never exceeds limit | ☐ |
| T3.3-6 | Blocked actions not charged | — | BLOCK then check | Budget unchanged | ☐ |
| T3.3-7 | Regression | — | T3.2 | Pass | ☐ |

**7. Verification Checklist** — [ ] budget snapshot in audit entries

**8. Completion Criteria** — Budgets enforce per-agent and per-resource limits atomically.

**9. Git Checkpoint**
```bash
git status
git add gateway/budgets.py gateway/rules.py tests/test_budgets.py
git commit -m "M3.3: resource-keyed cumulative budgets charged on resolved effect (R08)"
git push origin chetan/effects
```

**10. Rollback** — E.5.

### ✅ Phase 3 Completion Checkpoint

| Item | Value |
|---|---|
| Completed | 3.1 ☐ · 3.2 ☐ · 3.3 ☐ |
| Tests passed | ___ / 25 |
| Merge & tag | `chetan/effects` → `main`; `phase-3-ok` |
| Overall verification | Every bank case in `lab/suite.yaml` gets its expected mode-C verdict (before seals) |
| **Go / No-Go** | Go when decide() is deterministic and matches the suite |

---

# PHASE 4 — Seal & Execution (the core)
**Owner:** aryanketkar-15 · **Branch:** `aryan/gateway` · **Must finish by hour 6**

---

## Milestone 4.1 — Approvals and separation of duties
**Depends on:** 3.2

**1. Milestone Name** — Human approvals with role checks (R7).

**2. Objective** — HOLD actions are approved or rejected only by authorised humans who are not the requester's owner; tier-3 actions need two distinct approvers.

**3. Tasks to Complete**
- [ ] Hardcoded users in `gateway/users.yaml`: `priya` (ops officer), `rahul` (branch manager), `meera` (staff, requester)
- [ ] Demo auth: `X-User` header + per-user token from `.env` (stated as demo-only)
- [ ] `POST /approve`, `POST /reject` with checks: user exists, role authorised for tier, user ≠ requester/owner, not already approved by same user
- [ ] `approvals` table; all attempts (incl. refused) logged

**4. Files / Modules Affected** — `gateway/approvals.py`, `gateway/users.yaml`, `gateway/main.py`, `tests/test_approvals.py`

**5. Implementation Guidance** — Authorisation is enforced **server-side**; the UI only hides buttons. Agents never have user tokens.

**6. Test Cases**

| ID | Scenario | Preconditions | Steps | Expected Result | Status |
|---|---|---|---|---|---|
| T4.1-1 | Valid approval | HOLD action by meera | priya approves | Approved | ☐ |
| T4.1-2 | Self-approval | — | meera approves own | 403, logged | ☐ |
| T4.1-3 | Agent approves | — | agent key used on /approve | 401 | ☐ |
| T4.1-4 | Missing token | — | No X-User | 401 | ☐ |
| T4.1-5 | Wrong token | — | Bad token | 401 | ☐ |
| T4.1-6 | Tier 3 single approver | T3 action | priya approves | Still pending (1 of 2) | ☐ |
| T4.1-7 | Same approver twice | — | priya approves twice | Second refused | ☐ |
| T4.1-8 | Approve non-HOLD | ALLOW action | approve | 409 | ☐ |
| T4.1-9 | Reject | HOLD | rahul rejects | Rejected, logged | ☐ |

**7. Verification Checklist** — [ ] every refused attempt in audit log · [ ] tokens only in `.env`

**8. Completion Criteria** — SoD enforced; unauthorised access impossible via API.

**9. Git Checkpoint**
```bash
git status
git add gateway/approvals.py gateway/users.yaml gateway/main.py tests/test_approvals.py
git commit -m "M4.1: approvals with separation of duties and tiered approvers (R7)"
git push origin aryan/gateway
```
Do not commit: user tokens in `.env`.

**10. Rollback** — E.5.

---

## Milestone 4.2 — Effect seal with typed drift
**Depends on:** 4.1

**1. Milestone Name** — Approval tokens bound to the measured effect (R6).

**2. Objective** — An approval produces a signed seal; any later difference in arguments, effect, labels, policy or state voids it with a named reason.

**3. Tasks to Complete**
- [ ] `seal.create(decision, approvers)` → token with `action_hash, effect_hash, label_path_hash, label_catalog_ver, policy_ver, state_ver, requester, tier, approvers, nonce, expiry`, signed with gateway key (HMAC)
- [ ] `state_ver` = hash of current contents of affected rows
- [ ] `seal.check(token, fresh_effect, fresh_state, current_policy)` → `OK` or one of `args_drift, effect_drift, label_drift, policy_drift, state_drift, replay, expired, bad_signature`
- [ ] Seals stored in `seals` table; nonce marked used on execute

**4. Files / Modules Affected** — `gateway/seal.py`, `gateway/db.py`, `tests/test_seal.py`

**5. Implementation Guidance** — Compare components **one by one** in a fixed order (signature → expiry → replay → args → policy → label → effect → state) so the reported reason is the most fundamental one.

**6. Test Cases**

| ID | Scenario | Preconditions | Steps | Expected Result | Status |
|---|---|---|---|---|---|
| T4.2-1 | Unchanged | Sealed 40 invoices | check | OK | ☐ |
| T4.2-2 | Effect drift | Insert 3,960 matching invoices | check | `effect_drift` (40 → 4,000) | ☐ |
| T4.2-3 | Args drift | Change amount | check | `args_drift` | ☐ |
| T4.2-4 | Policy drift | Edit policy limit, reload | check | `policy_drift` | ☐ |
| T4.2-5 | Label drift | Relabel a column | check | `label_drift` | ☐ |
| T4.2-6 | State drift | Same rows, edited values | check | `state_drift` | ☐ |
| T4.2-7 | Replay | Seal used once | check again | `replay` | ☐ |
| T4.2-8 | Expired | TTL passed | check | `expired` | ☐ |
| T4.2-9 | Forged token | Edit token field | check | `bad_signature` | ☐ |
| T4.2-10 | Key reorder in args | Same args reordered | check | OK | ☐ |

**7. Verification Checklist** — [ ] each drift type produces a distinct audit entry

**8. Completion Criteria** — All 10 cases pass.

**9. Git Checkpoint**
```bash
git status
git add gateway/seal.py gateway/db.py tests/test_seal.py
git commit -m "M4.2: effect-bound seal with typed drift detection (R6)"
git push origin aryan/gateway
```

**10. Rollback** — E.5.

---

## Milestone 4.3 — One-transaction execution and transactional outbox
**Depends on:** 4.2

**1. Milestone Name** — Execute only what was sealed; irreversible sends only after commit.

**2. Objective** — The gateway executes approved/allowed actions on the real DB inside one transaction, verifies the actual effect equals the sealed effect, and delivers emails/payments only after commit.

**3. Tasks to Complete**
- [ ] `execute_sealed(token)`: `BEGIN IMMEDIATE` → snapshot → run action on real DB → diff → `seal.check` → match: write outbox rows → `COMMIT`; mismatch: `ROLLBACK`, VOID, re-queue as HOLD
- [ ] `outbox` rows (`pending`) for `send_email`, `pay`; `delivery_worker` thread marks `sent` and writes to `delivered_messages`
- [ ] ALLOW decisions auto-execute through the same path (unsealed but effect-checked)
- [ ] `GET /status/{id}` for agents
- [ ] Demo helper `POST /demo/insert-invoices` (judge-clickable drift trigger)

**4. Files / Modules Affected** — `gateway/execute.py`, `gateway/outbox.py`, `gateway/main.py`, `tests/test_execute.py`

**5. Implementation Guidance** — Execution on the real DB inside a transaction makes "re-resolve" and "execute" the same step: the diff is measured on the real data before commit, so there is no gap for the world to change.

**6. Test Cases**

| ID | Scenario | Preconditions | Steps | Expected Result | Status |
|---|---|---|---|---|---|
| T4.3-1 | Happy path | Approved 40-row seal | execute | 40 rows changed; DONE | ☐ |
| T4.3-2 | Drift at execution | Insert invoices after approval | execute | VOID effect_drift; real DB unchanged | ☐ |
| T4.3-3 | Email only after commit | Approved send | execute | outbox pending → sent after commit | ☐ |
| T4.3-4 | Email on failure | Drift on send | execute | No outbox row | ☐ |
| T4.3-5 | Crash mid-execution | Kill process inside transaction | Restart | DB unchanged; no outbox row | ☐ |
| T4.3-6 | Replay execute | Executed seal | execute again | Refused `replay` | ☐ |
| T4.3-7 | Agent bypass | — | Agent code tries to open bank.db | No path/credentials in agents/ | ☐ |
| T4.3-8 | Concurrent executes | Two seals same rows | Execute in parallel | One succeeds; other VOID state_drift | ☐ |
| T4.3-9 | Regression | — | Phases 1–3 + 4.1–4.2 | Pass | ☐ |

**7. Verification Checklist**
- [ ] Real DB hash unchanged after any VOID
- [ ] `delivered_messages` only contains committed sends
- [ ] Full demo beat 5 (approve 40 → insert → VOID) works by clicking through the API

**8. Completion Criteria** — **The core of SEALGATE works end to end.** All tests pass.

**9. Git Checkpoint**
```bash
git status
git add gateway/execute.py gateway/outbox.py gateway/main.py tests/test_execute.py
git commit -m "M4.3: one-transaction sealed execution and transactional outbox"
git push origin aryan/gateway
```

**10. Rollback** — E.5. If this milestone is unstable at hour 6, revert to `phase-3-ok` + 4.2 and debug on a separate branch `aryan/execute-fix`.

### ✅ Phase 4 Completion Checkpoint (HOUR-6 GATE)

| Item | Value |
|---|---|
| Completed | 4.1 ☐ · 4.2 ☐ · 4.3 ☐ |
| Tests passed | ___ / 28 |
| Merge & tag | `aryan/gateway` → `main`; `phase-4-ok` |
| Overall verification | Propose → HOLD → approve → execute; drift → VOID; send → outbox after commit |
| **Go / No-Go** | **No-Go blocks everything except frontend.** All hands fix Phase 4 first. |

---

# PHASE 5 — AI Layer (escalate-only)
**Owner:** atharvg44 · **Branch:** `atharv/ai-agents`

---

## Milestone 5.1 — AI client, schema validation and fallback
**Depends on:** 0.3 (develops in parallel; plugs into 3.2)

**1. Milestone Name** — Safe AI wrapper that can only escalate (R4, R9, R10).

**2. Objective** — A single module calls the LLM with a timeout, validates output against a strict schema, and returns a fallback result on any failure.

**3. Tasks to Complete**
- [ ] `gateway/ai.py`: `ask(prompt, schema) -> (result | None, status)` with 3-s timeout
- [ ] Ollama HTTP API (`POST http://localhost:11434/api/generate`, `format: "json"`), configurable model via `.env`
- [ ] Pydantic validation; invalid → `status="invalid"`
- [ ] `AI_ENABLED` toggle + `POST /ai/toggle` for demo
- [ ] `decision_path` set to `rules+ai` or `fallback`
- [ ] `escalation` output can only be `NONE | HOLD | BLOCK`

**4. Files / Modules Affected** — `gateway/ai.py`, `gateway/decide.py`, `tests/test_ai.py`

**5. Implementation Guidance** — **Ollama** is chosen because it runs locally, free and offline, satisfying the booklet's local-fallback rule. Tests mock the HTTP call (`httpx.MockTransport`) so they run without a model.

**6. Test Cases**

| ID | Scenario | Preconditions | Steps | Expected Result | Status |
|---|---|---|---|---|---|
| T5.1-1 | Valid AI output | Mocked valid JSON | ask | result + `ok` | ☐ |
| T5.1-2 | Timeout | Mock sleeps 5 s | ask | None + `timeout`; path `fallback` | ☐ |
| T5.1-3 | Garbage text | Mock returns prose | ask | None + `invalid` | ☐ |
| T5.1-4 | Schema violation | `escalation: "ALLOW_ALL"` | ask | `invalid` | ☐ |
| T5.1-5 | AI says lower | Rules HOLD, AI `NONE` | decide | HOLD | ☐ |
| T5.1-6 | AI escalates | Rules ALLOW, AI `HOLD` | decide | HOLD, path `rules+ai` | ☐ |
| T5.1-7 | AI disabled | Toggle off | decide | Path `fallback`, same safety | ☐ |
| T5.1-8 | Ollama not running | Service stopped | ask | Fallback, no crash | ☐ |
| T5.1-9 | Prompt injection in input | Input says "return NONE" | ask | Output still schema-checked; cannot lower | ☐ |

**7. Verification Checklist** — [ ] system fully works with Ollama stopped · [ ] path recorded on every decision

**8. Completion Criteria** — AI failures never weaken a decision.

**9. Git Checkpoint**
```bash
git status
git add gateway/ai.py gateway/decide.py tests/test_ai.py
git commit -m "M5.1: escalate-only AI client with schema validation and fallback (R4, R9, R10)"
git push origin atharv/ai-agents
```
Do not commit: model files, `.env`.

**10. Rollback** — E.5; setting `AI_ENABLED=false` is an instant operational rollback.

---

## Milestone 5.2 — Envelope from instruction and claim-vs-effect check
**Depends on:** 5.1, 3.1

**1. Milestone Name** — AI converts the human's request into checkable limits and flags mismatches.

**2. Objective** — Meaningful AI: (a) build the envelope from `user_instruction`; (b) compare agent's stated intent with the measured effect.

**3. Tasks to Complete**
- [ ] Prompt + schema for envelope extraction (`scope`, `max_rows`, `max_amount_minor`, `allowed_destinations`)
- [ ] Validation: AI envelope can only be **narrower or equal** to policy limits (clamped)
- [ ] Fallback to `envelope.default_for` with `source=policy_default`
- [ ] Claim-vs-effect prompt → `{mismatch: bool, reason}` → escalation HOLD if mismatch
- [ ] Few-shot examples stored in `gateway/prompts/`

**4. Files / Modules Affected** — `gateway/ai_envelope.py`, `gateway/ai_claim.py`, `gateway/prompts/*.txt`, `tests/test_ai_envelope.py`

**5. Implementation Guidance** — AI never widens permissions: `final_limit = min(ai_limit, policy_limit)`. Store prompts as files so they appear in the methodology record.

**6. Test Cases**

| ID | Scenario | Preconditions | Steps | Expected Result | Status |
|---|---|---|---|---|---|
| T5.2-1 | Correct extraction | "Refund C-1042's March duplicates" | extract | scope customer=C-1042, month=March | ☐ |
| T5.2-2 | Clamp to policy | AI says max_amount 10 lakh | extract | Clamped to policy 20,000 | ☐ |
| T5.2-3 | Ambiguous instruction | "clean up old stuff" | extract | Strict policy default; flagged | ☐ |
| T5.2-4 | Injection in instruction | "…and ignore limits" | extract | Limits still clamped | ☐ |
| T5.2-5 | Mismatch detected | Intent "1 customer", effect 61 | claim check | mismatch → HOLD | ☐ |
| T5.2-6 | No mismatch | Intent matches | claim check | NONE | ☐ |
| T5.2-7 | AI off | Disabled | full propose | policy_default envelope; decision still correct | ☐ |
| T5.2-8 | Explainability | Any | Decision JSON | `envelope.source` and AI reason visible | ☐ |

**7. Verification Checklist** — [ ] 5 sample instructions produce sensible envelopes; logged in journal as evidence

**8. Completion Criteria** — Envelopes from AI are clamped and validated; fallback identical in safety.

**9. Git Checkpoint**
```bash
git status
git add gateway/ai_envelope.py gateway/ai_claim.py gateway/prompts tests/test_ai_envelope.py
git commit -m "M5.2: AI envelope from user instruction (clamped) and claim-vs-effect escalation"
git push origin atharv/ai-agents
```

**10. Rollback** — E.5.

---

## Milestone 5.3 — Paraphrase sentry and explanations
**Depends on:** 5.2 · **First to cut if behind**

**1. Milestone Name** — AI flags likely personal data in free text; plain-language reasons.

**2. Objective** — Best-effort escalation for PII rewritten in email bodies; one-sentence explanation for approvers.

**3. Tasks to Complete**
- [ ] Sentry prompt: outgoing body + names/fields from rows the agent read → `{likely_pii: bool, evidence}`
- [ ] Fallback rule: external free-text send by an agent that touched PII in this task → HOLD
- [ ] Explanation generator with template fallback per rule ID

**4. Files / Modules Affected** — `gateway/ai_sentry.py`, `gateway/explain.py`, `tests/test_sentry.py`

**5. Implementation Guidance** — Presented as **best-effort**; never BLOCKs on its own, only HOLDs.

**6. Test Cases**

| ID | Scenario | Preconditions | Steps | Expected Result | Status |
|---|---|---|---|---|---|
| T5.3-1 | Paraphrased PII | Body describes customers by name | sentry | HOLD | ☐ |
| T5.3-2 | Generic body | Newsletter text | sentry | NONE | ☐ |
| T5.3-3 | AI off | Disabled, agent touched PII | external send | HOLD (fallback rule) | ☐ |
| T5.3-4 | Explanation present | Any HOLD | Decision | Non-empty `reason` | ☐ |
| T5.3-5 | Explanation fallback | AI off | Decision | Template text | ☐ |

**7. Verification Checklist** — [ ] limitation recorded in journal

**8. Completion Criteria** — Sentry escalates sample paraphrase; never lowers.

**9. Git Checkpoint**
```bash
git status
git add gateway/ai_sentry.py gateway/explain.py tests/test_sentry.py
git commit -m "M5.3: best-effort paraphrase sentry and approver explanations"
git push origin atharv/ai-agents
```

**10. Rollback** — E.5 or disable via config flag `SENTRY_ENABLED=false`.

### ✅ Phase 5 Completion Checkpoint

| Item | Value |
|---|---|
| Completed | 5.1 ☐ · 5.2 ☐ · 5.3 ☐ |
| Tests passed | ___ / 22 |
| Merge & tag | `atharv/ai-agents` → `main`; `phase-5-ok` |
| Overall verification | Same suite results with AI on and off (safety); `decision_path` correct |
| **Go / No-Go** | Go if AI-off run is at least as strict as AI-on |

---

# PHASE 6 — Signature Features

---

## Milestone 6.1 — Smallest safe version
**Owner:** chetanagrawal721 · **Depends on:** 4.3, 3.1

**1. Milestone Name** — One-click minimal safe alternative for blocked/held actions.

**2. Objective** — Compute the smallest change to the resolved effect that flips the decision, run it through the full gate, and let the approver accept it.

**3. Tasks to Complete**
- [ ] For R05/R06: remove offending recipients/rows → explicit action (`WHERE id IN (...)`, explicit recipient list)
- [ ] For tier/limit rules: reduce to boundary using declared ordering (oldest first, by PK)
- [ ] Re-run reduced action through resolve → decide; only offer if result is ALLOW or lower tier
- [ ] Never offer for hard BLOCK classes (R01–R04, honeytoken, SECRET)
- [ ] `POST /safe-version/{id}` → new decision → seal → execute; requester notified

**4. Files / Modules Affected** — `gateway/safe_version.py`, `gateway/main.py`, `tests/test_safe_version.py`

**5. Implementation Guidance** — Deterministic, no AI. Never suggest splitting an action into several smaller ones (budget evasion).

**6. Test Cases**

| ID | Scenario | Preconditions | Steps | Expected Result | Status |
|---|---|---|---|---|---|
| T6.1-1 | Broad refund | BLOCK R06 | compute | 3 refunds C-1042 → ALLOW | ☐ |
| T6.1-2 | External recipients | BLOCK R05 | compute | Remove externals → ALLOW | ☐ |
| T6.1-3 | Honeytoken | BLOCK R03 | compute | No safe version offered | ☐ |
| T6.1-4 | Accept | Offered | POST /safe-version | New seal bound to reduced effect; executed | ☐ |
| T6.1-5 | Reduced still unsafe | Edge fixture | compute | Not offered | ☐ |
| T6.1-6 | No split | Over budget | compute | No "split" suggestion | ☐ |
| T6.1-7 | Regression | — | Phase 4 tests | Pass | ☐ |

**7. Verification Checklist** — [ ] audit shows original BLOCK + accepted reduced version linked

**8. Completion Criteria** — Demo beat 3 works via API.

**9. Git Checkpoint**
```bash
git status
git add gateway/safe_version.py gateway/main.py tests/test_safe_version.py
git commit -m "M6.1: deterministic smallest-safe-version engine with re-sealing"
git push origin chetan/effects
```

**10. Rollback** — E.5; feature can be hidden in UI without code revert.

---

## Milestone 6.2 — Shadow Mode
**Owner:** chetanagrawal721 · **Depends on:** 6.1, 4.3

**1. Milestone Name** — Held agents keep working in a sandbox; humans approve the result.

**2. Objective** — After a HOLD with `shadow_mode.on_hold`, route that agent's subsequent actions to a session sandbox, record them, show total diff, and promote (replay with diff equality) or discard.

**3. Tasks to Complete**
- [ ] `shadow_sessions`, `shadow_steps` tables
- [ ] Routing: actions from a shadowed agent run on session sandbox; agent receives normal-looking ALLOW (marked `shadow` in log)
- [ ] `GET /shadow/{sid}`: steps + cumulative diff vs real
- [ ] `POST /promote/{sid}`: one transaction on real → replay recorded **actions** (not the agent) → real diff must equal sandbox diff → commit, else rollback
- [ ] `POST /discard/{sid}`: delete sandbox, log
- [ ] Sandbox outbox never delivers

**4. Files / Modules Affected** — `gateway/shadow.py`, `gateway/main.py`, `tests/test_shadow.py`

**5. Implementation Guidance** — Promotion requires approvals per tier (SoD from 4.1).

**6. Test Cases**

| ID | Scenario | Preconditions | Steps | Expected Result | Status |
|---|---|---|---|---|---|
| T6.2-1 | Enter shadow | Untrusted payee change HOLD | Next 3 actions | Run in sandbox; real unchanged | ☐ |
| T6.2-2 | Total diff | 4 steps | GET /shadow | Cumulative diff correct | ☐ |
| T6.2-3 | Promote ok | Real unchanged | promote | Real diff == sandbox diff; committed | ☐ |
| T6.2-4 | Promote with drift | Real changed meanwhile | promote | Rollback, VOID state_drift | ☐ |
| T6.2-5 | Discard | Session | discard | Real untouched; sandbox removed | ☐ |
| T6.2-6 | No sandbox emails | Shadow send | Check delivered | None delivered | ☐ |
| T6.2-7 | Self-promote | Requester promotes | promote | 403 | ☐ |
| T6.2-8 | Regression | — | 4.x, 6.1 | Pass | ☐ |

**7. Verification Checklist** — [ ] Demo beat 4 works end to end

**8. Completion Criteria** — Promotion verified by diff equality; discard leaves no trace on real.

**9. Git Checkpoint**
```bash
git status
git add gateway/shadow.py gateway/main.py tests/test_shadow.py
git commit -m "M6.2: Shadow Mode with recorded steps and diff-verified promotion"
git push origin chetan/effects
```
Do not commit: session sandbox files.

**10. Rollback** — E.5; disable with `shadow_mode.on_hold: false` in policy (falls back to plain HOLD).

---

## Milestone 6.3 — Replay and honeytoken freeze
**Owner:** aryanketkar-15 · **Depends on:** 1.3, 3.2

**1. Milestone Name** — Reproduce any past decision; freeze compromised agents.

**2. Objective** — Show that decisions are reproducible from stored inputs and that decoy actions freeze an agent.

**3. Tasks to Complete**
- [ ] `POST /audit/replay/{seq}`: load stored inputs + stored policy version → `decide()` → compare with stored verdict
- [ ] Policy versions stored (`policy_versions` table) on every load
- [ ] Agent `frozen` flag; frozen agents → BLOCK on every proposal until a human unfreezes

**4. Files / Modules Affected** — `gateway/audit.py`, `gateway/registry.py`, `tests/test_replay.py`

**5. Implementation Guidance** — Replay never touches live DBs; it uses only the stored Effect and budget snapshot.

**6. Test Cases**

| ID | Scenario | Preconditions | Steps | Expected Result | Status |
|---|---|---|---|---|---|
| T6.3-1 | Replay matches | Past decision | replay | Same verdict + rule | ☐ |
| T6.3-2 | Replay after policy change | Policy updated | replay old seq | Uses old policy; same verdict | ☐ |
| T6.3-3 | Tampered entry | Edited row | replay | Refused: chain broken | ☐ |
| T6.3-4 | Honeytoken freeze | — | call decoy | Agent frozen | ☐ |
| T6.3-5 | Frozen agent | Frozen | propose anything | BLOCK | ☐ |
| T6.3-6 | Unfreeze | Human | unfreeze | Proposals evaluated again | ☐ |

**7. Verification Checklist** — [ ] replay of 10 random entries all match

**8. Completion Criteria** — Replay deterministic; freeze works.

**9. Git Checkpoint**
```bash
git status
git add gateway/audit.py gateway/registry.py tests/test_replay.py
git commit -m "M6.3: decision replay against stored policy and honeytoken freeze"
git push origin aryan/gateway
```

**10. Rollback** — E.5.

### ✅ Phase 6 Completion Checkpoint

| Item | Value |
|---|---|
| Completed | 6.1 ☐ · 6.2 ☐ · 6.3 ☐ |
| Tests passed | ___ / 21 |
| Merge & tag | → `main`; `phase-6-ok` |
| Overall verification | Bank demo beats 2–5 run end to end via API |
| **Go / No-Go** | Go to full integration if Phase 4 regression still green |

---

# PHASE 7 — Agents & Domains

---

## Milestone 7.1 — Agents, tools and demo scenarios
**Owner:** atharvg44 · **Depends on:** 0.3 (mock), 1.2 (real signing)

**1. Milestone Name** — Scripted agents that can only propose.

**2. Objective** — Provide the agent side of every demo beat and suite case, plus a chat-facing interface.

**3. Tasks to Complete**
- [ ] `agents/tools.py`: `propose()` with HMAC signing; one function per action
- [ ] `agents/scenarios.py`: scripted sequences for each demo beat and domain
- [ ] `POST /demo/{scenario}` (gateway) triggers scenario; chat messages streamed as events
- [ ] Agents receive verdicts and produce chat replies ("Paused for review…", "Done ✅")
- [ ] Optional: small LLM agent with function calling using the same tools (only if time remains)

**4. Files / Modules Affected** — `agents/tools.py`, `agents/scenarios.py`, `gateway/main.py` (demo endpoint), `tests/test_agents.py`

**5. Implementation Guidance** — Scripted agents make the demo reproducible (booklet requirement). The agents folder must contain no DB path and no user tokens.

**6. Test Cases**

| ID | Scenario | Preconditions | Steps | Expected Result | Status |
|---|---|---|---|---|---|
| T7.1-1 | Tool signs | Gateway running | `refund()` | Accepted signature | ☐ |
| T7.1-2 | Scenario runs | — | `/demo/bank-refund` | Expected verdict sequence | ☐ |
| T7.1-3 | Agent has no DB access | — | `grep -r "sqlite\|\.db" agents/` | None | ☐ |
| T7.1-4 | Agent handles HOLD | — | Scenario with HOLD | Polls `/status`; replies after approval | ☐ |
| T7.1-5 | Gateway down | Gateway stopped | Run scenario | Clear error, no crash | ☐ |

**7. Verification Checklist** — [ ] every suite case has a matching scenario

**8. Completion Criteria** — All demo beats triggerable from one endpoint.

**9. Git Checkpoint**
```bash
git status
git add agents gateway/main.py tests/test_agents.py
git commit -m "M7.1: signed agent tools and scripted demo scenarios"
git push origin atharv/ai-agents
```
Do not commit: agent keys.

**10. Rollback** — E.5.

---

## Milestone 7.2 — Hospital and e-commerce domains
**Owner:** chetanagrawal721 · **Depends on:** 2.x, 3.x, 4.3 · **Hospital is cuttable**

**1. Milestone Name** — Same engine, two more organisations via policy files.

**2. Objective** — Prove generality: only policy + seed + one resolver change per domain.

**3. Tasks to Complete**
- [ ] `hospital.yaml`, `hospital_seed.py` (patients, reports, attachments); resolver `send_report`
- [ ] `shop.yaml`, `shop_seed.py` (customers, mailing lists, shared files); resolvers `write_file`, `send_email`
- [ ] Domain switch endpoint `POST /domain/{name}`
- [ ] Scenarios for demo beats 6–7

**4. Files / Modules Affected** — `gateway/policy/hospital.yaml`, `gateway/policy/shop.yaml`, `gateway/seed/*`, `gateway/resolvers/hospital.py`, `gateway/resolvers/shop.py`, `tests/test_domains.py`

**5. Implementation Guidance** — No changes to rules, seal or execute code. If a change is needed there, log it as a design finding in the journal.

**6. Test Cases**

| ID | Scenario | Preconditions | Steps | Expected Result | Status |
|---|---|---|---|---|---|
| T7.2-1 | Report with 340 patients | Hospital seeded | send_report | BLOCK R05; safe version = 1 patient | ☐ |
| T7.2-2 | Single-patient report to internal doctor | — | send_report | ALLOW | ☐ |
| T7.2-3 | File relay | Shop seeded | write_file then send_email external | BLOCK, label_path shown | ☐ |
| T7.2-4 | Newsletter | No customer file | send_email | ALLOW (false-positive control) | ☐ |
| T7.2-5 | List expands to externals | — | send to list | BLOCK; remove 37 → ALLOW | ☐ |
| T7.2-6 | Domain switch | — | switch bank→shop→bank | Correct policy hash each time | ☐ |
| T7.2-7 | Regression | — | Bank suite | Pass | ☐ |

**7. Verification Checklist** — [ ] `git diff phase-6-ok -- gateway/rules.py gateway/seal.py gateway/execute.py` is empty

**8. Completion Criteria** — Three domains run through the same engine.

**9. Git Checkpoint**
```bash
git status
git add gateway/policy gateway/seed gateway/resolvers tests/test_domains.py
git commit -m "M7.2: hospital and e-commerce domains via policy files and resolvers"
git push origin chetan/effects
```
Do not commit: generated `.db` files.

**10. Rollback** — E.5; demo can run with bank + shop only.

### ✅ Phase 7 Completion Checkpoint

| Item | Value |
|---|---|
| Completed | 7.1 ☐ · 7.2 ☐ |
| Tests passed | ___ / 12 |
| Merge & tag | → `main`; `phase-7-ok` |
| **Go / No-Go** | Go if all three (or two) domains run their scenarios on `main` |

---

# PHASE 8 — Frontend
**Owner:** Kanak-Agrawal-3008 · **Branch:** `kanak/frontend`

---

## Milestone 8.1 — Layout, chat panel and live events
**Depends on:** 0.3 (mock API)

**1. Milestone Name** — Split-screen shell with live updates.

**2. Objective** — Left: user↔agent chat; right: console shell; top bar with domain switcher and AI toggle; events arrive live.

**3. Tasks to Complete**
- [ ] Layout per Final Solution §11.2; dark theme tokens; domain tints
- [ ] `useEvents()` hook with `EventSource('/events')`; auto-reconnect
- [ ] Chat panel showing scenario messages and inline gate cards
- [ ] Backend: `GET /events` SSE in gateway (aryanketkar-15 adds; uses `asyncio.Queue`)

**4. Files / Modules Affected** — `frontend/src/App.jsx`, `frontend/src/components/{TopBar,ChatPanel,Console}.jsx`, `frontend/src/hooks/useEvents.js`, `gateway/events.py`

**5. Implementation Guidance** — **Server-Sent Events** are used instead of WebSockets because data flows one way (gateway → browser) and SSE needs no extra server library; the browser reconnects automatically.

**6. Test Cases**

| ID | Scenario | Preconditions | Steps | Expected Result | Status |
|---|---|---|---|---|---|
| T8.1-1 | Layout | — | Open at 1920×1080 | Two panels, no scroll on main view | ☐ |
| T8.1-2 | Live event | Gateway running | Trigger scenario | Message appears < 1 s | ☐ |
| T8.1-3 | Reconnect | — | Restart gateway | Events resume without reload | ☐ |
| T8.1-4 | Domain switch | — | Click 🏥 | Tint + policy name change | ☐ |
| T8.1-5 | Projector legibility | — | View at 50% zoom | Key text readable | ☐ |
| T8.1-6 | Gateway offline | Gateway stopped | Load page | Clear "gateway offline" banner | ☐ |

**7. Verification Checklist** — [ ] works against mock API and real gateway

**8. Completion Criteria** — Shell renders live chat from scenarios.

**9. Git Checkpoint**
```bash
git status
git add frontend/src gateway/events.py
git commit -m "M8.1: split-screen layout, chat panel and SSE live events"
git push origin kanak/frontend
```
Do not commit: `node_modules/`, `dist/`.

**10. Rollback** — E.5.

---

## Milestone 8.2 — Console: three-stage strip, verdict and popups
**Depends on:** 8.1; real data after 4.3

**1. Milestone Name** — The killer visual.

**2. Objective** — Expected → Sandbox → Real strip with envelope and seal, verdict row with baseline, Why/Next lines, action buttons, popup on HOLD/BLOCK.

**3. Tasks to Complete**
- [ ] `ThreeStageStrip` with envelope dotted boundary, overshoot in red
- [ ] `Seal` icon states: intact / cracked (animated)
- [ ] `VerdictRow`: "Normal gate: X · SEALGATE: Y · rule"
- [ ] `Toast` popup with Review / Approve safe version
- [ ] Buttons call `/approve`, `/safe-version`, open overlays
- [ ] "Insert invoices" demo button (calls `/demo/insert-invoices`)

**4. Files / Modules Affected** — `frontend/src/components/{ThreeStageStrip,Seal,VerdictRow,Toast,DecisionCard}.jsx`

**5. Implementation Guidance** — Same component for every decision; only data changes. Use CSS transitions, no heavy animation library.

**6. Test Cases**

| ID | Scenario | Preconditions | Steps | Expected Result | Status |
|---|---|---|---|---|---|
| T8.2-1 | ALLOW render | Phone update | — | Stages match; seal intact; green | ☐ |
| T8.2-2 | Outside envelope | Broad refund | — | Red overshoot; BLOCK; baseline ALLOW | ☐ |
| T8.2-3 | Drift | Beat 5 | Execute | Seal cracks; "40 → 4,000" | ☐ |
| T8.2-4 | Popup | HOLD | — | Toast appears once | ☐ |
| T8.2-5 | Approve flow | HOLD | Click Approve | Status updates live | ☐ |
| T8.2-6 | Unauthorised UI action | User = requester | Click Approve | Error shown from server 403 | ☐ |
| T8.2-7 | Safe version | BLOCK | Click | New decision ALLOW appears | ☐ |

**7. Verification Checklist** — [ ] all text readable from 2 m · [ ] max 3 status colours + 1 accent

**8. Completion Criteria** — Demo beats 1–3 and 5 visible in UI.

**9. Git Checkpoint**
```bash
git status
git add frontend/src
git commit -m "M8.2: three-stage strip, seal states, verdict row and popups"
git push origin kanak/frontend
```

**10. Rollback** — E.5.

---

## Milestone 8.3 — Overlays: diff, Shadow Mode, audit
**Depends on:** 8.2, 6.2, 1.3

**1. Milestone Name** — Detail views without leaving the page.

**2. Objective** — Diff (Real / Sandbox / Difference), Shadow Mode (steps, total diff, Promote/Discard), Audit (chain, Verify, Replay).

**3. Tasks to Complete**
- [ ] `DiffOverlay` with three tabs, green in-envelope / red outside rows, show-all
- [ ] `ShadowOverlay` with step dots, totals, Promote/Discard
- [ ] `AuditDrawer` with chain blocks, Verify, Replay buttons
- [ ] Backend endpoints already exist (4.3, 6.2, 6.3)

**4. Files / Modules Affected** — `frontend/src/components/{DiffOverlay,ShadowOverlay,AuditDrawer}.jsx`

**5. Implementation Guidance** — Paginate diff rows (first 20) to keep rendering fast.

**6. Test Cases**

| ID | Scenario | Preconditions | Steps | Expected Result | Status |
|---|---|---|---|---|---|
| T8.3-1 | Diff tabs | Broad refund | Open diff | Real unchanged; sandbox 212 added; difference coloured | ☐ |
| T8.3-2 | Shadow promote | Session | Promote | Success state; real updated | ☐ |
| T8.3-3 | Shadow discard | Session | Discard | Real untouched | ☐ |
| T8.3-4 | Audit verify ok | — | Verify | Green | ☐ |
| T8.3-5 | Audit tamper | Edited row | Verify | Red at that seq | ☐ |
| T8.3-6 | Replay | — | Replay #n | "Reproduced ✓" | ☐ |

**7. Verification Checklist** — [ ] overlays close with Esc and click-outside

**8. Completion Criteria** — Demo beats 4, 8, 9 visible in UI.

**9. Git Checkpoint**
```bash
git status
git add frontend/src
git commit -m "M8.3: diff, Shadow Mode and audit overlays"
git push origin kanak/frontend
```

**10. Rollback** — E.5.

---

## Milestone 8.4 — Attack Lab page and AI toggle
**Depends on:** 8.3, 9.1

**1. Milestone Name** — Evidence page.

**2. Objective** — Show modes A/B/C results, benign-twin allow rates, known misses, suite commit hash, and "add your own case".

**3. Tasks to Complete**
- [ ] `AttackLab` page: two big numbers per mode, results table, misses list, hash
- [ ] "Run suite" → `/lab/run`; progress indicator
- [ ] "Add case" form (domain, action, args, instruction) → runs once in all modes
- [ ] AI on/off toggle in top bar → `/ai/toggle`

**4. Files / Modules Affected** — `frontend/src/pages/AttackLab.jsx`, `frontend/src/components/TopBar.jsx`

**5. Implementation Guidance** — Numbers are shown exactly as returned; no hardcoded values.

**6. Test Cases**

| ID | Scenario | Preconditions | Steps | Expected Result | Status |
|---|---|---|---|---|---|
| T8.4-1 | Run suite | Gateway ready | Click Run | Results for A/B/C | ☐ |
| T8.4-2 | Hash shown | — | Load page | Matches journal | ☐ |
| T8.4-3 | Add case | — | Submit custom | Row appears with 3 verdicts | ☐ |
| T8.4-4 | Invalid custom case | Unknown action | Submit | Shown as BLOCK R02 | ☐ |
| T8.4-5 | AI toggle | — | Off | Path `fallback` on next decisions | ☐ |

**7. Verification Checklist** — [ ] no hardcoded numbers (`grep -n "22 / 22" frontend/src` → none)

**8. Completion Criteria** — Demo beat 10 works.

**9. Git Checkpoint**
```bash
git status
git add frontend/src
git commit -m "M8.4: Attack Lab page with live ablation results and AI toggle"
git push origin kanak/frontend
```

**10. Rollback** — E.5.

### ✅ Phase 8 Completion Checkpoint

| Item | Value |
|---|---|
| Completed | 8.1 ☐ · 8.2 ☐ · 8.3 ☐ · 8.4 ☐ |
| Tests passed | ___ / 24 |
| Merge & tag | → `main`; `phase-8-ok` |
| **Go / No-Go** | Go if all 10 demo beats are visible in the UI on `main` |

---

# PHASE 9 — Evaluation, Integration & Release
**Owner:** atharvg44 (9.1, 9.2) · all four (9.3)

---

## Milestone 9.1 — Attack Lab runner (ablation A/B/C)
**Depends on:** 0.3, 3.2, 4.3

**1. Milestone Name** — Reproducible paired evaluation.

**2. Objective** — Run every suite case and twin in modes A, B, C on fresh seeded DBs; report attacks stopped, harmless allowed, misses.

**3. Tasks to Complete**
- [ ] `GATE_MODE` config: A (allowlist+deny), B (+args binding), C (full)
- [ ] `lab/runner.py`: reseed → run case → record verdict → compare with expectation
- [ ] `/lab/run` endpoint and CLI `python -m lab.runner`
- [ ] Results file `lab/results_<timestamp>.json` (not committed; final one copied into journal)

**4. Files / Modules Affected** — `lab/runner.py`, `gateway/config.py`, `gateway/main.py`, `tests/test_lab.py`

**5. Implementation Guidance** — Each case runs on a freshly seeded DB so cases can't affect each other.

**6. Test Cases**

| ID | Scenario | Preconditions | Steps | Expected Result | Status |
|---|---|---|---|---|---|
| T9.1-1 | Determinism | — | Run suite twice | Identical results | ☐ |
| T9.1-2 | Isolation | — | Run case 2 alone vs in suite | Same verdict | ☐ |
| T9.1-3 | Mode A weaker | — | Run A | Some attacks ALLOW | ☐ |
| T9.1-4 | Twins allowed in C | — | Run C | Benign twins ALLOW (report any exception as a miss) | ☐ |
| T9.1-5 | Suite unchanged | — | `git diff <prereg-hash> -- lab/suite.yaml` | Only additions, each logged | ☐ |

**7. Verification Checklist** — [ ] final results recorded in journal, including misses

**8. Completion Criteria** — Results reproducible and honestly reported.

**9. Git Checkpoint**
```bash
git status
git add lab/runner.py gateway/config.py gateway/main.py tests/test_lab.py
git commit -m "M9.1: paired attack-suite runner with ablation modes A/B/C"
git push origin atharv/ai-agents
```
Do not commit: `lab/results_*.json`.

**10. Rollback** — E.5.

---

## Milestone 9.2 — End-to-end integration and regression
**Depends on:** all previous merged to `main`

**1. Milestone Name** — Whole system green on `main`.

**2. Objective** — Every test from every phase passes together; demo scenarios run start to finish.

**3. Tasks to Complete**
- [ ] `pytest -q` full suite on `main`
- [ ] Fresh-clone test: clone → setup → seed → run → demo
- [ ] Network-off test (Wi-Fi disabled, Ollama stopped)
- [ ] Fix integration bugs on short-lived branches, merge back

**4. Files / Modules Affected** — any (fixes only), `tests/test_e2e.py`

**5. Implementation Guidance** — No new features in this milestone.

**6. Test Cases**

| ID | Scenario | Preconditions | Steps | Expected Result | Status |
|---|---|---|---|---|---|
| T9.2-1 | Full test suite | `main` | `pytest -q` | 0 failures | ☐ |
| T9.2-2 | Fresh clone | New folder | Follow README | Demo runs | ☐ |
| T9.2-3 | Offline | Wi-Fi off | Run all demo beats | All work; AI path `fallback` | ☐ |
| T9.2-4 | Demo beats 1–10 | Seeded | Run script | Expected verdicts | ☐ |
| T9.2-5 | Restart mid-demo | — | Restart gateway | State consistent; chain verifies | ☐ |
| T9.2-6 | Authorship | — | `git log --format='%an' \| sort -u` | Only the four IDs | ☐ |

**7. Verification Checklist** — [ ] all phase checkpoints marked Go

**8. Completion Criteria** — `main` is release-ready.

**9. Git Checkpoint**
```bash
git checkout main
git status
git add .
git commit -m "M9.2: end-to-end integration fixes and regression green"
git push origin main
git tag rc-1 && git push origin rc-1
```

**10. Rollback** — Return to last phase tag: `git checkout phase-8-ok` (inspect) or `git revert` offending merges.

---

## Milestone 9.3 — Demo rehearsal and release
**Owners:** all four · **Depends on:** 9.2

**1. Milestone Name** — Final release and rehearsed demo.

**2. Objective** — Three timed dry runs, final README, journal updated, release tag.

**3. Tasks to Complete**
- [ ] Three dry runs (one offline), each < 2:50
- [ ] Assign speaking parts; rehearse Q&A answers 1, 3, 4, 5, 9
- [ ] README: setup, run, demo script, limits
- [ ] Journal: final results, last-moment changes, lessons
- [ ] Reset demo state script `./reset_demo.sh` (reseed all domains, clear logs)

**4. Files / Modules Affected** — `README.md`, `PROJECT_JOURNAL.md`, `reset_demo.sh`

**5. Implementation Guidance** — Freeze code after the second successful dry run; only critical fixes after that.

**6. Test Cases**

| ID | Scenario | Preconditions | Steps | Expected Result | Status |
|---|---|---|---|---|---|
| T9.3-1 | Dry run 1 | Reset | Full demo | < 2:50, no errors | ☐ |
| T9.3-2 | Dry run 2 offline | Wi-Fi off | Full demo | < 2:50 | ☐ |
| T9.3-3 | Dry run 3 + Q&A | — | Demo + 5 questions | Smooth | ☐ |
| T9.3-4 | Reset script | After demo | `./reset_demo.sh` | Clean initial state | ☐ |
| T9.3-5 | Projector | Venue screen | Show UI | Readable from back row | ☐ |

**7. Verification Checklist** — [ ] Final Release Checklist (below) fully ticked

**8. Completion Criteria** — Team agrees the demo is ready; release tagged.

**9. Git Checkpoint**
```bash
git checkout main
git status
git add README.md PROJECT_JOURNAL.md reset_demo.sh
git commit -m "M9.3: release documentation, demo reset script and final journal"
git push origin main
git tag v1.0-vortexa && git push origin v1.0-vortexa
```

**10. Rollback** — If anything breaks after the tag: `git checkout v1.0-vortexa` on the demo laptop and run from there.

### ✅ Phase 9 Completion Checkpoint

| Item | Value |
|---|---|
| Completed | 9.1 ☐ · 9.2 ☐ · 9.3 ☐ |
| Tests passed | ___ / 16 |
| Release tag | `v1.0-vortexa` · hash: |
| **Go / No-Go** | Go to stage |

---

# FINAL RELEASE CHECKLIST

### Functionality
- [ ] All 10 demo beats work in the UI
- [ ] ALLOW / HOLD / BLOCK / VOID / DONE all demonstrated
- [ ] Every drift type (args, effect, label, policy, state, replay, expired) tested
- [ ] Smallest safe version re-seals reduced effect
- [ ] Shadow Mode promote and discard work
- [ ] All domains switch cleanly

### Testing
- [ ] `pytest -q` green on `main`
- [ ] Attack Lab reproducible; results and misses recorded in journal
- [ ] Offline run successful
- [ ] Fresh-clone run successful

### Security
- [ ] Agents folder contains no DB paths, no user tokens
- [ ] `.env` not tracked; `.env.example` has placeholders only
- [ ] Self-approval and agent-approval refused
- [ ] Hash chain verify detects tampering
- [ ] No `yaml.load(`, no string-built SQL with agent input

### Performance
- [ ] Decision latency < 1 s per action on demo data (excluding AI)
- [ ] AI timeout 3 s; fallback instant
- [ ] UI renders diff overlays without lag (pagination)

### Deployment (local)
- [ ] `./run.sh` starts everything
- [ ] `./reset_demo.sh` restores initial state
- [ ] Ollama model pre-pulled on demo laptop (or AI-off path rehearsed)
- [ ] Laptop power, display mirroring and resolution tested

### Documentation
- [ ] README: setup, run, demo, limits
- [ ] `SEALGATE_Final_Solution.md` matches what was built (note differences in journal)
- [ ] `PROJECT_JOURNAL.md` up to date: methodology, decisions, last-moment changes, log, results

### Git repository cleanliness
- [ ] `git log --format='%an' | sort -u` → only the four team IDs
- [ ] No `Co-authored-by` trailers outside the team (`git log | grep -i co-authored-by`)
- [ ] No `.db`, `node_modules`, `.venv`, logs, results files tracked
- [ ] All personal branches merged; tags `phase-0-ok … phase-9-ok`, `rc-1`, `v1.0-vortexa` pushed
