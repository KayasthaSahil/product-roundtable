# P7 — Re-review (after external implementation)

**Goal:** independently assess externally implemented changes against the original findings and acceptance criteria. P7 is review-only: the committee may inspect diffs, run permitted targeted verification, and create follow-up findings/tickets, but must not fix, modify, or implement anything.

## Steps
1. `state.py rereview` first (opens P7, new cycle, records HEAD): the state transition precedes all other P7 work.
2. Read `.claude/skills/codebase-atlas/SKILL.md`; refresh the Atlas for the new snapshot with `python3 .claude/skills/codebase-atlas/scripts/atlas.py refresh --changed` (or `build --force` if schema/cache/freshness is uncertain), then run `verify`. Atlas refresh is not re-review evidence; source diff and direct verification remain mandatory.
3. `git diff --stat <base_commit>..HEAD` → changed areas. Map changed areas to roadmap workstreams and their decisions/findings.
4. **Dispatch `review-architect`**: re-run stack detection if manifests changed (`stack-profile` refresh only; existing-context unchanged unless docs changed).
5. For each implemented decision, identify the roles that **raised** its findings. Dispatch only those authors whose findings map to changed decisions; bundle all mapped findings per role into one invocation. Include only their finding IDs, acceptance criteria and changed-path diff summary. Each writes `.review/rereview/<ROLE>.json` (schema `rereview`) and records any regressions as new findings (`"phase": "P7"`) in its findings file.
   - Run only the tests linked to changed items (targeted budget applies). A full run only if the suite has been made fast by the implementation.
   - Start the dev server once if UI items are involved.
6. **Dispatch `review-verifier` once**: confirm every `resolved` claim with fresh evidence; downgrade unsupported ones → `.review/rereview/verification.json`.
7. Decide on new regression findings (decision-log, as in P5) and add follow-up planning tickets only when the Chair makes an explicit planning decision. Never fix the regression within the committee. Skip unrelated roles and record why.

## Gate
- Every implemented item has an outcome confirmed by the Verifier.

## Close
Standard close: run `python3 .claude/skills/report-builder/scripts/build-report.py`; run `state.py dispatch-metrics`; then `state.py advance`.
