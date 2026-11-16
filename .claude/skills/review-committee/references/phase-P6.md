# P6 — Readiness Gate

**Goal:** make sure the plan is safe and realistic; finalize the planning pack for owner handoff. The review is **complete** at the end of P6.

## Steps
1. Read `specialist-dispatch-matrix.md`. Dispatch assessors only for domains touched by actual workstreams. Each role receives one bundled assignment covering all its relevant workstreams and writes `.review/gate/<ROLE>.json` (gate schema). Default assessor pool when relevant: ARC, BE, AI, MED, QA, CPE, PMS. DOC reviews pack clarity only when substantive planning documents exist. UX/VIS/XAI/PMV are conditional when a material unresolved readiness question remains in their domain. Record every skipped role and reason.
2. **RED (conditional):** run a pre-mortem only for high-risk, cross-cutting, or strategically consequential roadmap items → `.review/implementation/REFERENCES/risk-register.md`. Reuse existing P5 risk analysis when no material risk question remains; do not dispatch RED just to rewrite it.
3. **Merge** assessments into `.review/gate/readiness-gate.json`: one item per workstream with verdict `Go` / `Go with conditions` / `Hold`, conditions, combined risk. Adjust roadmap sequencing if needed (record changes as decision amendments).
4. **Chair checks ticket quality and readiness** against merged workstream verdicts and conditions. Re-run `ticket-check.py`; every ticket proposed for owner handoff must have `quality_review.verdict=PASS`, all nine checks true, and no open quality issues. After recording P6 readiness, re-evaluate `quality_review.checks.status_and_gate_alignment`, update the Chair review timestamp, and retain `PASS` only if the new planning status, verdict, conditions, blockers, owner approval, and dependencies agree. Tickets for Go / Go-with-conditions workstreams become `AWAITING_OWNER_APPROVAL` only when all non-owner planning conditions and task dependencies are satisfied; Hold workstreams remain `BLOCKED` or `DEFERRED`. Record workstream verdict, conditions, satisfied/open conditions, assessor roles, and assessment date on each ticket. A ticket with open conditions or unmet task dependency remains `BLOCKED`; only tickets with all non-owner conditions satisfied may become `AWAITING_OWNER_APPROVAL`. Never set `APPROVED` during an autonomous review; explicit owner approval after the review is required to approve the ticket as part of the plan. This approval is not implementation authorisation. Run `build-pack-views.py --phase P6` to regenerate generated views, then rerun both ticket and trace checks.
5. **Chair finalises the pack with scripts, no agent:** run `build-pack-views.py --phase P6` (generates `START-HERE.md`, `DECISIONS/decision-log.md`, `PLAN/roadmap.md`, `tickets/INDEX.md`), then `trace-check.py` (the consistency pass). Do not dispatch SCR unless a trace-check failure needs a judgement-based content correction; record that as an assignment.
6. Fix trace-check failures deterministically where possible; re-dispatch the owning role at most once only when a judgement or content correction is required.

## Gate
- `readiness-gate.json` validates; every workstream has a verdict.
- `python3 .claude/skills/implementation-pack/scripts/ticket-check.py` passes.
- `python3 .claude/skills/implementation-pack/scripts/trace-check.py` passes.
- Every conditional P6 role is either dispatched or has a recorded skip reason.

## Close
Standard close: run `python3 .claude/skills/report-builder/scripts/build-report.py`; run `state.py dispatch-metrics`; then `state.py advance`.
Final message to the user (≤6 lines): review complete, where the report is (`.review/report/index.html`), where the pack and ticket backlog are (`.review/implementation/`), count of tickets awaiting plan approval, headline outcome, and strategic decisions flagged for attention.

**Scope boundary:** P6 finalises the review, roadmap, and ticket plan only. It does not dispatch coding agents, implement changes, run implementation tasks, or track delivery progress.
