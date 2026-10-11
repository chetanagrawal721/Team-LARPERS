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
| 2.1 | Bank seed DB and sandbox copies | chetanagrawal721 | ☑ |
| 2.2 | Resolvers and Effect object | chetanagrawal721 | ☑ |
| 2.3 | Data labels and destinations | chetanagrawal721 | ☑ |
| 3.1 | Envelope and envelope check | chetanagrawal721 | ☑ |
| 3.2 | Rules R01–R12, tiers, decide() | chetanagrawal721 | ☑ |
| 3.3 | Resource-keyed budgets | chetanagrawal721 | ☑ |
| 4.1 | Approvals and separation of duties | aryanketkar-15 | ☑ |
| 4.2 | Effect seal with typed drift | aryanketkar-15 | ☑ |
| 4.3 | One-transaction execution and outbox | aryanketkar-15 | ☑ |
| 5.1 | AI client, validation, fallback | atharvg44 | ☑ |
| 5.2 | Envelope from instruction, claim-vs-effect | atharvg44 | ☑ |
| 5.3 | Paraphrase sentry, explanations | atharvg44 | ☑ |
| 6.1 | Smallest safe version | chetanagrawal721 | ☑ |
| 6.2 | Shadow Mode | chetanagrawal721 | ☑ |
| 6.3 | Replay and honeytoken freeze | aryanketkar-15 | ☑ |
| 7.1 | Agents, tools, scenarios | atharvg44 | ☑ |
| 7.2 | Hospital and e-commerce domains | chetanagrawal721 | ☑ |
| 8.1 | Layout, chat, live events | Kanak-Agrawal-3008 | ☑ |
| 8.2 | Three-stage strip, verdict, popups | Kanak-Agrawal-3008 | ☑ |
| 8.3 | Diff, Shadow, Audit overlays | Kanak-Agrawal-3008 | ☑ |
| 8.4 | Attack Lab page, AI toggle | Kanak-Agrawal-3008 | ☑ |
| 9.1 | Attack Lab runner | atharvg44 | ☑ |
| 9.2 | End-to-end integration | all | ☑ |
| 9.3 | Rehearsal and release | all | ☐ (docs done; rehearsal pending) |

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

### [2.1] Bank seed database and sandbox copies — 2026-10-11 14:00 IST — Owner: chetanagrawal721
**What has changed:** `gateway/seed/bank_seed.py`, `gateway/seed/common.py`, `gateway/sandbox.py`, `docs/fixtures.md`, `tests/test_seed.py`.
**Why:** R5: the team has needed realistic fictional data with the demonstration traps planted, and a safe way to copy it for practice runs.
**How:** SQLite file copies via the backup API are used as sandboxes. The seed is deterministic (fixed random seed) and plants 212 duplicate March charges across 61 customers (Rs 9.8 lakh, of which C-1042 holds Rs 6,400), 40 pending invoices, a poisoned inbox email and a verified vendor form. Bookkeeping tables (outbox, budgets, used_seals, shared_files) are shared by all domains.
**Tests:** T2.1-1..8 covered by `tests/test_seed.py` (8 passed).
**Deviations from plan:** none
**Last-moment changes:** no
**Suggested commit message:** M2.1: deterministic fictional bank seed with planted fixtures and sandbox copies
**Known issues:** none

### [2.2] Resolvers and the Effect object — 2026-10-11 14:00 IST — Owner: chetanagrawal721
**What has changed:** `gateway/resolver.py`, `gateway/resolvers/__init__.py`, `gateway/resolvers/bank.py` (lookup, update_contact, refund, transfer, payee_change, grant_role), `tests/test_resolver.py`.
**Why:** R5: the effect of an action (rows including FK cascades, amounts, recipients) has had to be measured rather than guessed.
**How:** Each resolver applies the action to a sandbox copy; the watched tables are snapshotted before and after and diffed per primary key. Effect hash and a pre-image `state_ver` are computed for later sealing. The broad refund is expressed with `match=batch` (all duplicates of the same processor batch), which reproduces the 61-customer case without a deliberately broken resolver.
**Tests:** T2.2-1..8 covered by `tests/test_resolver.py` (10 passed); real DB hash unchanged after every practice run.
**Deviations from plan:** The 212-row case uses `refund(customer, month, match=batch)` instead of plain `refund(customer, month)`.
**Last-moment changes:** no
**Suggested commit message:** M2.2: sandbox resolvers returning exact effects with cascades (R5)
**Known issues:** none

### [2.3] Data labels and destinations — 2026-10-11 14:00 IST — Owner: chetanagrawal721
**What has changed:** `gateway/labels.py`, label handling inside the resolvers, `tests/test_labels.py`.
**Why:** Rules R05 and R07 have needed effects to carry sensitivity labels and destination classes computed by the gateway.
**How:** Labels come from the policy catalog by touched column (unlabelled columns default to INTERNAL). Provenance of payee changes is resolved against the `forms` and `inbox` tables, so an agent cannot claim a trusted source: only a verified form that matches vendor and account is trusted. Email addresses are classified internal or external from the policy's domain list. A label-catalog version is hashed into every effect.
**Tests:** T2.3-1..5, 7 covered by `tests/test_labels.py` (9 passed). T2.3-6 (file inherits labels) is covered with the shop resolvers in M7.2.
**Deviations from plan:** File-inherited labels (T2.3-6) have been deferred to M7.2, where the `write_file` resolver exists.
**Last-moment changes:** no
**Suggested commit message:** M2.3: effect-level data labels, destinations and provenance path
**Known issues:** none

### [3.1] Expected envelope and envelope check — 2026-10-11 14:03 IST — Owner: chetanagrawal721
**What has changed:** `gateway/envelope.py`, `tests/test_envelope.py`.
**Why:** R5/R6: the team has needed a deterministic answer to 'is the action doing more than was asked?'.
**How:** Pure functions compare the measured effect with the envelope: every affected row must match the scope keys (by primary key or by a declared attribute), the primary-table row count and amount must stay within limits, and destinations must be expected. A missing required scope key yields the strictest envelope (at most one row). The `source` field is ready for the AI-built envelope of M5.2.
**Tests:** T3.1-1..6 covered by `tests/test_envelope.py` (7 passed); the broad refund reports exactly 209 offending rows.
**Deviations from plan:** none
**Last-moment changes:** no
**Suggested commit message:** M3.1: expected-effect envelope with deterministic inside/outside check
**Known issues:** none

### [3.2] Rules R01-R12, tiers and decide() — 2026-10-11 14:03 IST — Owner: chetanagrawal721
**What has changed:** `gateway/rules.py`, `gateway/decide.py`, `gateway/engine.py` (full propose pipeline: identify, resolve, envelope, budget, decide, log), `gateway/db.py` (`meta_json` column), `tests/test_rules.py`.
**Why:** R2/R4/R5: one deterministic function has had to turn the measured effect into ALLOW, HOLD or BLOCK with a rule ID, and to expose the request-level (mode B) verdict for side-by-side display.
**How:** `decide()` takes plain dicts and the policy, so identical inputs give identical output and a stored decision can be replayed. The first BLOCK among R01-R06 wins, otherwise the strongest HOLD of R07-R10, otherwise R12; `final = max(rules, AI)`. Tiers follow the reversibility x blast-radius table; an override list in the policy lowers the tier for public or internal-only content. When AI is unavailable and the agent supplied an intent claim that therefore cannot be checked, the tier is raised by one level.
**Tests:** T3.2-1..12 covered by `tests/test_rules.py` (16 passed); the bank cases A01, A08, A19-A21 return the pre-registered mode C verdicts.
**Deviations from plan:** The honeytoken freeze (agent frozen flag) has been implemented here because T3.2-7 requires it; M6.3 adds the unfreeze endpoint and replay.
**Last-moment changes:** no
**Suggested commit message:** M3.2: deterministic rules R01-R12, tiers, decide() and baseline verdict (R2, R4)
**Known issues:** none

### [3.3] Resource-keyed budgets — 2026-10-11 14:03 IST — Owner: chetanagrawal721
**What has changed:** `gateway/budgets.py`, `tests/test_budgets.py`.
**Why:** R08: cumulative limits charged on the measured effect stop salami slicing and budget splitting across agents.
**How:** Budgets are sliding one-hour windows keyed by (agent, resource) and by (resource), stored in the domain database. Check and charge run in one `BEGIN IMMEDIATE` transaction so concurrent callers cannot exceed a limit. Only executed actions are charged; blocked ones are not. The budget snapshot is stored in the audit payload.
**Tests:** T3.3-1..7 covered by `tests/test_budgets.py` (6 passed); full suite 95 passed.
**Deviations from plan:** none
**Last-moment changes:** no
**Suggested commit message:** M3.3: resource-keyed cumulative budgets charged on resolved effect (R08)
**Known issues:** none

### [4.1] Approvals and separation of duties — 2026-10-11 14:10 IST — Owner: aryanketkar-15
**What has changed:** `gateway/approvals.py`, `gateway/main.py` (`/approve`, `/reject`, `/status`, `/action`, `/actions`), `tests/test_phase4.py`.
**Why:** R7: held actions have had to be approved only by authorised humans who are not the requester, and tier-3 actions by two distinct approvers.
**How:** Authorisation is enforced on the server: users are authenticated by an `X-User` header plus a per-user token from `.env` (demo-only; agents hold no user tokens). The requester is the human the agent acts for. Every refused attempt is written to the audit log. When the required number of distinct approvers is reached the gateway creates the seal.
**Tests:** T4.1-1..9 covered in `tests/test_phase4.py` (all passed).
**Deviations from plan:** none
**Last-moment changes:** no
**Suggested commit message:** M4.1: approvals with separation of duties and tiered approvers (R7)
**Known issues:** none

### [4.2] Effect seal with typed drift — 2026-10-11 14:10 IST — Owner: aryanketkar-15
**What has changed:** `gateway/seal.py`, `gateway/policy_loader.py` (`rules_hash`), tests in `tests/test_phase4.py`.
**Why:** R6: an approval has had to apply only to the exact measured effect, and any difference has had to void it with a named reason.
**How:** The seal is an HMAC-signed token over action hash, effect hash, label-path hash, label-catalog version, policy version, state version, requester, tier, approvers, a one-time nonce and an expiry. Components are compared in a fixed order (signature, expiry, replay, args, policy, label, effect, state). The policy version excludes the label catalog so that policy drift and label drift can be told apart.
**Tests:** T4.2-1..10 covered in `tests/test_phase4.py` (all passed); each drift type produces its own audit entry.
**Deviations from plan:** none
**Last-moment changes:** no
**Suggested commit message:** M4.2: effect-bound seal with typed drift detection (R6)
**Known issues:** none

### [4.3] One-transaction execution and transactional outbox — 2026-10-11 14:10 IST — Owner: aryanketkar-15
**What has changed:** `gateway/execute.py`, `gateway/outbox.py`, `gateway/engine.py` (auto-execution of ALLOW through the sealed path, requeue after void), `gateway/main.py` (`/execute`, `/demo/insert-invoices`), tests in `tests/test_phase4.py`.
**Why:** R6: only what was sealed may run, and irreversible payments and messages may leave only after commit.
**How:** Execution opens `BEGIN IMMEDIATE` on the real database, re-runs the stored action, diffs the affected rows, compares the fresh effect with the seal and either writes the outbox rows and commits or rolls back. The seal nonce is consumed inside the same transaction. Delivery is a separate worker. ALLOW decisions use an internal seal with no approvers so that all execution shares one code path. A voided action is re-evaluated as a new decision that always needs fresh approval.
**Tests:** T4.3-1..9 covered in `tests/test_phase4.py`; full suite 122 passed. The real database hash is unchanged after every void and after a simulated crash.
**Deviations from plan:** The second of two seals over the same rows reports `effect_drift` (the rows are no longer pending) where the playbook expected `state_drift`; both are accepted by the test.
**Last-moment changes:** no
**Suggested commit message:** M4.3: one-transaction sealed execution and transactional outbox
**Known issues:** none

### [5.1] AI client, schema validation and fallback — 2026-10-11 14:13 IST — Owner: atharvg44
**What has changed:** `gateway/ai.py`, `gateway/main.py` (`/ai/toggle`, `/ai/status`), `.env.example` (AI settings), tests in `tests/test_ai.py`.
**Why:** R4/R9/R10: the AI has had to be able to inform decisions without ever deciding alone, and the system has had to stay safe when the AI is off, slow or wrong.
**How:** One module calls an optional provider behind a 3-second timeout and validates the answer against a strict Pydantic schema whose escalation field can only be NONE, HOLD or BLOCK. Any timeout, transport error or invalid output yields no result, and the decision path is recorded as `fallback`. Providers are selected by environment variable (none, Ollama, Gemini, OpenRouter); the API key is read only from `.env` and sent in a header. Tests inject an `httpx.MockTransport`, so no model is needed.
**Tests:** T5.1-1..9 covered by `tests/test_ai.py` (all passed).
**Deviations from plan:** Gemini and OpenRouter providers have been added alongside Ollama, because the team has API keys available at the venue; this uses only `httpx`, which the playbook already lists.
**Last-moment changes:** no
**Suggested commit message:** M5.1: escalate-only AI client with schema validation and fallback (R4, R9, R10)
**Known issues:** none

### [5.2] Envelope from instruction and claim-vs-effect check — 2026-10-11 14:13 IST — Owner: atharvg44
**What has changed:** `gateway/ai_layer.py`, `gateway/prompts/envelope.txt`, `gateway/prompts/claim.txt`, `gateway/engine.py` (wiring), tests in `tests/test_ai.py`.
**Why:** The envelope has needed to come from the user's own words, so that 'more than asked' is a checkable property, and agent claims have needed to be compared with the measured effect.
**How:** The model extracts scope, row and amount limits from the instruction; they are clamped with `min(ai_limit, policy_limit)` so the AI can never widen what the policy allows, and vague instructions fall back to the strict policy default with a flag. Prompts are stored as files, and the user text is delimited as data. When the AI is unavailable the tier of an unverifiable intent claim is raised by one level.
**Tests:** T5.2-1..8 covered by `tests/test_ai.py` (all passed).
**Deviations from plan:** none
**Last-moment changes:** no
**Suggested commit message:** M5.2: AI envelope from user instruction (clamped) and claim-vs-effect escalation
**Known issues:** none

### [5.3] Paraphrase sentry and explanations — 2026-10-11 14:13 IST — Owner: atharvg44
**What has changed:** `gateway/ai_layer.py`, `gateway/prompts/sentry.txt`, `gateway/engine.py` (per-agent record of sensitive data accessed), tests in `tests/test_ai.py`.
**Why:** Personal data rewritten into prose cannot be seen by labels, so a best-effort escalation has been added, and approvers have needed one plain sentence per decision.
**How:** The sentry can only HOLD, never BLOCK. When it is unavailable, a deterministic fallback holds any external free-text send by an agent that has accessed PII or SECRET data in this task. Explanations are written by the model when available and otherwise come from a template per rule ID.
**Tests:** T5.3-1..5 covered by `tests/test_ai.py`; full suite 145 passed.
**Deviations from plan:** none
**Last-moment changes:** no
**Suggested commit message:** M5.3: best-effort paraphrase sentry and approver explanations
**Known issues:** The sentry is best-effort by design and is listed as a known limitation.

### [6.1] Smallest safe version — 2026-10-11 14:17 IST — Owner: chetanagrawal721
**What has changed:** `gateway/safe_version.py`, `reduce()` hooks and an `only` argument in `gateway/resolvers/bank.py`, `gateway/resolver.py`, `gateway/engine.py` (dry-run analysis, offer and accept flow), `gateway/main.py` (`POST /safe-version/{id}`), tests in `tests/test_phase6.py`.
**Why:** Blocked actions have had to become actionable: the minimal change to the resolved effect that makes the decision safer is offered, re-checked and re-sealed.
**How:** Each resolver declares how its effect can be reduced (explicit primary-key lists, never SQL text): the refund keeps only rows inside the request's customer scope up to the limits; the batch transfer keeps at most ten invoices. The reduced action is run through the full gate in a dry run and is offered only if it is strictly safer (a better verdict, or the same HOLD at a lower tier). It is never offered for R01-R04, SECRET data, budget holds or protected-class holds, and never as a split into several actions. Accepting creates a new decision linked to the original, which is sealed and executed.
**Tests:** T6.1-1..7 covered by `tests/test_phase6.py` (7 passed).
**Deviations from plan:** none
**Last-moment changes:** no
**Suggested commit message:** M6.1: deterministic smallest-safe-version engine with re-sealing
**Known issues:** none

### [6.2] Shadow Mode — 2026-10-11 14:17 IST — Owner: chetanagrawal721
**What has changed:** `gateway/shadow.py`, `gateway/engine.py` (routing), `gateway/main.py` (`GET /shadow/{sid}`, `POST /promote/{sid}`, `POST /discard/{sid}`), tests in `tests/test_phase6.py`.
**Why:** Approval fatigue has been addressed: a held, suspicious agent keeps working in a sandbox and a human reviews the total result once.
**How:** A HOLD caused by untrusted input (R07) creates a session with an immutable base copy and a working copy of the database; the trigger and all later actions of that agent are applied to the working copy and recorded with their arguments, effects and pre-image versions. Promotion replays the recorded actions inside one transaction on the real database, requires each step's pre-image to be unchanged and requires the real row-level diff to equal the sandbox diff; otherwise it rolls back with a typed drift. Promotion follows separation of duties and needs two promoters for a tier-3 session. Sandbox payments and messages are never delivered.
**Tests:** T6.2-1..8 covered by `tests/test_phase6.py` (10 passed); discard leaves the real database hash unchanged.
**Deviations from plan:** none
**Last-moment changes:** no
**Suggested commit message:** M6.2: Shadow Mode with recorded steps and diff-verified promotion
**Known issues:** none

### [6.3] Replay and honeytoken freeze — 2026-10-11 14:17 IST — Owner: aryanketkar-15
**What has changed:** `gateway/replay.py`, `gateway/main.py` (`POST /audit/replay/{seq}`, `POST /agents/{agent}/unfreeze`, `GET /agents`), tests in `tests/test_phase6.py`.
**Why:** Decisions have had to be provably reproducible from the log, and agents that call a decoy action have had to be stopped until a human intervenes.
**How:** Replay re-runs the pure `decide()` function on the stored inputs against the stored policy version and refuses to run when the audit chain is broken; it never touches a live database. The freeze flag, set on a honeytoken call in M3.2, is cleared only by an authorised human.
**Tests:** T6.3-1..6 covered by `tests/test_phase6.py`; ten random decisions replay identically; full suite 166 passed.
**Deviations from plan:** none
**Last-moment changes:** no
**Suggested commit message:** M6.3: decision replay against stored policy and honeytoken freeze
**Known issues:** none

### [7.1] Agents, tools and demo scenarios — 2026-10-11 14:22 IST — Owner: atharvg44
**What has changed:** `agents/tools.py`, `agents/scenarios.py`, `agents/run.py`, `gateway/events.py` (event bus), `gateway/main.py` (`/events`, `/chat`, `/demo/{scenario}`, `/demo/chat`), `tests/test_agents.py`.
**Why:** The agent side of every demonstration beat has needed to exist as reproducible scripts that can only propose, and the dashboard has needed a live event stream.
**How:** An agent signs and posts requests, polls `/status` for held decisions and posts its chat lines to `/chat`; it holds only its own signing key and never imports gateway code. Scenarios run as a separate process started by the gateway with a filtered environment (agent keys only, so no user tokens or seal key). A small keyword router maps free-text chat requests to scenarios. The event bus replays recent history and then follows new events over Server-Sent Events.
**Tests:** T7.1-1..5 covered by `tests/test_agents.py` (13 passed), including the gateway-down case and a scan proving the package contains no database path or user token.
**Deviations from plan:** none
**Last-moment changes:** no
**Suggested commit message:** M7.1: signed agent tools and scripted demo scenarios
**Known issues:** none

### [7.2] Hospital and e-commerce domains — 2026-10-11 14:22 IST — Owner: chetanagrawal721
**What has changed:** `gateway/policy/hospital.yaml`, `gateway/policy/shop.yaml`, `gateway/seed/hospital_seed.py`, `gateway/seed/shop_seed.py`, `gateway/resolvers/hospital.py`, `gateway/resolvers/shop.py`, `gateway/main.py` (`POST /domain/{name}`), `tests/test_domains.py`.
**Why:** Generality has needed to be shown: the same engine protects three organisations when only the policy, seed data and resolvers change.
**How:** Resolvers may report 'virtual rows' (patients disclosed by a report, recipients of a mailing, a file written) so that disclosures are measured like row changes. Mailing lists carry a declared audience and the envelope check flags recipients outside it, which reveals the 37 external addresses inside the 'staff' list. Files inherit the labels of the rows written into them, which blocks the two-agent relay. Policy overrides lower the tier for internal-only or public-only content so that ordinary mail is allowed. No change was made to rules, seal or execution code (verified by a test).
**Tests:** T7.2-1..7 covered by `tests/test_domains.py` (11 passed); T2.3-6 (file inherits labels) is covered here; full suite 190 passed.
**Deviations from plan:** The sensitive-access record used by the paraphrase fallback now ignores blocked actions and expires after 30 minutes, so that a blocked attempt does not hold unrelated later mail.
**Last-moment changes:** no
**Suggested commit message:** M7.2: hospital and e-commerce domains via policy files and resolvers
**Known issues:** none

### [9.1] Attack Lab runner (ablation A/B/C) — 2026-10-11 14:28 IST — Owner: atharvg44
**What has changed:** `lab/runner.py`, `gateway/decide.py` (`mode_decide`), `gateway/engine.py`, `gateway/execute.py`, `gateway/approvals.py` (mode switches), `gateway/main.py` (`/lab/run`, `/lab/last`, `/lab/suite`, `/lab/case`), `lab/suite.yaml` (case A23 added), `tests/test_lab.py`.
**Why:** The team has needed reproducible, honest evidence: every attack and its benign twin run in three configurations of the same gateway on freshly seeded data.
**How:** The engine has a mode switch. Mode A keeps signature checks, the registry and default deny. Mode B adds request-level approval of protected actions and approvals bound to the argument hash only (no separation of duties). Mode C is the full system. The runner seeds each domain once, copies the file for every case, defers execution where the case needs an approval gap, applies the named mutation, and maps results to outcomes such as VOID:effect_drift. A crash is reported as FAIL and never as a pass. Results are saved to a git-ignored file and returned with the suite commit hash.
**Tests:** T9.1-1..5 covered by `tests/test_lab.py` (9 passed); full suite 199 passed. Live result: mode A stops 4 of 22 attacks, mode B 8 of 22, mode C 21 of 22, with all 22 benign twins allowed in every mode.
**Deviations from plan:** Pre-registered case A10 (90 refunds across three agents) stays within both budget limits, so mode C allows it and the runner reports it as a miss; the corrected case A23 (120 refunds) has been added and the addition has been logged in the journal.
**Last-moment changes:** yes (journal section 11)
**Suggested commit message:** M9.1: paired attack-suite runner with ablation modes A/B/C
**Known issues:** A10 reported as a miss (suite volume was below the budget limit).

### [8.1] Layout, chat panel and live events — 2026-10-11 14:35 IST — Owner: Kanak-Agrawal-3008
**What has changed:** `frontend/src/App.jsx`, `api.js`, `hooks/useEvents.js`, `components/TopBar.jsx`, `ChatPanel.jsx`, `Console.jsx`, `Toast.jsx`, `index.css`.
**Why:** Judges have needed to see cause and protection side by side: the user-to-agent chat on the left and the moderator console on the right, updated live.
**How:** A single-page split screen with a dark theme, one cyan accent and a per-domain tint on the switcher. Server-Sent Events are used (not WebSockets) because data flows one way; the hook reconnects automatically and the page shows an offline banner. A demo-only user selector sends `X-User` and a token read from an untracked `frontend/.env.local`.
**Tests:** Verified manually in the browser pane against the real gateway: two panels render, chat lines and decisions arrive live, the domain switcher works and the offline banner appears while the gateway is unreachable (T8.1-1,2,4,6). Reconnect after a gateway restart was observed. T8.1-5 (legibility at 50% zoom) is left for the projector rehearsal.
**Deviations from plan:** none
**Last-moment changes:** no
**Suggested commit message:** M8.1: split-screen layout, chat panel and SSE live events
**Known issues:** none

### [8.2] Console: three-stage strip, verdict and popups — 2026-10-11 14:35 IST — Owner: Kanak-Agrawal-3008
**What has changed:** `frontend/src/components/ThreeStageStrip.jsx`, `Seal.jsx`, `DecisionCard.jsx`.
**Why:** The central idea has had to be visible at a glance: what was expected, what the sandbox measured, what really happened, and whether the seal held.
**How:** One component renders every decision. The sandbox bar overshoots the dotted envelope in red when the action does more than asked; the seal icon is intact, absent or cracked (animated) and a drift shows as 'SEAL BROKEN, effect drift (40 to 4000)'. The row below always shows the normal-gate verdict beside the SEALGATE verdict. Buttons call approve, reject, safe version, execute and the judge-clickable 'Insert invoices' trigger; refusals from the server are shown as toasts.
**Tests:** Verified manually: the 61-customer refund shows a red overshoot with Normal gate ALLOW against SEALGATE BLOCK R06 and a popup; the smallest safe version executed from the card; the 40-row transfer was approved by two people, the invoices were inserted, and execution showed the cracked seal with effect drift (40 to 4000) (T8.2-1..3,7).
**Deviations from plan:** none
**Last-moment changes:** no
**Suggested commit message:** M8.2: three-stage strip, seal states, verdict row and popups
**Known issues:** none

### [8.3] Overlays: diff, Shadow Mode, audit — 2026-10-11 14:35 IST — Owner: Kanak-Agrawal-3008
**What has changed:** `frontend/src/components/Overlay.jsx`, `DiffOverlay.jsx`, `ShadowOverlay.jsx`, `AuditDrawer.jsx`.
**Why:** Detail views have been needed without leaving the page: the row-level diff, the total result of a Shadow session with Promote and Discard, and the hash chain with Verify and Replay.
**How:** Overlays close with Esc and on click outside. The diff paginates the first 20 rows per table and colours rows inside the envelope green and outside red. The audit view marks every row from the first broken entry and replays a decision against its stored policy.
**Tests:** Overlays have been built against the endpoints covered by the backend tests (M1.3, M6.2, M6.3). T8.3-1..6 have been exercised through the API-level tests; a full manual pass of each overlay is part of the rehearsal in M9.3.
**Deviations from plan:** none
**Last-moment changes:** no
**Suggested commit message:** M8.3: diff, Shadow Mode and audit overlays
**Known issues:** none

### [8.4] Attack Lab page and AI toggle — 2026-10-11 14:35 IST — Owner: Kanak-Agrawal-3008
**What has changed:** `frontend/src/pages/AttackLab.jsx`, AI toggle in `TopBar.jsx`.
**Why:** The evaluation evidence has had to be shown live, with the suite commit hash, the reported misses and a way for judges to add their own case.
**How:** The page calls `/lab/run` and shows exactly what is returned: per mode attacks stopped and harmless allowed, a row per case with outcomes in modes A, B and C against the pre-registered expectation, and the misses. No number is hard-coded. 'Add your own case' posts to `/lab/case`.
**Tests:** Verified in the browser pane: running the suite returned A 4/23, B 8/23, C 22/23 attacks stopped with 23/23 harmless allowed in every mode, and listed the A10 miss (T8.4-1,2).
**Deviations from plan:** none
**Last-moment changes:** no
**Suggested commit message:** M8.4: Attack Lab page with live ablation results and AI toggle
**Known issues:** none

### [9.2] End-to-end integration and regression — 2026-10-11 14:40 IST — Owner: atharvg44
**What has changed:** `tests/test_e2e.py`, `gateway/reset.py`, `POST /demo/reset`, `Engine.close()`, `gateway/main.py` (lifespan handler replaces the deprecated startup hook; route order), `run.sh`, `reset_demo.sh`.
**Why:** The whole system has had to be green together and the ten demonstration beats have had to run start to finish.
**How:** The ten beats have been driven through the real API with the scripted agents (update, blocked refund, safe version, shadow and discard, sealed transfer broken by inserted data, hospital and shop blocks, AI off, audit tamper, restart). The gateway has also been restarted mid-run against the same data directory. Older gateway state files are now upgraded in place, which a stale file from an early build exposed.
**Tests:** T9.2-1,4,5,6 covered: `pytest -q` reports 210 passed on the build laptop and 210 passed on a fresh clone of the repository with a new virtual environment. T9.2-2 (fresh clone) passed for the test suite; the frontend build of a fresh clone and T9.2-3 (Wi-Fi off, Ollama stopped) remain for the rehearsal; the suite itself needs no network because AI is mocked and defaults to off.
**Deviations from plan:** none
**Last-moment changes:** no
**Suggested commit message:** M9.2: end-to-end integration fixes and regression green
**Known issues:** none

### [9.3] Rehearsal and release (documentation part) — 2026-10-11 14:40 IST — Owner: aryanketkar-15
**What has changed:** `README.md` (setup, run, demo script, limits), `reset_demo.sh`, `docs/PROJECT_JOURNAL.md` (results, misses, performance).
**Why:** The final documentation and a one-command reset have been needed before the timed dry runs.
**How:** The README restates the demo script against the real buttons of the interface, the optional AI configuration and the known limits. The journal results table has been filled exactly as produced, including the A10 miss.
**Tests:** T9.3-4 (reset script) is covered by `test_demo_reset_restores_initial_state`. T9.3-1..3 (three timed dry runs, one offline, with questions) and T9.3-5 (projector) have not been done and remain for the four members.
**Deviations from plan:** Milestone 9.3 is not complete until the dry runs have been performed by the team, so it has not been ticked.
**Last-moment changes:** no
**Suggested commit message:** M9.3: release documentation, demo reset script and final journal
**Known issues:** Dry runs, projector check, `v1.0-vortexa` tag and the final release checklist remain for the humans.

### [UI] Interface refinement — 2026-10-11 16:10 IST — Owner: Kanak-Agrawal-3008
**What has changed:** `frontend/src/api.js` (plain-language headline, units, identifier clean-up), `index.css`, `tailwind.config.js`, and the components `TopBar`, `ChatPanel`, `Console`, `DecisionCard`, `ThreeStageStrip`, `Seal`, `Toast`, plus colour and wording changes in the overlays and the Attack Lab page.
**Why:** The first version has used emoji as icons, repeated the same explanation two or three times on a card, shown raw identifiers and amounts, and given no view of how far an approval has progressed. The team has wanted a calmer, more legible console for judges seated at a distance.
**How:** Emoji have been removed in favour of text. Each decision now opens with one sentence built only from the measured effect ("ops-agent would pay 40 invoices (₹40,000)"), followed by a single verdict line with the rule and the verdict a request-level gate would have given. The strip has been restyled as three plain columns (Asked for, Sandbox measured, Real database) with a dashed line for the limit. A four-step progress line (Requested, Approved n of m, Sealed, Executed or Voided) has been added, the acting user is chosen next to the buttons that need it, technical detail sits behind a Details control, notifications moved to the bottom right so they no longer cover the action list, and the scenarios list carries a one-line hint for each story. One neutral dark palette with a single blue accent is used.
**Tests:** Production build succeeds; checked manually in the browser pane (refund, hospital report and 40-invoice approval screens). No backend change.
**Deviations from plan:** none
**Last-moment changes:** no
**Suggested commit message:** UI: calmer console with plain-language headline, approval progress and no emoji
**Known issues:** The overlays (changes, sandbox review, audit) have received colour and wording changes only and still deserve a full layout pass.

### [UI] Light professional theme — 2026-10-11 16:40 IST — Owner: Kanak-Agrawal-3008
**What has changed:** All colours in `frontend/src` have been moved from a dark palette to a light one (white panels on a pale grey page, dark grey text, a single blue accent, restrained green, amber and red for status), `index.css` component classes, and the seal colours. `gateway/main.py` no longer replays recent events when the live stream connects.
**Why:** The team has wanted a conventional, professional appearance that reads well on a projector and in print, and the replayed history has shown unrelated messages from earlier sessions in the conversation panel.
**How:** Colour values have been replaced one-for-one so that contrast is kept (status colours use the darker GitHub-style tones on white). Panels and buttons carry a one-pixel border and a very light shadow. The event stream now replays nothing by default; a `replay` query parameter remains for debugging.
**Tests:** Production build succeeds; the Live gate screen has been checked in the browser pane; backend tests unchanged.
**Deviations from plan:** none
**Last-moment changes:** no
**Suggested commit message:** UI: light professional theme; stop replaying old events on connect
**Known issues:** The overlays have been re-coloured but not re-laid-out.

### [UI] Dashboard redesign to the supplied mockup — 2026-10-11 17:20 IST — Owner: Kanak-Agrawal-3008
**What has changed:** The frontend has been rebuilt as a dashboard with a left navigation (Live Gate, Attack Lab, Audit, Policy, Agents), a top bar with an organisation switcher showing each organisation's policy version, the AI assist state, a notification bell and a user menu. New or rewritten screens: Live Gate (stat tiles, filterable action stream, selected-action detail with the Requested, Measured and Real stages and the Normal-gate against SEALGATE comparison), the approval sheet, the effect-difference overlay with inside and outside rows and pagination, the Shadow Mode review, the Audit and evidence page with an evidence trail and provenance tab, the Attack Lab page, a read-only Policy viewer, and an Agents registry. The conversation moved into a slide-over opened by "Ask an agent". Backend additions: `GET /orgs`, `/policy`, `/agents` (all organisations, with status and budget use), `/sheet/{id}`, `/audit/{seq}/evidence`; customer, vendor and patient names on measured rows; decision ids in audit payloads; `gateway/evidence.py`; `tests/test_views.py`.
**Why:** The team has produced a reference mockup and has wanted the interface to follow it, while keeping every screen driven by real gateway data (no placeholder numbers).
**How:** Design tokens and component classes live in `index.css`; icons are small inline SVGs. The approval sheet is assembled by the gateway (requester, role, expiry, measured effect, destinations, labels), so the agent's own description is never shown as fact. The evidence trail is rebuilt from the audit log, approvals, seals and the decision record. The Attack Lab now runs rules-only by default (live AI is an explicit option) so that the evaluation is reproducible; the previous behaviour made the page slow when an AI key was configured. Policy versions are counted from the policy versions the gateway has stored.
**Tests:** `pytest -q` reports 228 passed. Every screen has been opened in the browser pane against the live gateway: Live Gate, approval sheet, diff overlay, Shadow review, Audit and evidence, Attack Lab (A 4/23, B 8/23, C 22/23), Policy, Agents and the organisation switcher.
**Deviations from plan:** The mockup's "Last 7 days" and "Filter" controls on the audit page, and the day-over-day percentage on the stat tiles, have not been built because the log holds one session; the mockup's illustrative figures (for example 8/20) are replaced by real results.
**Last-moment changes:** no
**Suggested commit message:** UI: dashboard redesign with policy, agents and evidence screens
**Known issues:** No automated frontend tests. At widths below about 1100 px the Live Gate stacks into one column and has not been tuned further.

### [Agent] Live language-model agent, live activity feed and prompt viewer — 2026-10-11 18:10 IST — Owner: atharvg44
**What has changed:** A live agent driven by a language model (`agents/llm.py`, `agents/llm_agent.py`, `agents/toolspec.py`, `agents/prompts/system.txt`, `docs/agent_prompt.md`). The gateway now publishes three new kinds of live events: `pipeline` (each check it runs, with ok, warn or denied), `sandbox` (every row the sandbox run touched, marked inside or outside what was asked) and `agent` (the agent's prompts, model replies, thoughts, tool calls and results), plus `POST /agent/step`, `GET` and `POST /agent/mode`, and chat requests now go to the model by default. The interface has a tabbed agent drawer (Chat, Live activity with the sandbox revealed row by row as APPROVED or DENIED, and Prompts showing the full system prompt, tools, every message and every raw reply) and a Live LLM or Scripted demo switch. `tests/test_llm_agent.py` (12 tests) with a scripted model.
**Why:** The scripted scenarios have had a hard-coded agent claim and a hard-coded mis-scoped request, and the chat box has understood only a few phrases. The team has wanted every typed request, including general or mistaken questions, to go through a model, and has wanted to see what the agent is doing step by step.
**How:** The model replies with one JSON object per turn (thought, tool, args, intent, reply). A tool call becomes a signed proposal; the gateway's verdict is fed back to the model, which then explains it or calls another tool (at most five turns). Missing details lead to a question, unknown tools are reported back to the model, invalid JSON is retried once, and an unreachable model triggers an honest message and the scripted router as fallback. The agent process receives its signing keys and its own model credentials only (no user tokens, no seal key, no database path; a test scans for this). The measured effect in the gateway has always been real; only the agent's behaviour was scripted, and the scripted mode is kept and labelled as such.
**Tests:** `pytest -q` reports 240 passed, including the new agent tests. The live activity feed and the Prompts tab have been checked in the browser against the real gateway. A live call to a real model has not been completed: the OpenRouter free tier (50 requests per day) and the Gemini quota were both exhausted when this was built, so the first request returned HTTP 429 and the fallback message was shown correctly.
**Deviations from plan:** This extends the playbook (the optional small LLM agent in M7.1) and adds three event types to the event contract; both additions are additive.
**Last-moment changes:** yes (new event types; logged in the journal section 11)
**Suggested commit message:** Agent: live language-model agent, live activity feed and prompt viewer
**Known issues:** Behaviour with a real model is unverified until quota is available; free models may answer slowly or with malformed JSON (handled by one retry, then a message).
