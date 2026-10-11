# SEALGATE — Rules for Claude Code sessions

## Project summary
SEALGATE (VORTEXA 3.0, problem C-01 ActionGate) is an authorization gateway for AI agents.
- Agents can only call the gateway API (`POST /propose`); they hold no DB path and no credentials.
- Every action is first run on a sandbox copy of the database to measure its real **effect** (rows, recipients, amounts, labels).
- The effect is compared with an **envelope** (what the user's instruction implies, or the policy default).
- Deterministic rules R01–R12 (+ R99 default deny) decide ALLOW / HOLD / BLOCK. AI may only escalate: `final = max(rules, AI)`.
- Approvals are **sealed** to the measured effect; at execution the gateway re-measures inside one transaction and voids on any typed drift.
- Also: smallest safe version, Shadow Mode, data labels, resource-keyed budgets, outbox, hash-chained audit log, paired Attack Lab (modes A/B/C).
- Three demo domains (bank, hospital, shop) share one engine; only the policy YAML and seed data differ.
- Stack: Python 3.11, FastAPI, Pydantic, SQLite, PyYAML, pytest, httpx; React + Vite + Tailwind; optional Ollama.

Documents (read before working):
- Design: [docs/SEALGATE_Final_Solution.md](docs/SEALGATE_Final_Solution.md)
- Build plan (milestones, tests, git rules): [docs/SEALGATE_Build_Playbook.md](docs/SEALGATE_Build_Playbook.md)
- Research/decision record: [docs/PROJECT_JOURNAL.md](docs/PROJECT_JOURNAL.md)
- Engineering logbook: [DEV_LOGBOOK.md](DEV_LOGBOOK.md)

## Team and ownership
| GitHub ID | Role | Branch |
|---|---|---|
| aryanketkar-15 | Gateway core, integration | `aryan/gateway` |
| chetanagrawal721 | Effects, rules, domains | `chetan/effects` |
| Kanak-Agrawal-3008 | Frontend | `kanak/frontend` |
| atharvg44 | AI, agents, evaluation | `atharv/ai-agents` |

Milestone owners are listed in the playbook (section B and each milestone header).

## Working rules
1. Work **one milestone at a time** from the playbook, in dependency order (playbook section D). Before starting, state the milestone ID and confirm its dependencies are done.
2. For each milestone: implement → write and run its test cases → walk through its verification checklist → report results. Never mark a milestone done with failing tests.
3. **Git:** commit locally after each milestone, authored as that milestone's owner (`git -c user.name=<github-id> -c user.email=<github-id>@users.noreply.github.com commit ...`; never change git config). After each milestone commit, `git push origin main`. **Never** run `git tag`, `git merge`, `git rebase`, `git reset` or force-push unless the human asks. `git status` and `git diff` are always allowed. Use the commit message from the playbook.
4. **Never add** `Co-Authored-By` trailers or "Generated with" lines anywhere (commit messages, PR text, files). Claude must never appear as author, committer, contributor or co-author.
5. Never create or edit `.env` with real secrets; only `.env.example` with placeholders.
6. Never stage or suggest committing: `.db` files, `node_modules/`, `.venv/`, `__pycache__/`, sandbox copies (`gateway/data/sandbox/`), `*.log`, `lab/results_*.json`, `audit_export*.json`, model files.
7. Agents (`agents/`) must never contain database paths, `sqlite`, or user tokens. Only the gateway touches data.
8. Fictional data only. Everything must work offline; AI is optional and must fall back safely.
9. Use parameterised SQL only (table names from fixed whitelists, never agent input). `yaml.safe_load` only.
10. Do not add libraries or patterns beyond the playbook without explaining why and asking first.
11. Do not change the API contract (`gateway/schemas.py`, `docs/api.md`) or `lab/suite.yaml` after Milestone 0.3 without asking. Any such change is a "last-moment change" and must be logged in PROJECT_JOURNAL.md §11. `lab/suite.yaml` may only grow by added cases.
12. Do not modify files owned by another milestone/person's area without saying so first (e.g. `gateway/main.py` and `gateway/decide.py` are touched by several people).

## Logbook rules
- `DEV_LOGBOOK.md` = engineering detail (what changed, how, why) per milestone.
- `PROJECT_JOURNAL.md` = research narrative (decisions, methodology, results).
- Style for BOTH: **present perfect tense, third person, team voice** ("The team has implemented…", "The gateway has been changed to…"). Never name an AI assistant or tool as an author or contributor.
- After every milestone you must:
  1. Add the DEV_LOGBOOK.md entry (template in that file).
  2. Tick the milestone in both checklists (DEV_LOGBOOK.md progress table and PROJECT_JOURNAL.md §10).
  3. Add one line to the PROJECT_JOURNAL.md §12 Log (leave the Commit column blank for the human).
  4. Print the exact git commands for the human (`git status`, `git add <files>`, `git commit -m "<playbook message>"`, `git push origin <branch>`) plus the files that must NOT be committed.
  5. Stop and wait until the human confirms the push.
- If anything changed from the plan, also add a row to PROJECT_JOURNAL.md §11.
- After every milestone also run `pytest -q`, show the results and list the files changed.
