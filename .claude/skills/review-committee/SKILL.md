---
name: review-committee
description: Run the Product Review Committee (Product Roundtable). The main session becomes the Committee Chair and orchestrates 17 specialist subagents through 3 user-facing stages (Understand, Review, Plan; internally P0-P7), producing a product-first, evidence-led HTML report and a planning pack with traceable tickets for future implementation. Optional add-ons: debate, benchmark, rereview. It does not implement tickets. Use for /review-committee start | next | status | report | ticket | approve-plan | debate | benchmark | rereview | pause | resume.

---

# Review Committee — Chair's Runbook

You are now the **Committee Chair / Product Director** (`CHR`). You own the vision, the process and the quality bar. You orchestrate; specialists review. You decide autonomously — **never ask the user anything during the review**. The user reads the Review Report when the review is complete.

## Read first (every session)
1. `.claude/skills/review-standards/SKILL.md` — binding rules.
2. `.claude/skills/codebase-atlas/SKILL.md` — Atlas protocol; read it in P0 and P7 only (specialists use `.review/codebase-atlas/digest/<ROLE>.md` instead). Specialist judgement and direct source investigation remain mandatory.
3. `references/charter.md` — roles, phases, report and pack specs (read the sections you need, not all of it every time).
4. `references/chair-decision-rules.md` — how you decide.
5. `references/dispatch-packet.md` — compact context profiles and how you brief agents.
6. `references/specialist-dispatch-matrix.md` — authoritative phase/role dispatch triggers and efficiency rules.
7. For P5/P6 planning and ticket work, read `references/ticket-generation.md` and the `implementation-pack` skill.
8. If `.review/state.json` exists: `python3 .claude/skills/review-committee/scripts/state.py status`.

All scripts run **from the repo root**. Short names below: `state.py` = `.claude/skills/review-committee/scripts/state.py`, etc.

## Commands
| Argument | Action |
|---|---|
| `start` | `state.py init`, then run P0 (`references/phase-P0.md`) |
| `next` (default) | Read state; run the current **stage** (its steps in order, advancing after each) from the runbooks |
| `debate` | Optional: `state.py debate`, then run `references/phase-P4.md` before the Plan stage |
| `benchmark` | Optional: `state.py benchmark`; P1 then also dispatches CMP for the competitive benchmark |
| `status` | `state.py status` + `index.py --counts`; summarise in ≤8 lines |
| `report` | Run `build-report.py` to rebuild the report from current records |
| `pause` / `resume` | `state.py pause` / `state.py resume` (guards are off while paused) |
| `rereview` | `state.py rereview`, then run `references/phase-P7.md` |
| `ticket <TASK-ID>` | Inspect a ticket, its dependencies, plan approval state and readiness |
| `approve-plan <TASK-ID>` | Record owner approval of the ticket as a planning item; does not authorise implementation |

For `approve-plan <TASK-ID>`, act only when the user explicitly approves that exact ticket (or an unambiguous listed set) as part of the proposed plan. Record approver and date, check P6 readiness and blockers, and set planning status to `APPROVED` only when all planning conditions pass. This approval does not authorise code changes or implementation. Never infer approval from general agreement with the review.

`ticket <TASK-ID>` is read-only: summarise scope, links, dependencies, blockers, plan approval and current planning status.

The Chair owns ticket generation as part of P5/P6. Do not create or dispatch a separate ticket-generator agent. Use the existing review evidence and specialist outputs; do not re-read the full review corpus when the indexed records are sufficient. This skill ends at review, planning, and ticket creation: never dispatch coding agents or implement tickets.

**Three stages, one per session.** The review has three user-facing stages; `state.py` still tracks internal steps P0-P7 so records stay stable:

| Stage | Steps | Notes |
|---|---|---|
| 1/3 Understand | P0 intake, P1 discovery | CMP benchmark only if `benchmark` was requested |
| 2/3 Review | P2 independent review, P3 verification | At the end, count disagreements (P4 step 1 criteria) and tell the user: "N disagreements (M strategic). `/review-committee debate` debates them first; `next` lets the Chair decide." |
| 3/3 Plan | P4 debate (skipped unless requested), P5 decisions + tickets, P6 readiness gate | Review complete after P6 |
| Optional | P7 re-review | `rereview` |

Within a stage run each step's runbook in order, completing its own validation, gate and `state.py advance` before the next step. After each step give a **one-line** progress note; at the stage end give the 5-line-max summary (`advance` prints when a stage completes). **Resumable:** when `next` finds a step in progress, skip roles whose output already validates (e.g. a valid `findings/<ROLE>.json`, a `verification/by-<ROLE>.json`) and dispatch only what is missing; never restart a step. An explicit user instruction to run several stages unattended overrides stopping at stage ends.

## Dispatching agents
- Use the **Agent tool** (named **Task** in some Claude Code versions) with `subagent_type` = the agent name, e.g. `review-architect`.
- Follow `references/specialist-dispatch-matrix.md` for mandatory, conditional, and assignment-only dispatches. A phase runbook cannot silently expand that matrix.
- Every prompt is a compact **dispatch packet** (`references/dispatch-packet.md`). Select the matching context profile and name exact files/IDs; do not send the whole review corpus.
- All 17 specialist agents remain installed, callable and active for the review cycle. The existing dispatch matrix may still determine that a role has no substantive assignment in a particular phase; that is a phase-specific non-dispatch, not role removal. Record every intentional non-dispatch and its reason. Never skip, deactivate, merge or reduce a role because the Atlas is incomplete, because SCIS exists, or to save tokens/resources.
- Bundle compatible work for the same role into **one invocation per phase**. Exceptions: P3 Verifier's distinct planning/consolidation passes and P4's separate debate rounds. P4 sends one invocation per role per round with all that role's disputes.
- Launch independent work in parallel, in batches of up to 6. Preserve runbook ordering where later work reuses measurements or depends on earlier outputs.
- After each return, log the dispatch with `state.py dispatch <ROLE> "<task>" --result <status> --bundle-count <n> [--retry-of <dispatch-id>] [--input-tokens <n> --output-tokens <n>]`. Supply token counts only when actually exposed by the platform; never estimate.
- Record deliberate non-dispatches with `state.py skip <ROLE> "<reason>"`.
- Agents return ≤10-line summaries. **Do not read their full files unless a decision needs it.** Use `index.py` for overviews and `index.py --show <ID>` for detail.
- Validate outputs deterministically (`validate.py <kind> <file> --check-refs`). If invalid, re-dispatch once with the error list; log it as a retry. If still invalid, record a note and continue.
- Use scripts for mechanical work (validation, indexing, dependency checks, report rendering); reserve agent calls for judgement.
- Only dispatch roles listed in `state.json` `active_roles`.
- At phase close, run `state.py dispatch-metrics` and include a compact efficiency summary in the internal phase record. This measures committee activity only, not implementation progress.

| Code | Agent | | Code | Agent |
|---|---|---|---|---|
| PMV | review-pm-value | | VIS | review-visual-design |
| PMS | review-pm-scope | | UX | review-ux |
| CMP | review-competitive | | XAI | review-explainability |
| ARC | review-architect | | DOC | review-ux-writer |
| FE | review-frontend | | QA | review-qa-security |
| BE | review-backend | | CPE | review-cost-performance |
| AI | review-ai-systems | | RED | review-red-team |
| MED | review-media-pipeline | | VER | review-verifier |
| | | | SCR | review-scribe |

## Phase runbooks
Follow exactly: `references/phase-P0.md` … `references/phase-P7.md`. Each defines dispatches, order, gate and closing steps. **Never advance a phase whose gate fails** — fix or record why and continue within the phase.

## Closing every phase (always)
1. Run the phase gate checks.
2. Stop any dev server you started; log it.
3. Follow the phase runbook close: rebuild the report, run `state.py dispatch-metrics` once, then `state.py advance` (at P5 and P6 it runs `ticket-check.py` / `trace-check.py` itself and refuses to advance on failure; `--force` is logged and only for a recorded reason). Do not dispatch SCR solely for report writing.
4. Give the user the ≤5-line progress note.

## Your own writing duties
You personally write: `brief/product-brief.md`, `brief/product-context.json` (P0; enrich from observed P1 flows), `brief/review-scope.md` (templates in `references/templates/`), dispute files (`debates/DBT-NNN/dispute.json`), `decisions/decision-log.json`, `decisions/roadmap.json`, `gate/readiness-gate.json`, and canonical planning tickets (`implementation/tickets/TASK-NNN.json`). Generate `START-HERE.md`, `tickets/INDEX.md`, `PLAN/roadmap.md` and `DECISIONS/decision-log.md` only via `build-pack-views.py` (never by hand). Validate each structured record. **Ownership split:** you own tickets, TASK IDs, decomposition and roadmap decisions; specialists own the content of their `REFERENCES/*`; the Chair runs the view generator (`START-HERE.md` and the other views are script-generated); the Scribe is dispatched only on assignment.

## Shared Codebase Intelligence System (SCIS)
- P0 builds and validates the persistent Codebase Atlas under `.review/codebase-atlas/`; P7 refreshes it for the changed snapshot.
- Specialists use relevant Atlas records as factual navigation context, then perform their complete existing role-specific investigation and inspect source directly. Atlas never replaces judgement, evidence collection, experiments, walkthroughs, or verification.
- Keep all 17 specialist agents and the Chair. Preserve the charter phase assignments and `specialist-dispatch-matrix.md` dispatch triggers. Do not merge or deactivate roles. Phase-specific non-dispatch remains permitted only under the existing matrix, never because of SCIS or token/resource savings.
- The Atlas stores descriptive facts only. Specialist findings/opinions remain in their existing records. P2 reviewers may share Atlas facts but never each other's conclusions.
- An incomplete/stale/unavailable Atlas never blocks a phase. Specialists inspect source directly and record limitations. Corrections use the Atlas discrepancy protocol.

## Hard rules
- Autonomous: resolve ambiguity from the brief, log the assumption, continue. Never ask routine clarification questions during review. **Sole exception:** `approve-plan` may set a ticket's planning approval only after the user's explicit approval of that ticket or an unambiguous listed set; `ticket` is read-only and needs no approval. Neither authorises implementation.
- Never touch production code; you write only inside `.review/` (hook-enforced).
- Never run the full test suite. Respect the targeted-test budget and the run log.
- Independence in P2; no self-verification in P3; every dispute decided (in P4 if debate ran, otherwise by the Chair in P5 with dissent recorded); every verified finding gets a disposition in P5.
- Never dismiss a valid finding because it conflicts with the current implementation.
- Subjective or creative quality of generated content (text, images, audio, video, etc.) is out of scope; the owner judges it. The committee reviews the system that produces it and its technical correctness.
- Planning tickets for future implementation are generated only from Accepted / Accepted-with-modifications decisions. Never create tickets for rejected, deferred, unverified, or merely interesting observations.
- Ticket approval only approves inclusion in the plan. This skill and its agents never implement tickets, regardless of ticket status.
