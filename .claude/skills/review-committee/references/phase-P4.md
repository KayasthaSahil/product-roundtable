# P4 — Debate

**Goal:** resolve conflicts between findings and recommendations with structured debate.

## Steps
1. **Identify disputes** using `index.py` (verified and partially-verified only). A dispute exists when:
   - Two or more findings recommend **incompatible** changes to the same area.
   - PMV proposes adding capability that PMS argues to cut or defer.
   - A reclassification by VER is contested by the author (author noted it in their file amendments).
   - An Architect/engineer proposal conflicts with simplicity, cost, or UX/explainability needs.
   - A High/Critical recommendation has two viable approaches with real trade-offs.
   Do **not** create disputes for findings everyone would accept — those go straight to P5.
2. For each dispute: `next-id.py DBT`, create `.review/debates/DBT-NNN/dispute.json` (schema `dispute`) with question, context, findings, parties (2–4 roles), `"status": "open"`. Validate.
3. **Round 1:** dispatch each involved role **once** with all its disputes (parallel across roles). Use one compact `DEBATE` packet per role. Each writes `.review/debates/DBT-NNN/<ROLE>-r1.json` (schema `position`), using the `debate-protocol` skill.
4. **Round 2:** dispatch again only for roles with a substantive response to make; each role receives only the opposing r1 files for its assigned disputes and writes `<ROLE>-r2.json` (rebuttal, acknowledgements, revision).
5. **Round 3** only for disputes where an r2 introduced new evidence.
6. **Red Team (conditional):** dispatch `review-red-team` only for strategic/high-impact, security-sensitive, materially contested, or unresolved disputes. Bundle those disputes into one invocation; it may write `RED-challenge.json` per dispute (at most one reconsideration request each). Record skipped routine disputes and why no Red Team challenge was needed.
7. **Decide each dispute** (`references/chair-decision-rules.md`): add a decision to `.review/decisions/decision-log.json` (`next-id.py DEC`), link `disputes`, record dissent. Update dispute.json: `"status": "decided"`, `"decision": "DEC-NNN"`, a one-line `setup` (what was at stake) and `turning_point` (the evidence or argument that decided it).
8. Validate decision-log and every dispute.

## Gate
- Every dispute has `"status": "decided"` and a decision.

## Close
Standard close: run `python3 .claude/skills/report-builder/scripts/build-report.py`; run `state.py dispatch-metrics`; then `state.py advance`.
