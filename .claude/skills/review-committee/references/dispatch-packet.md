# Dispatch Packet

Every Agent call the Chair makes uses this structure. Keep it compact, fill every field, and write `none` where empty. The Chair should send a task-specific packet, not repeat the whole review brief.

```
ROLE:             <code> (<agent name>)
PHASE / CYCLE:    <P0–P7> / <n>
TASK:             <one-sentence objective>
SCOPE:            <exact paths, modules, screens, flows, or workstreams>
CONTEXT PROFILE:  <INTAKE | DISCOVERY | REVIEW | VERIFY | DEBATE | PLAN | GATE | REREVIEW>
READ FIRST:       .claude/skills/review-standards/SKILL.md
                  .review/codebase-atlas/digest/<ROLE>.md (Atlas leads only; inspect source independently; do not read the Atlas SKILL)
                  this dispatch packet
COMMON CONTEXT:   <only relevant paths from .review/brief and relevant Atlas records; do not preload the full Atlas>
SPECIALIST INPUT: <exact phase/task records and IDs>
DO NOT READ:      <explicit exclusions, especially other P2 findings>
OUTPUT:           <exact output path(s)>
ID RANGE:         <range or n/a>
APP / BROWSER:    <URL and availability, or not running/unavailable>
BUDGET:           <targeted runs, sample renders/generations, and time constraints>
BUNDLE:           <count and IDs of grouped assignments>
VALIDATE:         <exact deterministic validator command, or none>
RETURN:           ≤10-line summary in standard return format
```

## Context profiles

Use the smallest profile that supports the assignment. The dispatch packet names exact files; agents must not load every brief file automatically.

| Profile | Include |
|---|---|
| `INTAKE` | Review standards, repo root conventions, relevant manifests/configs and existing project context discovered by ARC. Do not preload a product brief that does not exist yet. |
| `DISCOVERY` | Review standards, product brief, product-context summary, relevant user flows/screens, stack summary, and assigned discovery question. |
| `REVIEW` | Review standards, compact product brief, stack summary, repo-map excerpt for assigned area, review-scope assignment, and relevant source paths. P2 must not include other agents' findings. |
| `VERIFY` | Review standards, assigned finding records only, their cited evidence/source paths, and verification protocol. Add adjacent-area context only if needed to reproduce or judge the claim. |
| `DEBATE` | Review standards, dispute record, relevant findings and verification verdicts, then opposing positions only for round 2+. Do not load unrelated findings or disputes. |
| `PLAN` | Review standards, accepted decision IDs, linked verified findings, roadmap/workstream context, and only relevant architecture/product references. |
| `GATE` | Review standards, assigned workstream/ticket records, linked decisions, relevant references, and dependencies/conditions. |
| `REREVIEW` | Review standards, mapped original findings/decisions, acceptance criteria, changed-path diff summary, and relevant current source. |

## Rules

- Every agent reads the binding `review-standards` skill (which contains the Atlas protocol and Must-not rules) and this packet. The full Atlas SKILL is for the Chair/Architect in P0 and P7 only. Name `debate-protocol`, `verification-protocol` or `stack-playbooks` in READ FIRST only when the assignment needs them.
- The Chair includes only the common context actually needed. A compact context file may be generated or quoted from existing canonical records, but must preserve evidence references and must not introduce new claims.
- Agents may use relevant Atlas records to navigate the repository, but must open source directly, trace paths and gather their own evidence. Atlas is never sole evidence for a finding/verdict and does not restrict source access. If stale/incomplete, proceed from source.
- Agents may follow a cited reference when needed to resolve a specific question. They should not recursively read the entire documentation tree.
- P2 independence is absolute: do not read other roles' findings, even if the Chair accidentally includes a link. Ask the Chair for a corrected packet rather than opening them.
- Existing finding authors may read their own findings to append or continue them.
- Bundle compatible assignments for one role into one invocation per phase/round. Keep separate calls only where the runbook explicitly requires distinct passes or rounds.
- If the packet is missing a necessary input, report the precise missing item. Do not compensate by loading the entire review corpus.
- Token usage may be recorded only from actual platform-reported usage. Never estimate it.

## Phase-specific notes

- **P0:** `INTAKE`; ARC receives repo intake task. PMS receives product brief and scope only after ARC output exists.
- **P1:** `DISCOVERY`; PMV/CMP/VIS/UX receive only the discovery context relevant to their assignment.
- **P2:** `REVIEW`; use shared factual Atlas records only, never other agents' conclusions, and continue full independent source review; explicitly state: "Independent review. Do not read `.review/findings/*` other than your own file." Include only the role's assigned areas and source paths.
- **P3:** `VERIFY`; cross-verifiers receive assigned finding IDs and cited evidence only. VER planning and consolidation are separate passes.
- **P4:** `DEBATE`; bundle all disputes for that role in the round. Round ≥2 includes opposing round-1 positions for those disputes only.
- **P5:** `PLAN`; include only accepted decisions, their verified findings, and relevant workstream references.
- **P6:** `GATE`; include only assigned workstreams, tickets, dependencies, and relevant reference docs.
- **P7:** `REREVIEW`; include only mapped original findings, decisions, acceptance criteria and changed areas.

## Atlas discrepancy handoff
If the Atlas contains an incorrect, missing or stale factual record/edge, create `.review/codebase-atlas/discrepancies/<ROLE>-<NNN>.json` from `.claude/skills/codebase-atlas/templates/discrepancy.json`. Include exact source evidence and continue the review without waiting for correction. Do not write specialist opinions into Atlas.
