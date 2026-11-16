# P0 — Intake

**Goal:** understand the product, its stack and existing context; set up the review.

## Steps
0. Read `.claude/skills/codebase-atlas/SKILL.md`.
1. If `.review/state.json` does not exist: `python3 .claude/skills/review-committee/scripts/state.py init`.
2. **Dispatch `review-architect`** (P0 intake packet):
   - TASK: "P0 intake: collect existing repo context, detect the stack, map the repo, run setup/build once."
   - Uses the `stack-detection` skill.
   - OUTPUT: `.review/brief/existing-context.md`, `.review/brief/stack-profile.md`, `.review/brief/stack-profile.json`, `.review/codebase-atlas/` (built and validated by stack-detection). `repo-map.md` is generated from the Atlas by script (`atlas.py repo-map`), not written by ARC.
3. Read those four files (they are the foundation — reading them in full is justified).
4. **Validate the SCIS Codebase Atlas:** ARC builds it through stack-detection. Run `python3 .claude/skills/codebase-atlas/scripts/atlas.py status` and `verify`; if missing/stale, run `build` or `refresh --changed`. Inspect manifest parser notes and coverage. Enrich product features/workflows and verified relationships only from direct evidence. Atlas gaps never block P0.
5. **Check browser tooling:** are `mcp__playwright__*` tools available in this session? Record the answer.
6. **Write `.review/brief/product-brief.md`** from `references/templates/product-brief.md`, grounded in existing-context and code. Cite paths.
7. Create `.review/brief/product-context.json` for the HTML report: concise product description, evidenced user profiles, 3–8 real use cases as user journeys, and a grouped inventory of major current features. Use only documented or observed facts; use Atlas as navigation, verify important claims directly in source, mark intended versus observed basis, and cite source paths/screens. Do not invent personas, features, or workflows. Start from `references/templates/product-context.example.json`. Validate with `python3 .claude/skills/review-standards/scripts/validate.py product-context .review/brief/product-context.json`.
8. **Create the first report** by running `python3 .claude/skills/report-builder/scripts/build-report.py` (no Scribe narrative invocation).
9. Run `python3 .claude/skills/review-committee/scripts/state.py depth` to set the review depth (lite for small repos).
9b. **Write `.review/brief/review-scope.md`** from `references/templates/review-scope.md`:
   - Keep all 17 specialist agents installed, callable and active. Do not merge, deactivate or remove any role. Assign each its full existing scope and record applicability; the specialist-dispatch matrix controls phase-specific invocation only. An absent surface may justify a phase-specific non-dispatch, never removal of the agent.
   - Assign every product area to a primary reviewer.
   - Pick a small fixed set of sample projects for renders and AI generation (2–3) and set the budget.
   - Plan the P2 batches.
   - Set the active-role inventory to all 17 specialists plus CHR: `state.py roles CHR,PMV,PMS,CMP,ARC,FE,BE,AI,MED,VIS,UX,XAI,DOC,QA,CPE,RED,VER,SCR`. The dispatch matrix determines which roles are called in each phase; P0 non-dispatches are logged as phase-level skips, not deactivation. Never skip because of Atlas limitations or token/resource savings.
10. **Dispatch `review-pm-scope`** (P0): review the brief's MVP boundary; OUTPUT `.review/brief/complexity-budget.md`.
11. Update the brief if PMS identified a scope fact you missed (log the change at the bottom of the brief).

## Gate
- `existing-context.md`, `stack-profile.md`, `stack-profile.json`, `repo-map.md`, `product-brief.md`, `review-scope.md`, `complexity-budget.md` and `product-context.json` exist; product-context validates.
- `.review/codebase-atlas/atlas.json`, `manifest.json` and `evidence/source-index.json` exist; `atlas.py verify` passes or parser limitations are explicitly recorded.
- All 17 specialist agents plus CHR remain active/callable; the existing dispatch matrix remains authoritative for phase-specific calls.
- `stack-profile.json` has `forbidden_commands` that block the full test suite (verify by reading it).
- Every area in review-scope has a primary reviewer.

## Close
Standard phase close: run `build-report.py`; run `state.py dispatch-metrics`; then `state.py advance`. The report is generated from product-context and canonical review records, not a phase narrative.
