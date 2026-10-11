# SEALGATE — Project Journal
### Research, methodology and progress record · VORTEXA 3.0 · Problem Statement C-01

> **Writing convention:** this journal is written in the **present perfect tense** and in the **third person** ("the team has…"), so that sections can be lifted into a research paper or patent disclosure with minimal editing.
> **Update rule:** after every milestone push, the responsible member adds one line to the **Log** (§12), ticks the **Progress Checklist** (§10), and records any **Last-Moment Change** (§11).

---

## Contents
1. Project Identity
2. Team
3. Problem Context
4. Methodology
5. Evolution of the Concept (Decision Record)
6. Current Design Summary
7. Prior Art and Novelty Position
8. Evaluation Methodology
9. Results (to be completed)
10. Progress Checklist
11. Last-Moment Changes
12. Log
13. Known Limitations
14. Notes for Research Paper
15. Notes for Patent Disclosure
16. Lessons Learned (to be completed)
17. Glossary

---

## 1. Project Identity

| Field | Value |
|---|---|
| Project name | **SEALGATE — Effect-Sealed Authorization for AI Agents** |
| Event | VORTEXA 3.0, 12-hour student hackathon, AIRS, Dr. D. Y. Patil Institute of Technology, Pimpri, Pune |
| Problem statement | C-01 — ActionGate: AI Agent Action Authorization Engine |
| One-line description | The system has been designed to approve what an AI agent's action will **really do**, not what the request says, and to seal that approval so that nothing else can execute. |
| Repository | `sealgate` (to be filled: URL) |
| Reference documents | `SEALGATE_Final_Solution.md`, `SEALGATE_Build_Playbook.md` |

---

## 2. Team

| GitHub ID | Role |
|---|---|
| aryanketkar-15 | Gateway core, integration (repository owner) |
| chetanagrawal721 | Effect resolution, decision rules, domains |
| Kanak-Agrawal-3008 | Frontend and user experience |
| atharvg44 | AI layer, agents, evaluation |

All commits in the repository have been authored by the four members listed above.

---

## 3. Problem Context

AI systems have moved from producing text to taking actions: deleting records, sending messages, issuing refunds and moving money. The team has observed that the interpretation of a request by an agent can differ from the user's intent, and that content read by an agent can be crafted to manipulate it.

The team has identified the central weakness of conventional action gateways: they authorise the **request** (a tool name and its arguments) rather than the **effect** (the specific records, recipients and amounts that the action will change). The same request has been shown to produce materially different effects at approval time and at execution time, and to touch far more than the user asked for.

The VORTEXA booklet has required that approvals apply only to the exact action approved (R6), that explicit rules make the final decision (R4), that every decision including refusals be tamper-evident (R8), and that safe decisions continue when AI is unavailable (R9, R10). The team has interpreted "the exact action" as **the exact measured effect**.

---

## 4. Methodology

The team has followed a five-stage methodology.

### 4.1 Problem-statement selection
The team has evaluated all 21 problem statements in the booklet against competition, innovation gap, technical depth, 12-hour feasibility, demo strength, judge explainability, relevance and AI meaningfulness. The team has shortlisted C-02 (BreachPath), P-03 (RailFlow) and C-01 (ActionGate) and has selected C-01, accepting that it is likely to be crowded, on the basis that it offers the highest ceiling above the baseline and that its correctness clause aligns with a rules-first design.

### 4.2 Threat modelling
The team has enumerated more than sixty failure scenarios for a conventional action gateway across twelve families: single-action effects, sequences and accumulation, multi-agent composition, tool composition, indirect effects and cascades, time and state drift, approval attacks, identity and delegation, gateway integrity, injection and provenance, policy and AI failure, and false positives. The team has observed that most failures arise from a gap between what the gateway evaluates and what actually causes harm.

### 4.3 Solution-space exploration
The team has explored and scored five solution directions: action-chain authorization, effect-bound authorization with budgets, recovery-bounded authorization, cross-agent capability graphs, and label-flow authorization across agents. Each direction has been tested against novelty, feasibility, demo strength, false-positive behaviour and research grounding (see §5).

### 4.4 Literature and prior-art review
The team has reviewed related work on information-flow control, agent security research, approval-binding practices in agent frameworks, identity and agent gateways, policy engines, and infrastructure tooling (see §7). The team has revised its novelty claims downward where close prior art has been found.

### 4.5 Design, build and evaluation
The team has adopted a milestone-based build plan with test cases and verification checkpoints for every milestone, and has pre-registered a paired attack suite (each attack with a benign twin) before implementing the evaluation, in order to avoid tuning results (see §8).

---

## 5. Evolution of the Concept (Decision Record)

Each entry records what the team has decided and why.

| # | Stage | Decision | Rationale |
|---|---|---|---|
| D1 | PS selection | Shortlisted C-02, C-01, P-03 | Highest combined scores; C-02 lowest competition, C-01 highest ceiling, P-03 strongest non-cyber visual |
| D2 | PS selection | **Selected C-01 ActionGate** | Rules-first correctness clause matches a deterministic design; ability to show a baseline failing side by side; AI intrinsic to the problem |
| D3 | First concept: **TETHER** (recovery-bounded authorization) | Authorize only actions that remain provably reversible within a recovery budget | Strong demo (undo verification failing on a cascade). **Superseded** because it does not address data leaks across agents and its undo-verification forge carries high build risk |
| D4 | Second concept: **CUSTODY** (label flow across agents) | Track data labels through agents and block flows to uncleared destinations | Addressed multi-agent composition. **Superseded** after the literature review found close prior art in runtime label-flow systems and after the team found that context-level labels over-block in realistic workflows |
| D5 | Reframing | Moved the headline from label flow to **effect-bound authorization** | Required by the booklet (R5, R6); open in reviewed approval-binding work; low false positives |
| D6 | **SEALGATE** adopted | Approvals sealed to measured effect, provenance, label-catalog version, policy version and state version | Directly targets R6; produces a clear demonstration (40 → 4,000 rows) |
| D7 | Novelty correction | Acknowledged Terraform saved plans as the closest analogue | Honest positioning; difference lies in application to agents with intent bounds, labels, separation of duties and typed drift |
| D8 | Engineering correction | Introduced a **transactional outbox** | Emails and payments cannot be rolled back; delivery only after the seal verifies and commits |
| D9 | Engineering correction | Stored full decision inputs in the log | Replay cannot re-resolve against a changed database |
| D10 | Engineering correction | Bound the **label-catalog version** into the seal and named "label drift" separately | Relabelling between approval and execution has been identified as a distinct failure |
| D11 | New feature | **Smallest safe version** (effect-level counterfactual) | Turns blocks into actionable alternatives; reduces false-positive pressure; not found in the reviewed related work |
| D12 | Evaluation design | **Paired, pre-registered ablation** (modes A/B/C) | Answers the concern that a self-built baseline would be a strawman |
| D13 | New feature | **Expected-effect envelope** derived from the user's instruction | Converts "is it doing more than asked?" into a deterministic check; gives the AI a meaningful, bounded role |
| D14 | New feature | **Shadow Mode** — held agents continue in a sandbox; humans approve the final result | Reduces approval fatigue; captures multi-step behaviour as one total diff |
| D15 | Scope | Three demonstration domains (banking, hospital, e-commerce) with one policy file each | Demonstrates generality; banking has been chosen as the main narrative |
| D16 | UI | Two pages plus three overlays; split screen (user↔agent chat and moderator console) | Judges see cause and protection simultaneously; reduced cognitive load |
| D17 | Architecture | Agents can reach the system only through the gateway API; only the gateway holds database paths and credentials | Makes bypass structurally impossible rather than detected |
| D18 | AI role | AI has been restricted to escalate-only: envelope extraction, claim-vs-effect checks, paraphrase sentry, explanations | Satisfies R4; decisions remain reproducible; safety does not depend on AI availability |

---

## 6. Current Design Summary

The system has been designed as a gateway that sits between AI agents and organisational systems. For every proposed action, the gateway has been designed to:

1. verify the agent's signed request and check it against the organisation's policy file;
2. derive an **expected-effect envelope** from the user's original instruction (AI) or from policy defaults;
3. execute the action on a **sandbox copy** and measure its exact effect, including cascades, expanded recipient lists, amounts and data labels;
4. compare the measured effect with the envelope and apply deterministic rules to decide ALLOW, HOLD or BLOCK, with AI permitted only to escalate;
5. compute the **smallest safe version** when an action is blocked or held;
6. route held agents into **Shadow Mode** where configured;
7. issue an **effect seal** on approval, binding the action, effect, provenance, label-catalog version, policy version and state version;
8. execute on the real database inside a single transaction, re-measuring the effect and committing only if it matches the seal; deliver irreversible messages and payments via a **transactional outbox** after commit;
9. record every decision, including refusals, in a **hash-chained log** that stores the full decision inputs for replay.

Full specification: `SEALGATE_Final_Solution.md`.

---

## 7. Prior Art and Novelty Position

### 7.1 Related work identified
| Area | Work / practice | Relation to SEALGATE |
|---|---|---|
| Infrastructure as code | Terraform saved-plan apply refusing stale plans | Closest analogue for effect binding |
| Information-flow control | Denning lattice model; Bell-LaPadula; Biba | Foundation for data labels (used only as an input) |
| Agent security research | CaMeL, FIDES; and, from the team's searches (papers to be read in full): AgentFlow, FlowSeal, FlowReview, SafeFlow, AIsafePy | Label/flow control for agents; prior art for the earlier CUSTODY concept |
| Approval binding | Agent framework guidance binding approvals to call IDs or arguments; documented failures ("Loopjacking"-style research) | Baseline (mode B) that SEALGATE extends to effects |
| Identity / agent gateways | Commercial agent gateways (identity, tool permissions, credential isolation) | Complementary layer |
| Policy engines | OPA, Cedar, AgentSpec, SAFi | Per-call decisions; SEALGATE adds stateful effect handling |
| Engineering patterns | Dry runs, transactions, transactional outbox, hash chains | Building blocks |

All citations above must be verified against the original sources before publication.

### 7.2 Novelty position
The team has positioned the contribution as an **under-explored combination applied to AI agents**, not as new theory:
1. effect-sealed approvals with typed drift reasons;
2. request-vs-reality checking against an envelope derived from the user's own instruction;
3. a deterministic smallest-safe-version engine operating on resolved effects;
4. Shadow Mode with diff-verified promotion;
5. paired, pre-registered evaluation via ablation of the same gateway.

Items 3 and 4 have not been found in the related work reviewed by the team; this is a statement about the reviewed literature, not a claim of absolute novelty.

---

## 8. Evaluation Methodology

| Element | Description |
|---|---|
| Suite | 22 attack cases across three domains, each paired with a benign twin |
| Pre-registration | The suite has been committed before any gateway logic existed. Commit hash: `__________` · time: `__________` |
| Ablation modes | **A** allowlist + default deny · **B** A + argument-hash approval binding · **C** full SEALGATE |
| Metrics | Attacks stopped per mode; benign twins allowed per mode; known misses listed explicitly |
| Isolation | Each case runs on a freshly seeded fictional database |
| AI conditions | Suite run with AI enabled and with AI disabled |
| Data | Fictional only; no real personal or financial records |

Additions to the suite after pre-registration must be logged in §11 with the reason.

---

## 9. Results (to be completed)

| Mode | Attacks stopped | Benign allowed | Notes |
|---|---|---|---|
| A | 4 / 23 | 23 / 23 | allowlist + default deny + signatures; A18 (structural) and A19-A21 are the stopped cases |
| B | 8 / 23 | 23 / 23 | adds protected-action approval and argument-bound approvals |
| C (AI on) | not measured | not measured | a live Gemini run was attempted on 2026-10-11; the model answered in 4 to 13 s and the account then returned HTTP 429 (quota exhausted), so most calls fell back to rules-only and the run cannot be reported as an AI-on result. The AI path is covered by mocked tests |
| C (AI off) | 22 / 23 | 23 / 23 | all pre-registered expectations met except A10 |

Run of 2026-10-11 on the build laptop (`python -m lab.runner`, 14.5 s). "Attack stopped" means BLOCK, HOLD, VOID, REFUSED or (for A18) a structural guarantee; "benign allowed" means not BLOCK, VOID or REFUSED. The 23 pairs are the 22 pre-registered pairs plus case A23, which was added after registration (see section 11).

**Known misses:**
- A10 (budget split across three agents, 90 refunds of Rs 1,000): the gateway allowed it because Rs 90,000 stays inside both the per-agent (Rs 50,000 each) and the shared (Rs 1,00,000) limits. The pre-registered volume was below the limit; the case has been kept and reported, and A23 (120 refunds) has been added, which mode C holds.
- Structural limits that the suite cannot exercise: data moved through channels the gateway never sees, and personal data paraphrased into free text (best-effort only).

**Performance observations:** decision latency has been measured at a median of 47 ms (maximum 65 ms) for the 212-row refund, including the sandbox copy, measurement, rules and logging, and 54 ms for a one-row update including execution (excluding AI). AI latency has not been measured. The fallback rate has been 100% in the suite run because no AI provider was configured.

---

## 10. Progress Checklist

### Phase 0 — Setup
- [x] 0.1 Repository, identities, authorship guards — aryanketkar-15
- [x] 0.2 Runnable scaffolds — all
- [x] 0.3 API contract, schemas, pre-registered suite — aryanketkar-15, atharvg44
- [x] **Phase 0 checkpoint** (tag `phase-0-ok`)

### Phase 1 — Gateway foundation
- [x] 1.1 Policy loader, registry, default deny — aryanketkar-15
- [x] 1.2 Signed requests, nonces, timestamps — aryanketkar-15
- [x] 1.3 Hash-chained audit log — aryanketkar-15
- [x] **Phase 1 checkpoint**

### Phase 2 — Effect resolution
- [x] 2.1 Bank seed DB and sandbox copies — chetanagrawal721
- [x] 2.2 Resolvers and Effect object — chetanagrawal721
- [x] 2.3 Data labels and destinations — chetanagrawal721
- [ ] **Phase 2 checkpoint**

### Phase 3 — Decision engine
- [x] 3.1 Envelope and envelope check — chetanagrawal721
- [x] 3.2 Rules R01–R12, tiers, decide() — chetanagrawal721
- [x] 3.3 Resource-keyed budgets — chetanagrawal721
- [ ] **Phase 3 checkpoint**

### Phase 4 — Seal & execution (hour-6 gate)
- [x] 4.1 Approvals and separation of duties — aryanketkar-15
- [x] 4.2 Effect seal with typed drift — aryanketkar-15
- [x] 4.3 One-transaction execution and outbox — aryanketkar-15
- [ ] **Phase 4 checkpoint**

### Phase 5 — AI layer
- [x] 5.1 AI client, validation, fallback — atharvg44
- [x] 5.2 Envelope from instruction, claim-vs-effect — atharvg44
- [x] 5.3 Paraphrase sentry, explanations — atharvg44
- [ ] **Phase 5 checkpoint**

### Phase 6 — Signature features
- [x] 6.1 Smallest safe version — chetanagrawal721
- [x] 6.2 Shadow Mode — chetanagrawal721
- [x] 6.3 Replay and honeytoken freeze — aryanketkar-15
- [ ] **Phase 6 checkpoint**

### Phase 7 — Agents & domains
- [x] 7.1 Agents, tools, scenarios — atharvg44
- [x] 7.2 Hospital and e-commerce domains — chetanagrawal721
- [ ] **Phase 7 checkpoint**

### Phase 8 — Frontend
- [x] 8.1 Layout, chat, live events — Kanak-Agrawal-3008
- [x] 8.2 Three-stage strip, verdict, popups — Kanak-Agrawal-3008
- [x] 8.3 Diff, Shadow, Audit overlays — Kanak-Agrawal-3008
- [x] 8.4 Attack Lab page, AI toggle — Kanak-Agrawal-3008
- [ ] **Phase 8 checkpoint**

### Phase 9 — Evaluation & release
- [x] 9.1 Attack Lab runner — atharvg44
- [x] 9.2 End-to-end integration — all
- [ ] 9.3 Rehearsal and release (`v1.0-vortexa`) — all
- [ ] **Final Release Checklist complete**

---

## 11. Last-Moment Changes

Record every change made after Phase 0 to the contract, suite, scope or design.

| Date / time (IST) | Changed by | What has changed | Why | Impact on tests / demo |
|---|---|---|---|---|
| 2026-10-11 | Team | Headline has moved from label flow (CUSTODY) to effect-sealed authorization (SEALGATE) | Prior art and over-blocking found in label-flow approach | Multi-agent kept as one scenario using object labels |
| 2026-10-11 | Team | Transactional outbox has been added | Irreversible sends cannot be rolled back | New tests T4.3-3, T4.3-4 |
| 2026-10-11 | Team | Label-catalog version has been added to the seal | Relabelling between approval and execution | New drift type `label_drift` |
| 2026-10-11 | Team | Expected-effect envelope and Shadow Mode have been added | Deterministic "more than asked" check; reduced approval fatigue | New milestones 3.1, 5.2, 6.2 |
| 2026-10-11 | Team | Demo has been expanded to three domains | Demonstrate generality | Milestone 7.2; hospital is cuttable |
| 2026-10-11 | atharvg44 | Case A23 has been added to the paired suite (budget split across three agents, 120 refunds) | Pre-registered case A10 (90 refunds) stays inside both budget limits (Rs 90,000 of the Rs 1,00,000 resource budget), so the gateway correctly allows it; A10 is retained and reported as a miss, and A23 has been added with a corrected volume | Mode C stops A23; A10 remains a reported miss |
| | | | | |

---

## 12. Log

One line per milestone push, decision, or notable event. Newest at the bottom.

| Date / time (IST) | Member | Type | Entry | Commit |
|---|---|---|---|---|
| 2026-10-11 09:52 | Team | Decision | The team has evaluated all 21 VORTEXA problem statements and has shortlisted C-02, C-01 and P-03. | — |
| 2026-10-11 10:03 | Team | Decision | The team has leaned toward C-01 ActionGate. | — |
| 2026-10-11 10:29 | Team | Design | The team has developed the TETHER concept (recovery-bounded authorization). | — |
| 2026-10-11 11:41 | Team | Design | The team has explored label flow across agents (CUSTODY) and has produced a 60+ case threat model. | — |
| 2026-10-11 12:10 | Team | Review | A literature scan has identified close prior art for label flow; the team has reframed the headline to effect-bound authorization. | — |
| 2026-10-11 12:13 | Team | Design | The team has adopted SEALGATE with five engineering fixes and the smallest-safe-version engine. | — |
| 2026-10-11 12:34 | Team | Design | The team has added the expected-effect envelope, Shadow Mode and three demonstration domains. | — |
| 2026-10-11 12:40 | Team | Design | The team has fixed the connection model: agents reach the system only through the gateway API. | — |
| 2026-10-11 12:46 | Team | Docs | The team has produced the final solution document. | — |
| 2026-10-11 13:02 | Team | Docs | The team has produced the build playbook and this journal. | — |
| 2026-10-11 15:15 | aryanketkar-15 | Milestone | M0.1–M0.3 — The team has created the repository guards, runnable scaffolds, the frozen API contract and the pre-registered 22-pair suite. | |
| 2026-10-11 15:15 | aryanketkar-15 | Milestone | M1.1–M1.3 — The team has implemented the policy loader, signed requests with nonce and timestamp checks, and the hash-chained audit log (39 tests passing). | |
| 2026-10-11 13:57 | aryanketkar-15 | Milestone | M0.1 — repository, ignore rules and authorship guard hooks have been added. | |
| 2026-10-11 13:57 | aryanketkar-15 | Milestone | M0.2 — runnable gateway, agents and frontend scaffolds have been added. | |
| 2026-10-11 13:57 | aryanketkar-15 | Milestone | M0.3 — the API contract, mock API and 22-pair attack suite have been added. | |
| 2026-10-11 13:57 | aryanketkar-15 | Milestone | M1.1 — the policy loader, registry and default deny have been implemented. | |
| 2026-10-11 13:57 | aryanketkar-15 | Milestone | M1.2 — HMAC-signed proposals with nonce and timestamp checks have been implemented. | |
| 2026-10-11 13:57 | aryanketkar-15 | Milestone | M1.3 — the hash-chained audit log with verification has been implemented. | |
| 2026-10-11 14:00 | chetanagrawal721 | Milestone | M2.1 — the deterministic bank seed and sandbox copy utility have been implemented. | |
| 2026-10-11 14:00 | chetanagrawal721 | Milestone | M2.2 — sandbox resolvers returning exact effects have been implemented. | |
| 2026-10-11 14:00 | chetanagrawal721 | Milestone | M2.3 — effect-level data labels, destinations and provenance have been implemented. | |
| 2026-10-11 14:03 | chetanagrawal721 | Milestone | M3.1 — the expected-effect envelope and its deterministic check have been implemented. | |
| 2026-10-11 14:03 | chetanagrawal721 | Milestone | M3.2 — the deterministic rules, tiers, decide() and baseline verdict have been implemented. | |
| 2026-10-11 14:03 | chetanagrawal721 | Milestone | M3.3 — resource-keyed cumulative budgets have been implemented. | |
| 2026-10-11 14:10 | aryanketkar-15 | Milestone | M4.1 — approvals with separation of duties and tiered approvers have been implemented. | |
| 2026-10-11 14:10 | aryanketkar-15 | Milestone | M4.2 — the effect-bound seal with typed drift detection has been implemented. | |
| 2026-10-11 14:10 | aryanketkar-15 | Milestone | M4.3 — one-transaction sealed execution and the transactional outbox have been implemented. | |
| 2026-10-11 14:13 | atharvg44 | Milestone | M5.1 — the escalate-only AI client with schema validation and fallback has been implemented. | |
| 2026-10-11 14:13 | atharvg44 | Milestone | M5.2 — the clamped AI envelope and claim-vs-effect escalation have been implemented. | |
| 2026-10-11 14:13 | atharvg44 | Milestone | M5.3 — the best-effort paraphrase sentry and approver explanations have been implemented. | |
| 2026-10-11 14:17 | chetanagrawal721 | Milestone | M6.1 — the deterministic smallest-safe-version engine has been implemented. | |
| 2026-10-11 14:17 | chetanagrawal721 | Milestone | M6.2 — Shadow Mode with diff-verified promotion has been implemented. | |
| 2026-10-11 14:17 | aryanketkar-15 | Milestone | M6.3 — decision replay and the honeytoken freeze with unfreeze have been implemented. | |
| 2026-10-11 14:22 | atharvg44 | Milestone | M7.1 — signed agent tools, scripted scenarios and the event stream have been implemented. | |
| 2026-10-11 14:22 | chetanagrawal721 | Milestone | M7.2 — the hospital and e-commerce domains have been implemented through policy files and resolvers. | |
| 2026-10-11 14:28 | atharvg44 | Milestone | M9.1 — the paired attack-suite runner with ablation modes A, B and C has been implemented (A 4/22, B 8/22, C 21/22 attacks stopped; all benign twins allowed). | |
| 2026-10-11 14:35 | Kanak-Agrawal-3008 | Milestone | M8.1 — the split-screen layout, chat panel and live event stream have been implemented. | |
| 2026-10-11 14:35 | Kanak-Agrawal-3008 | Milestone | M8.2 — the three-stage strip, seal states, verdict row and popups have been implemented. | |
| 2026-10-11 14:35 | Kanak-Agrawal-3008 | Milestone | M8.3 — the diff, Shadow Mode and audit overlays have been implemented. | |
| 2026-10-11 14:35 | Kanak-Agrawal-3008 | Milestone | M8.4 — the Attack Lab page with live ablation results and the AI toggle have been implemented. | |
| 2026-10-11 14:40 | atharvg44 | Milestone | M9.2 — end-to-end integration has been verified (210 tests passing locally and on a fresh clone). | |
| 2026-10-11 14:40 | aryanketkar-15 | Milestone | M9.3 — the release README, reset script and journal results have been written; rehearsal is pending. | |

**Entry types:** Decision · Design · Review · Milestone · Fix · Change · Test · Result · Docs

---

## 13. Known Limitations

| Limitation | Current mitigation |
|---|---|
| Effect-level labels cannot detect personal data paraphrased into free text | Best-effort AI paraphrase sentry (escalation only) |
| The gateway observes only data it has served | Agents are sandboxed so that the gateway is their only egress; covert channels are out of scope |
| External services cannot always be dry-run | Transactional outbox; actions without a dry run are treated as unverifiable and held |
| Envelope quality depends on the clarity of the instruction | AI envelopes are clamped to policy limits and shown for confirmation |
| Sandbox copies have been implemented as file copies | Production would use transactions, savepoints or database branching |
| The gateway is the trusted computing base | Kept small; policy changes require two humans and are logged |

---

## 14. Notes for Research Paper

**Working title:** *SEALGATE: Effect-Sealed, Intent-Bounded Authorization for Tool-Using AI Agents*

**Suggested structure**
1. Introduction — agents act; approvals bind to requests, harm lies in effects
2. Threat model — families from §4.2
3. Design — envelope, sandbox resolution, seal, typed drift, smallest safe version, Shadow Mode, outbox, replayable log
4. Implementation — stack and domains
5. Evaluation — paired pre-registered ablation (§8, §9)
6. Related work — §7
7. Limitations — §13
8. Conclusion

**Contribution statements (draft)**
- The work has formalised approval as a commitment to a measured effect rather than a request.
- The work has introduced a deterministic effect-level counterfactual for actionable denials.
- The work has proposed sandboxed review with diff-verified promotion to reduce approval fatigue.
- The work has evaluated the design with a paired, pre-registered ablation.

**Before submission:** read all cited papers in full; verify every figure; disclose tools and external assistance according to the venue's policy.

---

## 15. Notes for Patent Disclosure

> This section records material for a possible future disclosure. It is not legal advice; a registered patent agent or attorney should be consulted.

**Candidate inventive concepts (for discussion with an agent/attorney)**
1. A method of authorising an AI agent action by resolving the action against a sandbox copy to obtain an effect set, deriving an expected-effect envelope from the originating natural-language instruction, and deciding on the comparison of the two.
2. A sealed approval token binding the effect hash, provenance path, label-catalog version, policy version and state version, with typed drift classification at execution.
3. A method of computing a minimal modification of a resolved effect that changes an authorization outcome, re-evaluating it, and re-sealing it upon approver acceptance.
4. A method of continuing a held agent's actions in a sandbox, recording them, and promoting them to the real system only if the real diff equals the sandbox diff.

**Prior art to address:** §7.1, especially Terraform saved plans, approval-binding practices and label-flow systems.

**Important timing note:** public demonstration at the hackathon, public repositories and publications may count as public disclosure. Patent laws differ by country, and India's grace-period provisions are limited. If patent protection is intended, the team should seek advice **before** the public demo or before making the repository public.

**Evidence of conception:** this journal, the decision record (§5), dated log (§12) and the git history have been maintained as a dated record of conception and development by the four team members.

---

## 16. Lessons Learned (to be completed)

| Area | Lesson |
|---|---|
| Selection | |
| Design | |
| Build | |
| Demo | |
| Teamwork | |

---

## 17. Glossary

| Term | Meaning |
|---|---|
| **Effect** | The exact records, recipients, amounts, destinations and labels an action would change |
| **Envelope** | The expected bounds of an action's effect, derived from the user's instruction or policy defaults |
| **Seal** | A signed approval token bound to a measured effect and its context |
| **Drift** | A difference between the sealed context and the context at execution (args, effect, label, policy, state) |
| **Smallest safe version** | The minimal change to an effect that makes it acceptable under the rules |
| **Shadow Mode** | Sandboxed continuation of a held agent's actions, reviewed as a total diff |
| **Outbox** | A table holding irreversible messages/payments that are delivered only after commit |
| **Mode A/B/C** | Ablation configurations of the gateway used in evaluation |
| **Benign twin** | A harmless variant of an attack case used to measure false positives |
