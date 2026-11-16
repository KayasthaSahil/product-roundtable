# Product Review Committee Charter

> Source of truth for building the committee's skills and agents.
> Every agent, skill, tool grant and output format is derived from this document. Phase-by-phase dispatch eligibility and triggers are defined in `specialist-dispatch-matrix.md`; this charter defines role purpose and phase participation, while the matrix is authoritative for actual dispatch.

---

## 0. Purpose & Operating Principles

**Purpose:** Run a rigorous, autonomous, multi-perspective review of the product MVP and produce (a) a transparent record of everything the committee found, debated and decided, and (b) a complete planning pack that turns those decisions into a prioritised, dependency-aware set of tickets for future work.

**Quality bar:** The product must feel like a genuinely impressive, professionally built product — never like an AI-generated student project. Every finding and decision is judged against that bar.

### Operating principles

1. **Fully autonomous.** The committee runs end to end without human involvement. No agent pauses for user input. The Chair is the final decision authority.
2. **Human reviews at the end.** The product owner reads the Review Report (HTML) after the review is complete and gives feedback then. Feedback may trigger a follow-up review cycle.
3. **Evidence first.** Every finding must carry evidence (file + line, command output, screenshot, recording, or reproducible steps). Findings without evidence cannot be accepted.
4. **Independence before debate.** In P2, specialists review alone and do not read each other's findings. Cross-influence only begins in P4.
5. **No self-verification.** A finding is never verified by the agent that raised it.
6. **Decisions, not endless debate.** Debates are capped; the Chair decides with written rationale.
7. **Preserve what works.** Every reviewer also records strengths that must be kept, so the committee does not "fix" good parts.
8. **Realistic engineering.** Recommendations are sized for the product's actual scale and team, not hypothetical enterprise scenarios.

### Out of scope

- **Subjective or creative quality of the product's generated content** (for example writing style, aesthetics, motion taste, audio feel), if the product generates any. The product owner judges this directly. The committee only reviews the *technical correctness* of the system that produces it (see Media & Processing Pipeline Engineer).

---

## 1. Workspace Layout

All committee work lives in the repo under `.review/`:

```
.review/
├── brief/
│   ├── product-brief.md          # P0: vision, users, quality bar, constraints
│   ├── repo-map.md               # P0: modules, boundaries, entry points
│   ├── stack-profile.md          # P0: detected tech stack, commands, conventions (§1.1)
│   ├── existing-context.md       # P0: digest of context files already in the repo (§1.2)
│   └── review-scope.md           # P0: what is reviewed, by whom, in which phase
├── findings/
│   └── <ROLE>.json               # P2: one file per reviewer (schema in §2.1)
├── verification/
│   └── verification-log.json     # P3: verdict per finding
├── debates/
│   └── DBT-<NNN>/                # P4: one folder per dispute, one file per agent per round
├── evidence/
│   └── <ROLE>/                   # screenshots, recordings, outputs cited by findings
├── runs/
│   └── run-log.json              # Shared log of long-running commands (standards §10)
├── decisions/
│   └── decision-log.json         # P5: every decision with rationale
├── gate/
│   └── readiness-gate.json       # P6: risk/effort/cost assessment per roadmap item
├── codebase-atlas/               # SCIS: evidence-backed factual repository map, graph and source index
├── report/
│   └── index.html                # Generated product-first Review Report
├── implementation/               # P5–P6: Implementation Planning Pack (§7)
│   └── tickets/TASK-NNN.json      # Canonical, traceable implementation units
└── state.json                    # Current phase, progress, round counters
```

Structured data (`.json`) is the single source; the HTML report and the implementation pack are generated from it.

### 1.1 Stack Adaptation

Agents are **stack-agnostic by design**. No agent definition hard-codes a language, framework or tool. Each agent adapts to the project it finds at review time.

**How it works**
1. **Detection (P0).** The Principal Architect inspects the repo (package manifests, lockfiles, build configs, Dockerfiles, framework and build/render-engine configs, CI files, test configs) and writes `stack-profile.md`.
2. **Stack profile contents:**
   - Languages, frameworks and versions (frontend, backend, AI SDK, render engine if any, database, queue)
   - Package manager and how to install, build and start the app
   - Test framework, and how to run a **single** test file or case (never the full suite)
   - Linting, formatting and type-checking commands
   - Project conventions observed (folder structure, naming, state management, API style)
   - Which product surfaces exist (UI, API, CLI, processing/render pipeline, AI layer)
   - Available review tooling in the environment (e.g. browser automation for screenshots)
3. **Role assignment.** All 17 specialist agents remain installed, callable and active for the review cycle. Do not merge, deactivate or remove roles. The Chair assigns each role its full existing responsibilities and records applicability; the specialist-dispatch matrix governs phase-specific dispatch. A missing product surface may justify a phase-specific non-dispatch only under that matrix, never removal of the role. Lack of browser tooling changes evidence method/confidence, not the presence of UX/VIS capabilities.
4. **Adaptive review.** The Chair includes a compact stack-profile summary and relevant stack details in each dispatch packet. Agents consult the full `stack-profile.md` only when the assigned task requires it, then apply their review area through the idioms of that stack. Example: the Frontend Engineer checks hook dependencies and memoization in React, or reactivity and stores in Svelte. The Backend Engineer checks async handling and validation models in FastAPI, or middleware and error handling in Express.
5. **Judging against the stack's own conventions.** Findings measure the code against that stack's established best practices *and* the project's own conventions, not a generic or foreign standard.
6. **Re-detection.** If the stack changes (e.g. after implementation, before P7), the profile is regenerated.

**Shared Codebase Intelligence System (SCIS):** P0 builds a persistent, evidence-backed Codebase Atlas under `.review/codebase-atlas/`; P7 refreshes it for the changed snapshot. It is descriptive factual context, not an evaluation or a substitute for source inspection. See `.claude/skills/codebase-atlas/SKILL.md` and the specialist dispatch matrix. All 17 specialist agents, their existing phase assignments, responsibilities and outputs remain intact. P2 reviewers may share factual Atlas records but never one another's conclusions.

**Constraint:** tool *permissions* are fixed when an agent is defined. Each agent is therefore granted a minimal, stack-independent set (read, search, limited shell). Stack-specific commands come from `stack-profile.md` and remain bound by the execution rules in `review-standards.md` §10.

### 1.2 Existing Repository Context

Before forming any opinion, the committee absorbs the context the repo already contains.

**What is collected (P0):** every existing context source, for example:
- `README*`, `CLAUDE.md`, `AGENTS.md`, and other AI-agent context files
- `docs/`, architecture notes, ADRs, PRDs, specs, design notes, roadmaps
- Existing `.claude/` skills, agents and commands
- `CHANGELOG`, `TODO`/`FIXME` notes, issue or plan files
- Config comments, `.env.example`, sample projects and fixtures

**Output:** `brief/existing-context.md` lists each source with its path, a short summary, what it says about intent and decisions, and a **trust level**:
- `verified`: matches the code
- `unverified`: not yet checked
- `outdated`: contradicts the code (this is itself a Documentation finding)

**Rules**
- Every agent receives the relevant entries from `existing-context.md` through its dispatch packet; it reads only sources needed for its assigned area. The full context inventory is not a mandatory read for every invocation.
- Documented intent informs the review, but **the code is the truth**. Where docs and code disagree, the agent reports the gap and does not assume either is right.
- Decisions already recorded in the repo (e.g. ADRs) are respected as context. They can still be challenged, but only with evidence.
- The product brief is built on this context, not invented from scratch.

---

## 2. Shared Protocols (apply to every agent)

> Finding schema, severity, categories, confidence, recommendation quality, decision dispositions, execution discipline and re-review rules are defined in **`review-standards.md`**, which every agent loads. This section covers only the process mechanics.

### 2.4 Debate protocol (P4)

1. Chair groups conflicting or competing findings into a dispute `DBT-<NNN>` with a clear question.
2. **Round 1 — Positions:** each involved agent states its position with evidence.
3. **Round 2 — Rebuttal:** each agent responds to the opposing positions.
4. **Optional Round 3 — Final rebuttal:** only if new evidence appeared in Round 2.
5. **Red Team challenge:** may raise one reconsideration request per dispute.
6. **Chair decision:** written decision, rationale, trade-offs accepted, and dissent recorded.

Hard cap: 3 rounds. No dispute is left open. Unresolved disagreement is recorded as dissent.

### 2.5 Decision dispositions

See `review-standards.md` §9: Accepted · Accepted with modifications · Rejected · Deferred · Requires experiment · Requires additional evidence. Duplicates are marked `merged into <ID>`.

### 2.6 Autonomy rules

- No agent asks the human for input during the review.
- Ambiguity is resolved by the Chair using the product brief; the assumption is logged.
- Strategic decisions are made by the Chair and clearly labelled `strategic` in the report so the product owner can revisit them.
- If a tool or environment step fails (e.g. app won't start), the agent logs it as a finding and continues with what it can review.

---

## 3. Review Phases

The planning review is **complete** at the end of **P6**. At that point the Review Report and the Implementation Planning Pack are final and ready for the product owner. The committee does not implement the plan. **P7**, if invoked later, is a separate post-delivery review of externally implemented changes; it does not perform implementation work.

### P0 — Intake
- **Goal:** Understand the product and set up the review.
- **Lead:** Chair. **Participants:** Principal Architect and PM — Scope & Simplicity. The Scribe is not dispatched unless a specific P0 writing/consistency task is assigned.
- **Activities:** collect existing repo context into `existing-context.md` (§1.2); build and validate the SCIS Codebase Atlas (source inventory, evidence, graph and snapshot); detect the tech stack and write `stack-profile.md` (§1.1); assign areas while retaining all 17 specialist agents and preserving the existing phase-specific dispatch matrix; read the repo and existing docs; write product brief (vision, target users, quality bar, constraints); map repository, modules and boundaries; define review scope and assign areas to roles; agree on finding schema.
- **Outputs:** `existing-context.md`, `stack-profile.md`, `product-brief.md`, `repo-map.md`, `review-scope.md`, `.review/codebase-atlas/`, initial report shell.
- **Exit:** every product area has at least one assigned reviewer.

### P1 — Discovery
- **Goal:** First impressions and market context.
- **Lead:** Chair. **Participants:** PM — User Value and Competitive Analyst; Visual Design and UX are conditional on the product having inspectable user-facing surfaces. The Scribe is not dispatched for routine report generation.
- **Activities:** run the product as a new user; capture first-impression notes and screenshots; build the competitive benchmark; define target-user profiles.
- **Outputs:** first-impression findings, competitive benchmark, user profiles.
- **Exit:** benchmark and first impressions recorded.

### P2 — Independent Review
- **Goal:** Deep review of each area, independently.
- **Lead:** Chair (dispatch only). **Participants:** all specialist reviewers in scope.
- **Rule:** reviewers do not read each other's findings.
- **Activities:** each reviewer examines its area and writes `findings/<ROLE>.json`, including strengths.
- **Outputs:** one findings file per reviewer.
- **Exit:** all assigned areas reviewed.

### P3 — Verification
- **Goal:** Separate real problems from assumptions and preferences.
- **Lead:** Evidence Verifier. **Participants:** Evidence Verifier and only the cross-verifiers assigned findings by VER. The Scribe is not dispatched for routine verification.
- **Activities:** reproduce defects; inspect cited code; confirm screenshots/flows; reclassify misjudged types or severities; mark duplicates.
- **Outputs:** `verification-log.json` with verdict per finding: `verified` · `partially-verified` · `unverified` · `reclassified` · `duplicate`.
- **Exit:** every finding has a verdict. Unverified findings cannot be accepted.

### P4 — Debate
- **Goal:** Resolve conflicts between findings and recommendations.
- **Lead:** Chair. **Participants:** involved dispute parties and the Chair; Red Team is conditional on material risk or unresolved strategic disagreement. Scribe is not dispatched for routine debate recording.
- **Activities:** form disputes; run rounds per §2.4.
- **Outputs:** `debates/DBT-*/` with positions, rebuttals, challenge, decision.
- **Exit:** every dispute has a decision.

### P5 — Decision
- **Goal:** Turn verified findings and debate outcomes into a roadmap.
- **Lead:** Chair. **Participants:** only specialists whose domains are materially affected by accepted decisions; Evidence Verifier provides one consolidated sign-off. Competitive Analyst and Red Team are conditional; Scribe is not dispatched for routine ticket generation.
- **Activities:** consolidate duplicates; decide each finding's state (§2.5); group accepted items into workstreams; prioritize; define dependencies and acceptance criteria; Verifier confirms every accepted item rests on verified evidence.
- **Outputs:** `decision-log.json`, prioritized roadmap, draft Implementation Planning Pack, canonical `TASK-NNN` ticket records and generated backlog index.
- **Exit:** every verified finding has a decision; roadmap prioritized.

### P6 — Readiness Gate
- **Goal:** Make sure the plan is safe and realistic before handoff.
- **Lead:** Chair. **Participants:** assessors whose domains intersect actual workstreams; UX/Visual/Explainability/PM specialists are conditional on unresolved domain-specific readiness questions; Red Team is conditional on material risk; Scribe performs one final pack-assembly pass.
- **Activities:** assess each roadmap item for implementation risk, effort, cost, operational impact, dependencies and regression risk; run a pre-mortem; finalize sequencing; finalize the Implementation Planning Pack.
- **Outputs:** `readiness-gate.json`, final Implementation Planning Pack, ticket plan-readiness / owner-approval states, final Review Report.
- **Exit:** **Review complete.** Report and pack handed to the product owner.

### P7 — Re-review (after implementation)
- **Goal:** Confirm changes solved the original problems without new ones.
- **Lead:** Chair. **Participants:** original finding authors mapped to externally changed decisions, plus the Evidence Verifier. Other specialists are conditional on a concrete changed-area question; Scribe is not dispatched unless a distinct report/pack correction is needed.
- **Activities:** check each implemented item against its original findings and acceptance criteria; look for regressions; record new findings.
- **Outputs:** re-review results per item (`resolved` · `partially-resolved` · `not-resolved` · `regressed`), updated report.

---

## 3.1 Specialist Coordination and Efficiency

The authoritative dispatch triggers live in `specialist-dispatch-matrix.md`. The Chair must dispatch only relevant active specialists, record skips with reasons, and bundle compatible assignments into one invocation per role per phase (except the distinct P3 Verifier passes and P4 debate rounds). Independent P2 reviews remain isolated. Context is supplied through the dispatch packet's profiles; agents must not load every brief file by default. Deterministic scripts handle mechanical validation and rendering. Token counts are recorded only when actual platform usage is available; never estimate them.

## 4. Committee Roles

Role codes are used in finding IDs and file names.

### 1. Committee Chair / Product Director — `CHR`
**Mission:** Own the product vision, the review process and the quality bar; ensure the review ends in clear decisions.

**Responsibilities**
- Create and maintain the product brief; map the review scope.
- Decide which specialists participate in each phase; dispatch and orchestrate rounds; manage dependencies between agents.
- Enforce independence in P2 and no self-verification in P3.
- Consolidate duplicate findings; identify contradictions; form disputes.
- Facilitate debates, challenge weak arguments, and decide disputes with written rationale and recorded dissent.
- Distinguish verified problems, reasonable recommendations, subjective preferences and strategic decisions.
- Never dismiss a valid finding because it conflicts with the original implementation.
- Resolve ambiguity autonomously using the brief and log the assumption.
- Enforce debate caps and tie-break rules; track every decision state.
- Approve the final roadmap and declare the review complete.
- Convert accepted decisions into a dependency-aware set of self-contained planning tickets for future implementation; validate coverage and traceability without creating a separate agent.
- Keep committee acceptance distinct from owner approval of the ticket plan. Neither is implementation authorisation.

**Owns:** product brief, review orchestration, quality standards, consolidated findings, decision log, final roadmap, ticket decomposition and ticket backlog integrity.
**Phases:** P0–P7 (orchestrator). Runs in the main Claude Code session via the `review-committee` skill, not as a subagent.
**Must not:** decide without rationale; accept unverified findings; leave a dispute open.

---

### Specialist roster

Each specialist's responsibilities, out-of-scope items, per-phase duties and outputs live in its agent file. Phase participation is governed by `specialist-dispatch-matrix.md` (authoritative).

| Code | Role | Agent file | Mission |
|---|---|---|---|
| `PMV` | PM — User Value | `.claude/agents/review-pm-value.md` | Represent the people who will use the product. |
| `PMS` | PM — Scope & Simplicity | `.claude/agents/review-pm-scope.md` | Protect the product from bloat and unjustified complexity. |
| `CMP` | Competitive Analyst | `.claude/agents/review-competitive.md` | Ground "impressive" in real market evidence. |
| `ARC` | Principal Architect | `.claude/agents/review-architect.md` | Ensure the product rests on sound, maintainable architecture. |
| `FE` | Frontend Engineer | `.claude/agents/review-frontend.md` | Review frontend implementation at senior engineering standard. |
| `BE` | Backend Engineer | `.claude/agents/review-backend.md` | Ensure backend services are predictable, reliable and maintainable. |
| `AI` | AI Systems Engineer | `.claude/agents/review-ai-systems.md` | Make the product's LLM/AI integration (any provider) robust, predictable and explainable. Phase-level skip when the product has no AI layer. |
| `MED` | Media & Processing Pipeline Engineer | `.claude/agents/review-media-pipeline.md` | Ensure generated or processed media and multi-stage outputs are technically correct. Applies when the product renders/transforms media or runs processing pipelines; otherwise a phase-level skip. *(Subjective or creative quality is out of scope — reviewed by the product owner.)* |
| `VIS` | Visual Design Critic | `.claude/agents/review-visual-design.md` | Be the visual quality authority for the product's interface. |
| `UX` | UX / Interaction Designer | `.claude/agents/review-ux.md` | Make every workflow intuitive and efficient. |
| `XAI` | AI Explainability & Control Designer | `.claude/agents/review-explainability.md` | Make the product feel like an intelligent creative tool, not an unpredictable AI. |
| `DOC` | UX Writer & Documentation Reviewer | `.claude/agents/review-ux-writer.md` | Make every word in the product and docs clear and accurate. |
| `QA` | QA, Reliability & Security Engineer | `.claude/agents/review-qa-security.md` | Ensure correctness, reliability and security. |
| `CPE` | Cost & Performance Engineer | `.claude/agents/review-cost-performance.md` | Make the product efficient in money and compute. |
| `RED` | Red Team / Contrarian | `.claude/agents/review-red-team.md` | Prevent groupthink and expose overlooked risks. |
| `VER` | Evidence Verifier | `.claude/agents/review-verifier.md` | Ensure only real, evidenced problems drive decisions. |
| `SCR` | Committee Scribe & Reporter | `.claude/agents/review-scribe.md` | Assemble accurate, traceable planning documents. The HTML report is generated deterministically from canonical records. |

---

## 5. Ownership Boundaries

| Topic | Defines / Decides | Implements / Verifies |
|---|---|---|
| Accessibility | UX (requirements), VIS (contrast) | FE (implementation) |
| Performance | CPE (system budgets, cost model) | FE, BE, MED, AI (domain findings) |
| Prompt injection | AI (defence) | QA (testing) |
| Overengineering | ARC (technical decision) | PMS (flags from user/maintenance view) |
| Documentation | DOC (clarity) | ARC / engineers (accuracy) |
| Observability | BE (logging, job tracking) | AI (AI-specific observability) |
| Build / CI / setup | ARC | DOC (setup docs clarity) |
| AI reasoning data | AI (produces it) | XAI (surfaces it in UX) |
| Licensing / disclosure | QA | CHR (decision if trade-off) |
| Final decisions | CHR | VER (evidence sign-off) |

---

## 6. Review Report (HTML) Specification

**File:** `.review/report/index.html`; one self-contained offline-capable HTML file rebuilt after every phase from canonical `.review/` records.

**Audience and goal:** help the product owner understand the product and its user workflows first, then its current features, committee findings, proposed behaviour changes, debates, decisions and plan. This is a product-understanding and decision-making report, not a chronological diary of P0–P7.

### 7.1 Reader structure
1. **Product overview:** what the product is, intended users, problem/value, and evidence-backed use cases.
2. **User journeys:** concise end-to-end flows: user goal → action → product response → outcome. Clearly label documented versus observed flows; never invent personas or journeys.
3. **Current features:** grouped major capabilities, purpose, implementation status, current behaviour, entry point and evidence.
4. **Findings and proposed changes:** problem/current behaviour, impact, where found, evidence, proposed behaviour, rationale, linked decision and disposition. Keep current and proposed behaviour visibly separate.
5. **Debates:** concise dialogue-style presentation of real agent positions, key evidence/turning point, resolution, exact decision and dissent. Full arguments remain expandable. Never invent quotes or dialogue; use faithful paraphrases of recorded positions.
6. **Decisions and plan:** dispositions, rationale, trade-offs, epics/workstreams, planning tickets, dependencies, readiness and owner approval. Clarify that approval is for the plan only, not implementation.
7. **Evidence library:** searchable findings, verification details, source references, glossary and planning-document links.

### 7.2 Data sources and token efficiency
- P0 creates `.review/brief/product-context.json`: product description and grouped feature inventory. P1 may make a small evidence-backed update to user profiles and core use cases from first-run observation. Every item includes evidence and a documented/observed basis.
- Findings, verification, disputes/positions, decisions, roadmap, gate and tickets are rendered directly from their canonical records. Do not create duplicate narrative summaries of those records.
- The report builder is deterministic. The Chair runs it after each phase gate; do not dispatch SCR just to rewrite a report. No phase chapters are required.

### 7.3 Presentation rules
- Plain language first; show concise summaries and keep technical evidence/full debate reasoning expandable.
- Each finding identifies the responsible agent, source location, evidence, and verification status.
- Never present a recommendation as accepted unless the decision record says so. Distinguish finding, recommendation and decision.
- Use actual screenshots captured during review only.
- Missing or invalid product context must be shown as incomplete; never silently invent missing content.
- Self-contained, responsive, accessible, calm editorial design; no external dependencies.

## 7. Implementation Planning Pack

**Location:** `.review/implementation/`. Drafted in P5, finalized in P6. This is a ticket-first planning artifact, not an implementation workspace.

| Location | Purpose | Owner role(s) |
|---|---|---|
| `START-HERE.md` | Entry point and reading order | Generated by `build-pack-views.py --phase P6` (Chair runs it; no agent) |
| `PLAN/roadmap.md` | Generated workstream outcomes, milestones, sequencing rationale, dependencies and P6 readiness | CHR (canonical JSON); generated by `build-pack-views.py`, run by SCR |
| `PLAN/migration-strategy.md` | Optional system-level migration strategy when it adds context beyond roadmap and ticket dependencies | ARC |
| `PLAN/workstreams/WS-NN-*.md` | Optional cross-ticket workstream brief for genuinely complex coordination; never required for every WS | Owning specialist |
| `tickets/TASK-NNN.json` | Canonical, self-contained planning ticket for one independently plannable unit of future work | CHR, informed by specialists |
| `tickets/INDEX.md` | Generated ticket index and proposed dependency order; not a second source of truth | Generated by `build-pack-views.py`, run by SCR; content owned by CHR |
| `DECISIONS/decision-log.md` | Generated human-readable view of the canonical decision log | CHR (canonical JSON); generated by `build-pack-views.py`, run by SCR |
| `DECISIONS/adr/ADR-NNN-*.md` | Accepted architectural decision records | ARC |
| `REFERENCES/architecture.md` | Current/target architecture, boundaries, contracts and diagrams | ARC |
| `REFERENCES/ai-system.md` | Prompt architecture, context, structured outputs, validation and evals | AI, when applicable |
| `REFERENCES/media-pipeline.md` | Pipeline stages, determinism, export and regression fixtures | MED, when applicable |
| `REFERENCES/design-system.md` | Tokens, typography, components and visual direction | VIS, when applicable |
| `REFERENCES/ux-flows.md` | User journeys, states, accessibility and explainability | UX, XAI, when applicable |
| `REFERENCES/terminology-and-copy.md` | Glossary, microcopy and documentation language | DOC, when applicable |
| `REFERENCES/test-strategy.md` | Test strategy, regression scenarios and security tests | QA |
| `REFERENCES/cost-performance.md` | Cost model, budgets, targets and trade-offs | CPE |
| `REFERENCES/risk-register.md` | Pre-mortem, risks and mitigations | RED, CHR |

**Ownership split:** the Chair owns canonical tickets, ticket IDs, decomposition and roadmap decisions; specialists own the content of their domain `REFERENCES/*`; `START-HERE.md` and the other views are generated by script and run by the Chair; the Scribe is not dispatched by default. Generated views are never edited by hand: fix the canonical JSON or its owner, then regenerate.

The roadmap owns workstream/milestone-level planning. Ticket JSON owns individual task scope, dependencies, proposed steps, acceptance criteria and verification plans. The generated ticket index is the only human-readable backlog. Specialist references explain shared technical context and must not duplicate ticket instructions. Omit irrelevant references rather than creating empty files.

---
