---
name: report-builder
description: Build the self-contained, decision-making HTML report from P0 product context and canonical review records. Run after each phase; do not author phase narratives.
---

# Report Builder

The report explains the product, its actual user workflows and features, what the committee found, what should change, why, and how decisions were reached. It is **product-first, evidence-led, and data-driven**.

## Generation

Run from the repository root:

```bash
python3 .claude/skills/report-builder/scripts/build-report.py
```

The script reads `.review/brief/product-context.json`, findings, verification, debates and positions, decisions, roadmap, tickets, gate records, and planning files. It generates `.review/report/index.html`. Never hand-edit the HTML or template.

## Data ownership and token discipline

- Capture product overview and grouped feature inventory in P0; enrich user profiles and journeys in P1 only when new evidence appears in `.review/brief/product-context.json`; validate it with the `product-context` schema.
- Reuse canonical findings, evidence, debate positions, decisions, and ticket records. Do not ask the Scribe to rewrite them as prose.
- After each phase, rebuild the report directly with the script. No chapter, recap, takeaway, or cast narrative is required.
- Do not reread the full review corpus to build the report. The script performs the aggregation.

## Reader experience

1. **Product:** what it is, intended users, supported use cases and end-to-end journeys. Distinguish documented/observed facts from assumptions.
2. **Current features:** grouped capabilities, purpose, current behaviour, entry point, and source evidence. Show implementation status accurately.
3. **Findings and proposed changes:** for each finding show the problem/current behaviour, impact, where it was found, evidence, proposed behaviour, linked decision and disposition. Do not imply an unapproved recommendation is accepted.
4. **Debates:** short conversational presentation using actual position headlines/arguments. Show the key disagreement, evidence/turning point, resolution, decision and dissent. Full arguments remain expandable. Never invent dialogue or quotations; concise paraphrase is allowed only when faithful to recorded positions.
5. **Decisions and plan:** dispositions, rationale, trade-offs, epics/workstreams, planning tickets, dependencies and readiness/owner-approval state. Make clear that ticket approval is planning approval, not implementation authorisation.
6. **Evidence library:** searchable findings, source references, verification details, glossary and links to planning documents.

## Writing and display rules

- Plain language first; technical detail is expandable.
- Default view: headline plus 1–2 concise sentences per item. Keep evidence available; do not omit it to achieve brevity.
- Every claim must be grounded in a canonical record or cited product-context source. Clearly label inference and uncertainty.
- Current behaviour and proposed behaviour must be separate fields/blocks. Never present proposed behaviour as existing functionality.
- Use actual product screenshots only when captured by the review; do not generate illustrative screenshots.
- If product-context or a required source is missing/invalid, show an explicit incomplete-data state; never silently invent or claim a complete report.

## Phase close

The Chair runs the report builder after the phase gate. The Scribe is not dispatched solely to rewrite the report. The Scribe remains available for P6 planning-pack assembly and consistency checks.
