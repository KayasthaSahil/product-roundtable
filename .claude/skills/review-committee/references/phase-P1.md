# P1 — Discovery

**Goal:** first impressions as a new user, target-user profiles, competitive context.

## Steps
1. **Start the app once** if runnable (command from `stack-profile.md`), using Bash with `run_in_background: true`. Record the URL: `state.py set dev_server_url <url>`. Log it in the run log (`kind server`). If it fails twice: record the failure, continue — UI roles review from code with lowered confidence.
2. Read `specialist-dispatch-matrix.md`. Dispatch:
   - `review-pm-value` — mandatory: first-time use/value discovery; write `.review/brief/user-profiles.md` and first-impression findings.
   - `review-competitive` — **only if `state.json` has `benchmark: true`** (user ran `/review-committee benchmark`): competitive benchmark `.review/brief/competitive-benchmark.md` (+ Opportunity findings). Otherwise record `state.py skip CMP "benchmark not requested"`.
   - `review-visual-design` — only if a user-facing visual interface exists and can be inspected.
   - `review-ux` — only if meaningful user journeys or interaction flows exist.
   Bundle any additional discovery questions for a role into the same invocation. Skip irrelevant roles and record why.
3. Validate each output.
4. Chair updates `.review/brief/product-context.json` only with material user profiles/use cases confirmed by PMV/UX or observed in the app; retain evidence and basis labels. Do not re-summarise the whole product. Revalidate the file.

## Gate
- `user-profiles.md` exists (and `competitive-benchmark.md` when `benchmark` is on); dispatched findings files and updated `product-context.json` validate. Every conditional P1 role is either dispatched or has a recorded skip reason.

## Close
Stop the dev server. Standard close: run `python3 .claude/skills/report-builder/scripts/build-report.py`; run `state.py dispatch-metrics`; then `state.py advance`.
