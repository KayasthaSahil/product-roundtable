# P2 — Independent Review

**Goal:** deep, independent review of every in-scope area. Reviewers never see each other's findings.

## Steps
0. Shared factual Atlas records may be used by all assigned reviewers. Atlas contains no specialist opinions. Every dispatched specialist must still perform the full independent review, inspect source directly, trace relevant paths, and investigate beyond Atlas as needed. Never reduce scope/depth because of Atlas. P2 reviewers must not read other roles' findings.
1. Read `review-scope.md` and `specialist-dispatch-matrix.md`, and `state.json` `depth`: when `lite`, dispatch only the core set defined in the matrix's depth rule and skip the rest with the stated reason. Dispatch only active primary reviewers assigned a real area. For any role with no substantive assignment because its domain is absent or irrelevant in this phase, record a matrix-grounded phase-level non-dispatch reason. Do not deactivate or merge the role.
2. Start the dev server for UI work and keep it available for roles that need it; record URL and run-log entry.
3. Preserve these dependency-aware batches, filtering each by active assignments:
   - **Batch A — core engineering (parallel):** ARC, FE, BE, AI, MED. MED performs sample pipeline/render runs once, only if the product has a processing or render pipeline (budget from review-scope); AI performs sample AI generations once. Skip roles whose corresponding product area does not exist.
   - **Batch B — quality, cost, scope, docs (parallel):** QA, CPE, PMS, DOC. Run after A so QA/CPE can reuse run-log outputs; shared measurements are not findings, so independence holds. QA reviews the test suite statically and diagnoses its slowness.
   - **Batch C — design & experience (parallel):** VIS, UX, XAI, PMV. Dispatch VIS/UX only where a UI/interaction surface exists; XAI only where AI transparency/control exists.
4. One invocation per role for the phase. Each packet states: "Independent review. Do not read `.review/findings/*` other than your own file." Include only the role's assigned scope and source references.
5. Validate every dispatched findings file with `--check-refs`; re-dispatch once on failure and log it as a retry.
6. `index.py --counts` to confirm coverage: every area in review-scope has findings or an explicit "reviewed, nothing significant" strength/summary.

## Gate
- Every active assigned reviewer has a findings file that validates, or an explicit documented matrix-based phase non-dispatch exists.
- Every area covered.

## Close
Stop the dev server. Standard close: run `python3 .claude/skills/report-builder/scripts/build-report.py`; run `state.py dispatch-metrics`; then `state.py advance`.
