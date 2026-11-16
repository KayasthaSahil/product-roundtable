# P5 — Decision

**Goal:** every verified finding gets a disposition; accepted work becomes a prioritized roadmap and a draft planning pack for future implementation.

## Steps
1. `index.py --undecided` → every verified / partially-verified finding without a decision.
2. **Decide all of them** (chair-decision-rules). Merge duplicates (`Merged`). Group closely related findings under one decision. Write acceptance criteria for every Accepted item (from findings' verification fields, sharpened). Mark strategic ones.
3. **Roadmap:** group Accepted / Accepted-with-modifications decisions into workstreams in `.review/decisions/roadmap.json` (schema `roadmap`): owner role, horizon (Now/Next/Later), sequence, dependencies, effort, outcome. Set each decision's `workstream`.
4. **Dispatch planning references by relevance**, following `specialist-dispatch-matrix.md`. Do not dispatch every specialist by default. Bundle all relevant reference work for each role into one invocation:
   - PMV only for material user-requirement/journey changes → append a short `## Requirements changes (P5)` section to `.review/brief/product-brief.md`; no separate requirements file.
   - ARC only for architectural decisions → `REFERENCES/architecture.md`, accepted ADRs, and optional migration strategy only when distinct from ticket sequencing.
   - AI only for material AI-system changes → `REFERENCES/ai-system.md`.
   - XAI only for material AI-control/transparency changes → relevant sections of `REFERENCES/ux-flows.md`.
   - DOC only for terminology/copy/documentation changes → `REFERENCES/terminology-and-copy.md`.
   - CPE only for cost/performance/operational changes → `REFERENCES/cost-performance.md`.
   - MED, VIS, UX, QA only when accepted decisions materially affect their domain; create a reference only when a ticket will link it (`trace-check.py` warns on unlinked references).
   - Workstream owners may create `PLAN/workstreams/WS-NN-*.md` only for complex cross-ticket coordination that cannot be expressed clearly in tickets and the dependency map.
   Record each conditional role skipped and why.
5. **CMP (conditional):** dispatch only if accepted roadmap decisions materially change product differentiation/positioning. Otherwise reuse the P1 benchmark and record the skip.
6. **RED (conditional):** challenge strategic, high-risk, irreversible, or cross-cutting decisions. Do not dispatch for routine decisions; record skipped rationale.
7. **VER (mandatory, one consolidated invocation):** sign off that every Accepted item rests on verified evidence → `.review/verification/p5-signoff.json`. Fix any decision it flags.
8. **Chair generates and quality-reviews planning tickets for future implementation** using `references/ticket-generation.md` after all P5 decisions and verifier sign-off are final. Decompose every Accepted / Accepted-with-modifications decision into canonical `.review/implementation/tickets/TASK-NNN.json` planning records. For each accepted decision, record `implementation_required`; if false, record `no_ticket_reason`. Complete all nine `quality_review.checks` per ticket. A passing ticket remains `DRAFT` with `quality_review.verdict=PASS`; tickets needing correction become `REVIEW_REQUIRED` with actionable issues; tickets blocked by missing prerequisites become `BLOCKED`. Run `ticket-check.py` and fix all errors. Then run `build-pack-views.py --phase P5` to generate `tickets/INDEX.md`, `PLAN/roadmap.md`, and `DECISIONS/decision-log.md` from canonical JSON sources. Do not hand-maintain generated views or dispatch a ticket-generator agent.

## Gate
- `index.py --undecided` returns 0 items. Roadmap validates. Verifier sign-off is clean (or every flag resolved).
- Every accepted decision explicitly states whether implementation is required; required work has one or more linked tickets, and non-implementation decisions have a reason. Generated indexes are not independently edited.
- Every ticket has a recorded Chair quality review; no ticket remains `NOT_REVIEWED`. Tickets pass schema, semantic traceability, source-grounding, status, and dependency checks. `REVIEW_REQUIRED` / `BLOCKED` tickets retain explicit issues and do not pass as ready. No ticket is implemented by the committee.
- Every matrix-conditional P5 role is either dispatched or has a skip reason.

## Close
Standard close: run `python3 .claude/skills/report-builder/scripts/build-report.py`; run `state.py dispatch-metrics`; then `state.py advance`.
