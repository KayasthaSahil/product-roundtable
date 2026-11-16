---
name: verification-protocol
description: P3 verification procedure for the product review committee — integrity checks for hallucinated references, direct verification, cross-verifier assignment (never the author), verdict consolidation, P5 sign-off and P7 resolution checks. Load as the Evidence Verifier or when assigned findings to cross-verify.
---

# Verification Protocol

**Principle:** only real, evidenced problems drive decisions. No finding is verified by its author.

## Verdicts
`verified` · `partially-verified` · `unverified` · `reclassified` (verified, but severity/category changed — give the new values and reason) · `duplicate` (give `duplicate_of`). Definitions: see "Verdict definitions" below.

## A. Verifier — planning pass (P3 step 1)
The Chair has already run `scripts/auto-verify.py`: Low/Opportunity and excerpt-matched Medium findings are verified in `by-AUTO.json`. Work only from `.review/verification/auto-queue.json`; the steps below apply to those IDs.
1. Index: `python3 .claude/skills/review-committee/scripts/index.py` (all findings).
2. **Integrity checks on every queued finding** (see "Integrity checks" below): run
   `python3 .claude/skills/review-standards/scripts/validate.py findings .review/findings/<ROLE>.json --check-refs` for each file, then open cited code and confirm the excerpt/claim matches. A fabricated reference → `unverified` with note "reference does not exist / does not match".
3. **Verify directly**: every Critical and High finding, and every finding whose evidence is code or commands you can check by reading. Use targeted runs only if essential (budget: hook-enforced 5 per cycle, ≤5 min).
4. **Assign the rest** to cross-verifiers from an adjacent area — never the author. Suggested pairings: FE↔UX/VIS, BE↔ARC/QA, AI↔BE/XAI, MED↔CPE/FE, VIS↔UX, UX↔XAI/PMV, XAI↔UX/AI, DOC↔UX, QA↔BE, CPE↔MED/AI, PMV↔PMS, PMS↔PMV, CMP↔PMV, ARC↔BE.
5. Write `.review/verification/verification-log.json` with your verdicts so far, and `.review/verification/assignments.json`:
   `{"assignments": {"UX": ["FND-VIS-003", ...], ...}}`

## B. Cross-verifier (P3 step 2)
For each assigned ID: read the finding (`index.py --show <ID>`), reproduce or inspect the evidence, decide a verdict, record `method` (what you did) and your own evidence. Write `.review/verification/by-<ROLE>.json` (`{"verdicts": [...]}`, verification schema). You may not change the finding itself.

## C. Verifier — consolidation (P3 step 3)
Merge all `by-*.json` into `verification-log.json`. Where a cross-verdict looks weak or conflicts with your integrity check, re-check directly and decide. Apply reclassifications (severity reflects actual impact). Mark duplicates (keep the best-evidenced one as primary). Validate with `--check-refs`.

## D. P5 sign-off
For every `Accepted` / `Accepted with modifications` decision, confirm all linked findings are `verified`/`partially-verified`/`reclassified`, and that the acceptance criteria are observable. Write `.review/verification/p5-signoff.json`: `{"clean": true|false, "flags": [{"decision": "DEC-007", "issue": "..."}]}`.

## E. P7 resolution check
For every `resolved` claim in `.review/rereview/*.json`, confirm fresh evidence shows the acceptance criteria are met. Downgrade unsupported claims. Write `.review/rereview/verification.json` (`{"confirmations": [{"finding_id", "confirmed": bool, "notes"}]}`).

## Rules
- Unverified ≠ wrong. It means not shown. Say what evidence would settle it.
- Severity reclassification needs a written reason grounded in actual impact.
- Never run the full test suite. Prefer reading code over running it.

## Integrity checks (run on every finding)

1. **Paths exist** — every `code` evidence ref resolves to a real file (`validate.py --check-refs`).
2. **Lines exist** — cited line ranges are within the file length.
3. **Content matches** — open the file at the cited lines; the excerpt or described behaviour is actually there (not a similar function elsewhere, not an older version).
4. **Symbols exist** — functions, components, routes, env vars, config keys named in the finding exist (`Grep`).
5. **Behaviour claims** — runtime claims ("X re-renders on every keystroke", "the job is retried forever") are backed by observation (command output, screenshot, profiler, log) or clearly labelled as inference with `confidence` ≤ medium.
6. **Screenshots exist** — referenced evidence files exist under `.review/evidence/`.
7. **Market claims** — CMP claims have a dated source.
8. **Stack fit** — the recommendation uses idioms of the stack in `stack-profile.md` (no foreign framework advice).

Any failure on 1–4 → `unverified` (note the failure). Failure on 5–8 → `partially-verified` or `unverified` by judgment.

## Verdict definitions

| Verdict | Meaning | Required |
|---|---|---|
| verified | Evidence checked; the problem exists as described | method + your evidence |
| partially-verified | Part of the claim holds; part is unproven or overstated | notes stating which part holds |
| unverified | Evidence missing, wrong, or could not be reproduced | notes: what was tried, what evidence would settle it |
| reclassified | Problem exists, but severity or category is wrong | `reclassified.severity/category/reason` |
| duplicate | Same root cause as another finding | `duplicate_of` (the better-evidenced finding) |

Strengths are not verified unless the Chair asks; they are spot-checked for fabricated references only.
