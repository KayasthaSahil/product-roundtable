---
name: review-standards
description: Binding review rules for every Product Review Committee agent — finding format, severity, categories, evidence, debate conduct, decisions, execution limits. Load before doing any committee work.
---

# Committee Review Standards (condensed)

Full text: `references/review-standards.md`. This summary is binding; read the full file when a rule is unclear.

## Objective
Transform the product into a distinctive, polished, reliable, maintainable, production-quality product of its kind, judged against its own promise and users. Not the longest list of criticisms. Subjective or creative quality of generated content is judged only by the product owner; you review the system that produces it and its technical correctness, never creative taste.

## Before reviewing
1. Read `.review/brief/existing-context.md`, `stack-profile.md`, `product-brief.md`, `repo-map.md`, `review-scope.md` (whichever exist).
2. Judge code by the idioms of the stack actually in use and the project's own conventions. Documented intent informs you; **the code is the truth**. Report doc/code gaps.

## Findings
- One file per role: `.review/findings/<ROLE>.json` (schema: `schemas/findings-file.schema.json`). Append across phases; never edit other roles' files.
- Every finding: id `FND-<ROLE>-<NNN>`, title (the problem, not the fix), category, severity, location, evidence, problem, impact, recommendation, confidence.
- **Tiered detail (saves output tokens; depth of investigation is unchanged):**
  - **Critical / High — full form:** also repro steps (or code/command evidence), current behaviour where distinct, root cause, assumptions, and a recommendation with `what`, `why`, `expected_outcome`, `verification`.
  - **Medium — standard form:** recommendation with `what` + `verification` (observable acceptance criterion). `why` / `expected_outcome` / `root_cause` optional.
  - **Low / Opportunity — short form:** recommendation `what` only; group minor polish into one finding per area. Keep `problem` and `impact` to one or two plain sentences.
  - Include a short code excerpt in `evidence[].detail` for every `code` reference — the scripted P3 check matches it against the source.
- **Evidence** = file:line + short excerpt, command + real output, screenshot/recording path, rendered frame, reproducible steps, or a dated cited source. "Best practice says…" alone is not evidence.
- **Cite only what exists**, exactly. A fabricated or approximate reference invalidates the finding.
- Report **root causes**; list symptoms inside one finding.
- Record **strengths** (`kind: "strength"`) — a review without strengths is incomplete. Max 3 per role per phase, one line each, with a reference.
- No minimum count. Group minor Low polish into one finding per area.
- Stay in your area; outside it, note briefly with `handoff_to`.

### Severity (actual impact, not feeling; severity ≠ priority)
`Critical` security / data loss / fundamental failure / release blocker · `High` major defect, broken core workflow, significant architectural risk · `Medium` meaningful usability/maintainability/reliability/performance improvement · `Low` minor polish · `Opportunity` strategic enhancement. Critical and High require repro steps or direct code evidence.

### Category (exactly one; split cross-cutting issues and link via `related`)
`Bug / Defect` · `Architectural Problem` · `UX / Usability Problem` · `Visual Design Problem` · `Performance / Cost Problem` · `Security / Reliability Risk` · `Missing Capability` · `Redundancy / Complexity` · `Documentation Problem` · `Product Strategy Opportunity`

### Confidence
`high` observed/reproduced · `medium` strong evidence, partly inferred · `low` plausible, needs verification. Never present low confidence as confirmed.

### Recommendations must be actionable
State **what** changes (files/components/flows/contracts), **why** (tied to evidence), **expected outcome**, and **verification** (observable acceptance criteria). Offer alternatives with trade-offs where meaningful. Prefer the simplest change that solves the root cause; "industry standard" alone is no justification. Forbidden: "improve architecture", "make UI cleaner", "optimize performance".

## Atlas (specialists)
- Read `.review/codebase-atlas/digest/<ROLE>.md` if it exists; do not read the Atlas SKILL (Chair/Architect only). Digest/Atlas records are leads, never proof or a source boundary.
- Do your full role investigation: open source, trace paths, gather your own evidence. Never cite Atlas as sole evidence. Never write opinions into the Atlas.
- Missing/stale/incomplete Atlas never blocks you: inspect source directly and note the limitation.
- Atlas factual error → `.review/codebase-atlas/discrepancies/<ROLE>-<NNN>.json` from `.claude/skills/codebase-atlas/templates/discrepancy.json` with exact source evidence; keep reviewing.
- P2: never read other roles' findings. Shared factual Atlas access is allowed.

## Conduct
- Independence: in P2 never read other roles' findings.
- Never verify your own findings.
- Direct, respectful, no flattery, no dismissal of the original work.
- `problem` and `impact` written in plain language (they feed the owner's report).

## Debates
Present position + evidence; name assumptions/weaknesses in opposing views; explain trade-offs and alternatives; acknowledge valid counterpoints; revise when evidence justifies (that is a strength); record unresolved disagreement. Argue evidence and outcomes, never the agent. Goal: the best decision, not winning.

## Decisions (Chair)
For every Accepted / Accepted-with-modifications decision, record whether implementation is required and link `TASK-NNN` tickets or provide a no-ticket rationale. Committee acceptance is not owner approval of the plan. Owner approval of a ticket is planning approval only; implementation is outside this committee and skill. Dispositions: `Accepted` · `Accepted with modifications` · `Rejected` · `Deferred` · `Requires experiment` · `Requires additional evidence` · `Merged`. Each has rationale, owner role, dependencies, linked findings, dissent. Nothing is ever deleted.

## Execution discipline — HARD LIMITS
- **Never run the full test suite** (it can take hours). Review tests statically; reuse existing CI/test artifacts.
- Targeted test (single file/case) only when it is the only way to verify a specific finding: timeout ≤ 5 min (Bash `timeout` ≤ 300000), max 5 per review cycle committee-wide (hook-enforced).
- Check `.review/runs/run-log.json` before any long command; reuse outputs from the same commit. Log every command > 1 min or that costs money with `python3 .claude/skills/review-standards/scripts/runlog.py add ...`.
- Build/setup once (P0). Sample renders and sample AI generations once, shared. No exploratory generation loops.
- A command failing twice for the same reason → log a finding, do not retry.

## Safety
- Write only inside `.review/` (hook-enforced). No production code, config, asset or design changes.
- No destructive or git-mutating commands. Never print or copy secrets — cite the location, never the value.
- If something blocks you (hook, missing tool, app won't start): note it, lower confidence, continue another way.

## Validate before returning
`python3 .claude/skills/review-standards/scripts/validate.py <kind> <file>` — kinds: `findings`, `verification`, `position`, `dispute`, `decisions`, `roadmap`, `gate`, `rereview`, `product-context`, `ticket`. Specialists validate only the record types they own; they do not create or edit implementation tickets. The Chair validates canonical planning tickets in P5/P6 with `.claude/skills/implementation-pack/scripts/ticket-check.py`, including the recorded nine-point quality review. Fix every validation error before the relevant phase gate.

## Must not
- Modify anything outside `.review/`, or change dependencies, git state or data.
- Run the full test suite; targeted single tests only when essential, ≤5 min, within the committee budget.
- Read or print secrets (cite locations only).
- Report a defect without evidence, cite a file/line you have not opened, or present inference as fact.
- Judge subjective or creative quality of generated content (owner's domain).
- Ask the user questions: make a reasonable assumption, record it, continue.

## Return format (to the Chair, ≤10 lines)
```
STATUS:   complete | partial | blocked
WROTE:    <paths>
COUNTS:   Critical n · High n · Medium n · Low n · Opportunity n · Strengths n
TOP 3:    <ID — one line each>
HANDOFFS: <role codes + IDs>
BLOCKERS: <anything that limited the review>
```
