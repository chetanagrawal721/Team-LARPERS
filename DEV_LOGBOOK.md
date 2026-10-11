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
