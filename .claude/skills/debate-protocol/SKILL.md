---
name: debate-protocol
description: How product review committee members take part in structured P4 debates (and P5/P6 challenges) — writing positions, rebuttals and Red Team challenges as JSON files in .review/debates/DBT-NNN/. Load when the Chair dispatches you to a dispute.
---

# Debate Protocol

The objective is the **best decision for the product**, not winning. Changing your position when evidence justifies it is a strength.

## Files
```
.review/debates/DBT-NNN/
├── dispute.json        # written by the Chair: question, context, findings, parties
├── <ROLE>-r1.json      # Round 1 position
├── <ROLE>-r2.json      # Round 2 rebuttal
├── <ROLE>-r3.json      # Round 3 (only if the Chair opens it)
└── RED-challenge.json  # Red Team challenge (optional)
```
Schema: `.claude/skills/review-standards/schemas/position.schema.json`. Template: see "Position file template" below.

## Round 1 — Position
1. Read `dispute.json` and the linked findings (`python3 .claude/skills/review-committee/scripts/index.py --show <ID>`), plus their verification verdicts.
2. Write your position: one-line `headline` (it appears in the owner's report — make it sharp and plain), `stance`, `argument`, `evidence` (same standards as findings), `tradeoffs`, `final_recommendation`.
3. Do **not** read other parties' r1 files in Round 1.

## Round 2 — Rebuttal
1. Read every other party's r1 file.
2. Write `<ROLE>-r2.json`:
   - `assumptions_challenged`: the specific assumptions or weaknesses in opposing arguments.
   - `acknowledges`: valid points from others — be honest; at least one if any exist.
   - `revised`: true if your position changed; explain in `argument`.
   - `final_recommendation`: your recommendation now.
3. New claims need evidence. No repetition of Round 1 — respond to what was actually said.

## Round 3 (rare)
Only when the Chair opens it because Round 2 introduced new evidence. Address only that evidence.

## Red Team challenge
`RED-challenge.json` (`round: "challenge"`): the strongest argument against the emerging consensus or the decision, what could go wrong after implementation, whether a simpler/safer option exists. Set `reconsideration_requested: true` only with new evidence or an unaddressed major risk. One per decision.

## Rebuttal rules

1. Argue about **evidence and outcomes**, never about the agent.
2. Name the exact assumption you challenge and why it fails — cite evidence.
3. Explain the trade-offs of **both** your option and the opposing one.
4. Offer alternatives when neither side's option is good.
5. Acknowledge valid counterpoints explicitly.
6. Revise when the evidence justifies it, and say so plainly.
7. If disagreement remains, state precisely what it rests on (a value judgment, missing evidence, or risk tolerance) so the Chair can decide.
8. Stay within your own area; defer to the area owner (charter §5) on their own domain unless you have contrary evidence.
9. Keep headlines short and plain — they are read by the product owner.
10. No padding: a short, decisive rebuttal beats a long one.

## Validate
`python3 .claude/skills/review-standards/scripts/validate.py position <file>` for every file you write.

## Position file template (`<ROLE>-r<N>.json`)

```json
{
  "dispute_id": "DBT-003",
  "role": "ARC",
  "round": 1,
  "headline": "Split the render worker from the API now; it is the root of three reliability findings",
  "stance": "Support FND-ARC-004 approach A (separate worker process with a job table)",
  "argument": "Plain-language reasoning, tied to evidence. 3–8 sentences.",
  "evidence": [
    {"type": "code", "ref": "server/render.ts:40-88", "detail": "render runs inside the request handler; a timeout kills the job"},
    {"type": "command", "ref": ".review/runs/render-sample-1.log", "detail": "sample render took 212 s, longer than the 120 s proxy timeout"}
  ],
  "assumptions_challenged": [],
  "acknowledges": [],
  "tradeoffs": "Adds a process and a table; mitigated by reusing the existing DB.",
  "revised": false,
  "final_recommendation": "Approach A, incrementally: move render behind a job table first, worker process second."
}
```
