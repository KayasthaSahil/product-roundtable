# Ticket Generation — Committee Chair Capability

## Purpose and boundary
Translate accepted committee decisions into a clear, prioritised, dependency-aware implementation plan expressed as canonical tickets. This is a capability of the existing Committee Chair, not a separate agent.

**This committee and its skills stop at review, planning, and ticket creation. They do not implement tickets.** They must not modify product source code, configuration, assets, or runtime state; dispatch coding agents; execute implementation steps; update tickets with implementation progress; or claim that a planned change has been implemented or verified. Tickets describe work for a future, separately authorised implementation process.

The committee may inspect the repository and existing tests as part of product review, verify findings, and assess whether proposed tickets are grounded. That review activity is distinct from carrying out the planned changes.

## Authority and approval boundaries
- Generate tickets only for decisions with disposition `Accepted` or `Accepted with modifications`.
- Never generate implementation tickets for `Rejected`, `Deferred`, `Requires experiment`, `Requires additional evidence`, or `Merged` decisions. An experiment may be represented as a ticket only after the Chair records a separate accepted decision authorising that experiment.
- Committee acceptance means the recommendation is accepted into the proposed plan; it does not authorise code changes or execution.
- At P6, tickets that pass plan-readiness are marked `AWAITING_OWNER_APPROVAL`. Explicit owner approval changes the planning status to `APPROVED` only. It does not authorise this committee, these agents, or this skill to implement the ticket.
- Do not infer plan approval from silence or review completion.

## Generation method (low-context)
1. Read `decision-log.json`, `roadmap.json`, P5/P6 gate outputs, and any optional workstream briefs that exist. Use `index.py` for finding detail; do not reload every finding or agent report.
2. For each Accepted / Accepted-with-modifications decision, decide whether a future implementation ticket is required. Record `implementation_required` and either linked ticket IDs or a concise `no_ticket_reason` on the decision record.
3. Group closely related decisions only when they share one coherent outcome and can be planned and assessed together. Otherwise create separate tickets. One decision may produce multiple tickets; one ticket may address multiple decisions.
4. Split work into the smallest independently plannable units that remain meaningful. Avoid tickets that are merely a heading, research note, or vague instruction.
5. Assign stable IDs with `python3 .claude/skills/review-committee/scripts/next-id.py TASK <count>`. Never reuse IDs.
6. Create one `.review/implementation/tickets/TASK-NNN.json` per ticket using `.claude/skills/review-standards/schemas/ticket.schema.json` and `templates/ticket.json` as the contract.
7. Build the dependency graph from actual prerequisites. Do not serialize independent work just because its ID is later. Detect cycles and missing dependencies. Dependencies describe the proposed future implementation order; the committee does not track their execution or completion.
8. Complete the Chair-owned `quality_review` before the P5 gate. `PASS` → `DRAFT`; `REVISE` → `REVIEW_REQUIRED` with actionable issues; `BLOCKED` → `BLOCKED` with a concrete blocker. Keep readiness at `Hold` / unassessed until P6; do not imply a readiness verdict early.
9. Run `python3 .claude/skills/implementation-pack/scripts/build-pack-views.py --phase P5` to create / regenerate `tickets/INDEX.md`, `PLAN/roadmap.md`, and `DECISIONS/decision-log.md` from canonical JSON. Do not maintain a second, independently edited task list.
10. Run `python3 .claude/skills/implementation-pack/scripts/ticket-check.py`. Fix every error and rerun it. `NOT_REVIEWED` and `REVISE` tickets fail the gate; a ticket cannot pass P5 while its quality review is unresolved.
11. Run the ticket checker again after any correction to canonical records and regenerate pack views. These checks validate planning records; they do not execute or verify product implementation.

## Ticket quality bar
Every ticket must state:
- The problem and why it matters.
- Current behaviour, supported by review evidence; distinguish observed facts from assumptions or details a future implementer must confirm.
- Expected behaviour and the rationale for the change.
- In-scope and explicitly out-of-scope work.
- Ordered proposed implementation steps for a future implementer.
- Relevant source files / functions only when verified during review. Use `verified` only when the path was inspected and its existence confirmed. Unverified candidate locations must be labelled `candidate_to_verify`; never invent paths, line numbers, APIs, or function names.
- Dependencies, owner gates, and affected decisions/findings/workstreams.
- Test scenarios, planned checks, and observable acceptance criteria. These are requirements for future implementation and verification; the committee does not run them as part of ticket execution.
- Rollback or recovery considerations for the future change.
- Handoff requirements describing what evidence a future implementation/review process should provide (for example changed-file summary, test output, and deviations). Do not populate these with fictional results.

A ticket is not plan-ready if its scope is ambiguous, its dependency is unknown, its acceptance criteria are not testable, or a required product-owner decision is unresolved.

## Required ticket quality review (Chair-owned; no extra agent)
After drafting tickets in P5, the Chair performs one bounded quality pass per ticket. Do not dispatch another agent solely to rewrite or score tickets. Reuse the accepted decision, verified finding, and specialist evidence already in the review record.

Record the result in each ticket's `quality_review` object:
- `NOT_REVIEWED`: initial template state; must not pass the P5 gate.
- `PASS`: all nine checks are true, `issues` is empty, and `reviewed_by` / `reviewed_at` are populated.
- `REVISE`: at least one quality issue remains; set planning status to `REVIEW_REQUIRED` and list actionable corrections.
- `BLOCKED`: a missing decision, evidence source, or external prerequisite prevents a reliable plan; set status to `BLOCKED` and explain the blocker.

The nine checks are:
1. `traceability`: linked decision is Accepted / Accepted with modifications; every finding and decision exists; both sides link to the ticket; ticket workstream agrees with its decisions.
2. `behavior_clarity`: objective, current behaviour, expected behaviour, and rationale are distinct, concrete, and grounded. Current behaviour is not guessed; uncertainty is explicitly marked for future inspection.
3. `scope_decomposition`: in-scope and out-of-scope boundaries are explicit; the ticket is one coherent, independently plannable outcome. Reconsider `XL` tickets for splitting and record why they remain together if split would harm coherence.
4. `source_grounding`: verified paths were actually inspected and exist; candidate paths use `candidate_to_verify`; verified source-inspection items include evidence. Never invent symbols or line numbers.
5. `dependency_integrity`: only real prerequisites are listed; no self-dependency, missing references, duplicate edges, or cycles; independent tickets are not serialized unnecessarily.
6. `acceptance_criteria`: criteria are observable and testable, cover the promised outcome, and avoid vague assurances such as "works correctly" or "is improved".
7. `verification_plan`: test scenarios and required checks explain how a future implementer can demonstrate each important acceptance criterion; include failure/boundary cases where relevant. These are plans, not test results.
8. `rollback_and_handoff`: rollback/recovery is credible for code, data, configuration, and runtime effects, or explicitly explains why no special rollback is needed; handoff requirements request evidence without fabricating it.
9. `status_and_gate_alignment`: planning status, P6 verdict, conditions, blockers, owner approval, and dependencies agree. `APPROVED` means approval of plan inclusion only.

Use the deterministic checker for schema, strict input loading, references, status consistency, safe verified paths, duplicate IDs, and dependency cycles. The checker cannot judge product intent or ticket decomposition; the Chair must complete those judgement checks. If any check fails, do not promote the ticket: record `REVISE` or `BLOCKED` and fix the source ticket. Do not hide warnings by weakening the schema.

The ticket checker is fail-closed: missing or malformed decision, roadmap, finding, ticket, or schema inputs are errors, never empty defaults. P5 and P6 gates must run it after the canonical records and generated views are updated.

## Planning status lifecycle
`DRAFT` → `REVIEW_REQUIRED` → `AWAITING_OWNER_APPROVAL` → `APPROVED`.

Other planning states: `BLOCKED`, `DEFERRED`, `REJECTED`.
- `DRAFT`: ticket has passed the Chair's quality review but has not yet completed P6 readiness / owner handoff.
- `REVIEW_REQUIRED`: scope, evidence, decomposition, dependency, or acceptance criteria need clarification; `quality_review.verdict` is `REVISE` or `NOT_REVIEWED`.
- `AWAITING_OWNER_APPROVAL`: P6 says the ticket plan is Go / Go-with-conditions and all non-owner planning conditions are satisfied.
- `APPROVED`: the owner has approved this ticket as part of the plan. This is a planning decision only, not permission for this committee or skill to execute it.
- `BLOCKED`: a planning prerequisite or unresolved decision prevents the ticket from being considered ready; record the blocker. The quality review may be `BLOCKED` or `PASS` if the ticket itself is sound but a prerequisite remains open.
- `DEFERRED`: intentionally postponed; record a revisit trigger.
- `REJECTED`: owner or committee rejected the proposed ticket; retain the record and rationale.

Do not use implementation-progress statuses such as `IN_PROGRESS`, `IMPLEMENTATION_REVIEW`, `VERIFIED`, or `COMPLETED` in this ticket system. The committee does not own implementation tracking.

## Strictly out of scope
- No production-code, configuration, asset, database, or runtime modifications.
- No dispatching or orchestrating coding agents.
- No implementing ticket steps.
- No commits, branches, deployments, migrations, or implementation operations.
- No recording implementation commits, changed files, test outcomes, or completion states in tickets.
- No claiming that a ticket is complete because its plan has been approved.

## Token discipline
- Do not add a permanent ticket-generator agent.
- Do not dispatch another model solely to restate known findings as tickets.
- Reuse structured IDs, evidence references, decisions, and existing specialist outputs.
- Generate tickets once in P5; refine their plan/readiness fields in P6. After P6, the committee's ticket-generation responsibility ends unless the user explicitly starts a new review or asks for a planning revision.
- Use deterministic scripts for schema, reference, duplicate-ID, and dependency-cycle checks. Use model judgement only for decomposition and ambiguous planning decisions.
