# SEALGATE — Development Logbook

**Purpose.** This logbook is the engineering record of the SEALGATE build: what has changed, how it has been done, and why, for every milestone. It complements `docs/PROJECT_JOURNAL.md`, which holds the research narrative (decisions, methodology, results).

**Convention.** Entries are written in the present perfect tense and the third person, in the team's voice ("The team has implemented…"). Entries are appended in order, newest at the bottom. Each milestone has one entry.

**Source of truth.** Milestones, test IDs and commit messages come from `docs/SEALGATE_Build_Playbook.md`.

## Progress checklist

| Milestone | Title | Owner | Status |
|---|---|---|---|
| 0.1 | Repository, identities, authorship guards | aryanketkar-15 | ☑ |
| 0.2 | Runnable scaffolds (a: gateway, b: data folder, c: frontend) | aryanketkar-15 / chetanagrawal721 / Kanak-Agrawal-3008 | ☑ |
| 0.3 | API contract, schemas, pre-registered suite | aryanketkar-15 / atharvg44 | ☑ |
| 1.1 | Policy loader, registry, default deny | aryanketkar-15 | ☑ |
| 1.2 | Signed requests, nonces, timestamps | aryanketkar-15 | ☑ |
| 1.3 | Hash-chained audit log | aryanketkar-15 | ☑ |
| 2.1 | Bank seed DB and sandbox copies | chetanagrawal721 | ☐ |
| 2.2 | Resolvers and Effect object | chetanagrawal721 | ☐ |
| 2.3 | Data labels and destinations | chetanagrawal721 | ☐ |
| 3.1 | Envelope and envelope check | chetanagrawal721 | ☐ |
| 3.2 | Rules R01–R12, tiers, decide() | chetanagrawal721 | ☐ |
| 3.3 | Resource-keyed budgets | chetanagrawal721 | ☐ |
| 4.1 | Approvals and separation of duties | aryanketkar-15 | ☐ |
| 4.2 | Effect seal with typed drift | aryanketkar-15 | ☐ |
| 4.3 | One-transaction execution and outbox | aryanketkar-15 | ☐ |
| 5.1 | AI client, validation, fallback | atharvg44 | ☐ |
| 5.2 | Envelope from instruction, claim-vs-effect | atharvg44 | ☐ |
| 5.3 | Paraphrase sentry, explanations | atharvg44 | ☐ |
| 6.1 | Smallest safe version | chetanagrawal721 | ☐ |
| 6.2 | Shadow Mode | chetanagrawal721 | ☐ |
| 6.3 | Replay and honeytoken freeze | aryanketkar-15 | ☐ |
| 7.1 | Agents, tools, scenarios | atharvg44 | ☐ |
| 7.2 | Hospital and e-commerce domains | chetanagrawal721 | ☐ |
| 8.1 | Layout, chat, live events | Kanak-Agrawal-3008 | ☐ |
| 8.2 | Three-stage strip, verdict, popups | Kanak-Agrawal-3008 | ☐ |
| 8.3 | Diff, Shadow, Audit overlays | Kanak-Agrawal-3008 | ☐ |
| 8.4 | Attack Lab page, AI toggle | Kanak-Agrawal-3008 | ☐ |
| 9.1 | Attack Lab runner | atharvg44 | ☐ |
| 9.2 | End-to-end integration | all | ☐ |
| 9.3 | Rehearsal and release | all | ☐ |

## Entry template

```
### [Milestone ID] Title — YYYY-MM-DD HH:MM IST — Owner: <github-id>
**What has changed:** files/modules/tables/endpoints created or modified
**Why:** the requirement (booklet R1–R10, rule ID, or design decision D#) it serves
**How:** approach, key design choices, alternatives considered and rejected
**Tests:** test IDs run, pass/fail counts, notable failures and fixes
**Deviations from plan:** anything different from the playbook, and the reason
**Last-moment changes:** yes/no (if yes, also add a row to PROJECT_JOURNAL.md §11)
**Suggested commit message:** from the playbook
**Known issues:** open items carried forward
```

---

## Entries

### [Setup] Project understanding and agent rules — 2026-10-11 13:35 IST — Owner: aryanketkar-15
**What has changed:** `CLAUDE.md` and `DEV_LOGBOOK.md` have been created at the repository root, and `.claude/settings.json` has been added to disable commit and pull-request attribution lines. The three design documents have been placed under `docs/`.
**Why:** The team has needed persistent working rules (one milestone at a time, humans perform all git operations, no authorship other than the four team members) and a place to record engineering detail separately from the research journal.
**How:** The rules have been derived from the Build Playbook (sections A–E) and the Final Solution. No application code has been written.
**Tests:** Not applicable.
**Deviations from plan:** None. Milestone 0.1 has not been started.
**Last-moment changes:** no
**Suggested commit message:** none (setup files only; to be committed with M0.1)
**Known issues:** Open questions on the playbook's Section A and several cross-document inconsistencies have been raised and await the team's answers.

### [0.1] Repository, identities and authorship guards — 2026-10-11 13:57 IST — Owner: aryanketkar-15
**What has changed:** `.gitignore`, `README.md`, `.env.example`, `.githooks/commit-msg`, `.githooks/pre-commit`, `docs/` (design documents), `CLAUDE.md`, `DEV_LOGBOOK.md`, `.claude/settings.json`, `tests/test_hooks.py`.
**Why:** The team has needed a shared repository whose commits are restricted to the four team identities and which never tracks secrets or generated files (playbook E.2, E.4).
**How:** The ignore rules and the two hooks from the playbook have been added unchanged except that the author hook also accepts the configured display name. The hooks have been tested directly as shell scripts so that the checks do not depend on `core.hooksPath` being set on a given laptop.
**Tests:** T0.1-1..5 covered by `tests/test_hooks.py` (6 passed). T0.1-6 (collaborator pushes) remains for the humans.
**Deviations from plan:** Design documents live in `docs/` rather than the repository root; the playbook `git add` list has been adapted accordingly. Branch creation and `core.hooksPath` are left to the humans.
**Last-moment changes:** no
**Suggested commit message:** M0.1: repository, ignore rules and authorship guard hooks
**Known issues:** none

### [0.2] Runnable scaffolds — 2026-10-11 13:57 IST — Owner: aryanketkar-15
**What has changed:** `gateway/main.py` (FastAPI, `/health`, CORS), `agents/config.py`, `frontend/` (Vite + React + Tailwind, dark theme, health banner), `tests/conftest.py`, `tests/test_scaffold.py`, `run.sh`, `pytest.ini`, `gateway/requirements.txt`.
**Why:** Every part of the system has needed to start with one command so that later milestones only add code.
**How:** The stack from the playbook has been used (FastAPI, pytest, Vite, Tailwind 3). Python 3.12 and Node 22 are installed on the build laptop instead of the 3.11 and 20 named in the playbook; no version-specific features are used.
**Tests:** T0.2-1,2,5,6,7 covered by `tests/test_scaffold.py` (3 passed); the frontend production build succeeds.
**Deviations from plan:** Python 3.12 / Node 22 instead of 3.11 / 20.
**Last-moment changes:** no
**Suggested commit message:** M0.2: runnable gateway/agents/frontend scaffolds with health check
**Known issues:** none

### [0.3] API contract, schemas and pre-registered attack suite — 2026-10-11 13:57 IST — Owner: aryanketkar-15
**What has changed:** `gateway/schemas.py`, `gateway/mock_api.py`, `docs/api.md`, `lab/suite.yaml` (22 attack/twin pairs), `tests/test_schemas.py`.
**Why:** All four members have needed to build against one set of request and response shapes, and the evaluation suite has had to be fixed before any gateway logic exists (pre-registration).
**How:** Pydantic models with `extra=forbid` have been defined. Beyond the playbook sketch, `Proposal` has gained `on_behalf_of`, `Decision` has gained `status`, `tier`, `approvals`, `drift` and related fields, and `Effect` has gained `row_meta` and `table_sizes`. The suite also records predicted outcomes for modes A and B and defines the metrics for 'attack stopped' and 'benign allowed'.
**Tests:** T0.3-1..6 covered by `tests/test_schemas.py` (6 passed in the suite).
**Deviations from plan:** Optional fields added to the contract before freezing (see How).
**Last-moment changes:** no
**Suggested commit message:** M0.3: frozen API contract, schemas, mock API and pre-registered paired suite
**Known issues:** none

### [1.1] Policy loader, registry and default deny — 2026-10-11 13:57 IST — Owner: aryanketkar-15
**What has changed:** `gateway/policy/bank.yaml`, `gateway/policy_loader.py`, `gateway/registry.py`, `gateway/users.yaml`, `gateway/config.py`, `tests/test_policy.py`.
**Why:** R02/R3: unknown agents, actions and destinations have had to be refused by default.
**How:** The policy has been validated by a strict Pydantic model (fails closed), hashed from canonical JSON, and loaded with `yaml.safe_load` only. Effective permissions have been defined as the intersection of the agent's actions and the acting human's role.
**Tests:** T1.1-1..9 covered by `tests/test_policy.py` (all passed).
**Deviations from plan:** none
**Last-moment changes:** no
**Suggested commit message:** M1.1: per-org policy loader, registry, effective permissions, default deny (R02, R3)
**Known issues:** none

### [1.2] Signed requests, nonces and timestamps — 2026-10-11 13:57 IST — Owner: aryanketkar-15
**What has changed:** `gateway/verify.py`, `gateway/clock.py`, `gateway/db.py` (control-plane state schema), `tests/helpers.py`, `tests/test_verify.py`.
**Why:** R01: requests tampered with, replayed or sent by impostors have had to be blocked before any analysis.
**How:** HMAC-SHA256 over the canonical body with constant-time comparison; a nonce is consumed only by an authentic request. The agent is checked against the registry first so that an unknown agent yields R02 (T1.2-8). An injectable clock has been added for later time-dependent tests.
**Tests:** T1.2-1..9 covered by `tests/test_verify.py` (all passed).
**Deviations from plan:** none
**Last-moment changes:** no
**Suggested commit message:** M1.2: HMAC-signed proposals with nonce and timestamp checks (R01)
**Known issues:** none

### [1.3] Hash-chained audit log — 2026-10-11 13:57 IST — Owner: aryanketkar-15
**What has changed:** `gateway/audit.py`, `gateway/engine.py` (engine skeleton, refusal logging), `gateway/main.py` (`/propose`, `/audit`, `/audit/verify`, `/policy/reload`), `tests/test_audit.py`.
**Why:** R8/R10: every decision, including refusals, has had to be recorded tamper-evidently with its decision path.
**How:** Each entry hashes the previous entry hash plus its canonical fields; `verify()` returns the first broken sequence number. Full decision inputs are stored in `payload_json`, which keeps the table schema stable for later milestones.
**Tests:** T1.3-1..7 covered by `tests/test_audit.py`; full suite 39 passed.
**Deviations from plan:** none
**Last-moment changes:** no
**Suggested commit message:** M1.3: hash-chained audit log with verify endpoint (R8, R10)
**Known issues:** Truncating the newest entries is not detectable by the chain alone (documented limit).
