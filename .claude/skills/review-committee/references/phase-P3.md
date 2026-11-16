# P3 — Verification

**Goal:** separate real problems from assumptions and preferences. No finding is verified by its author.

## Steps
0. Atlas is a navigation aid only. Verifiers must reopen cited source and independently reproduce/confirm claims; an Atlas record alone is never sufficient verification evidence. Preserve the no-self-verification rule.
0b. **Tier-1 scripted verification (Chair, no agent):** run `python3 .claude/skills/verification-protocol/scripts/auto-verify.py`. Low/Opportunity findings and Medium findings whose cited code excerpts match the source get a scripted `verified` verdict in `by-AUTO.json`; every 5th such Medium, all Critical/High, strategy/market claims and anything failing a check go to `auto-queue.json`. Quality is preserved: nothing is skipped, the script only removes agent time from what it can fully check.
1. **Dispatch `review-verifier` (planning pass)** using `VERIFY` with `auto-queue.json` only (it must not re-verify `by-AUTO.json` items): integrity-check and directly verify every queued Critical/High finding and queued code-evidenced finding; write `.review/verification/assignments.json` assigning the remaining queued findings to adjacent-area cross-verifiers (never the author).
2. **Dispatch cross-verifiers in parallel**, only for roles with assignments. Bundle all assigned finding IDs per role into one invocation. Each gets only assigned finding records and cited evidence; OUTPUT `.review/verification/by-<ROLE>.json`. Start the dev server first if UI findings are assigned. Do not dispatch unassigned roles.
3. **Dispatch `review-verifier` (consolidation pass)** as a separate, intentional invocation: merge `by-AUTO.json` and all `by-<ROLE>.json` into `.review/verification/verification-log.json`, resolve conflicting verdicts, apply reclassifications, mark duplicates.
4. Validate: `validate.py verification .review/verification/verification-log.json --check-refs`.

## Gate
- Every finding (kind=finding) has a verdict. `index.py --verdict -` returns 0 items. Every assigned cross-verifier output validates or has a documented blocker.

## Close
Standard close: run `python3 .claude/skills/report-builder/scripts/build-report.py`; run `state.py dispatch-metrics`; then `state.py advance`.
