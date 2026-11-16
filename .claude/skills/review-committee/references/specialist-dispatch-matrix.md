# Specialist Dispatch Matrix

This is the authoritative dispatch policy for the Review Committee. Phase runbooks may add task details, but must not silently broaden this matrix. The Chair records each dispatched or intentionally skipped role in `.review/state.json`.

## Dispatch rules

- All 17 specialist agents remain installed, callable and active for the review cycle. The active-role set is an inventory of available committee capabilities, not a requirement to invoke every role in every phase. Existing phase-specific dispatch/skip triggers below remain authoritative.
- Never deactivate, merge, or phase-skip a specialist because the Atlas exists/is incomplete, to reduce token consumption, or to lower the number of agents. The only exception is the user-directed **depth rule** below (small repositories). A phase-specific skip is valid only when the matrix trigger is not met or there is no substantive assignment; record the concrete scope reason.

- Dispatch only active roles whose responsibility is materially relevant to the current phase and review scope.
- `Mandatory` means dispatch when the phase runs and the role is active; `Conditional` means dispatch only when its trigger is met; `On assignment` means dispatch only when the Chair/Verifier assigns concrete work.
- `CHR` is the main-session Chair, not a subagent dispatch. `VER`, `SCR`, and `RED` may be active for the cycle without being dispatched in every phase.
- Never dispatch an agent merely to populate a template. If there is no substantive work, record a skip reason.
- Combine all compatible assignments for the same role into one invocation per phase. The explicit exceptions are P3 Verifier's planning and consolidation passes, and P4's separate debate rounds.
- Parallelise independent work. Preserve required ordering where later roles reuse measurements or depend on earlier outputs.
- Do not dispatch coding agents. The committee's work ends at review, decisions, and planning.

## Phase matrix

| Phase | Role | Dispatch | Trigger / assignment |
|---|---|---|---|
| P0 | ARC | Mandatory | Repository intake, stack detection, repo map and setup/build inspection. |
| P0 | PMS | Mandatory | Review MVP boundary and complexity budget after the initial brief. |
| P0 | Other specialists | Skip | Activate roles for later phases; do not dispatch them during intake without a specific intake question. |
| P1 | PMV | Mandatory | First-time user/value discovery and evidence-based user profiles. |
| P1 | CMP | Optional | Competitive benchmark and opportunity scan; dispatch only when the user requested it (`benchmark`). This is a user-selected add-on, not a token-motivated skip. |
| P1 | VIS | Conditional | Product has a user-facing visual interface that is running and inspectable in a browser. If the app or browser is unavailable, skip with reason "app not runnable: covered by P2 code review". |
| P1 | UX | Conditional | Meaningful user journeys exist and the app is running and usable in a browser. If not, skip with reason "app not runnable: covered by P2 code review". |
| P1 | Other specialists | Skip | No P1 assignment unless a material discovery question is documented. |
| P2 | PMV, PMS, ARC, FE, BE, AI, MED, VIS, UX, XAI, DOC, QA, CPE | On assignment | Dispatch each active primary reviewer whose assigned area exists in `review-scope.md`; include only the assigned area. Record a phase-level non-dispatch for absent/irrelevant areas; do not merge specialist roles. CMP is not a P2 reviewer; RED/VER/SCR participate only under their phase-specific rules. |
| P3 | VER | Mandatory, two passes | Planning/integrity assignment pass, then consolidation pass. These are distinct responsibilities, not duplicate retries. |
| P3 | Cross-verifiers | On assignment | Only when more than 12 queued findings remain after VER's direct checks, and only roles receiving at least 3 IDs; never the finding author. Smaller queues are verified directly by VER. Group all assigned IDs per role into one invocation. |
| P4 | Dispute parties | Optional step | The whole P4 step runs only when the user requested `debate`. Then: only roles named in an open dispute, bundled once per round. |
| P4 | RED | Conditional | Dispatch for strategic/high-impact, security-sensitive, materially contested, or unresolved disputes. Do not dispatch for routine disagreements already resolved by evidence. |
| P5 | PMV | Conditional | Accepted decisions materially change user requirements, user journeys, or success criteria. |
| P5 | PMS | Conditional | Accepted decisions materially expand scope, add complexity, introduce configuration burden, or require MVP trade-offs. |
| P5 | ARC | Conditional | Accepted decisions require architecture guidance, an ADR, or architectural reference updates. |
| P5 | AI | Conditional | Accepted decisions materially affect AI behaviour, orchestration, prompts, models, evaluation, or explainability data. |
| P5 | XAI | Conditional | Accepted decisions materially affect user control, transparency, explanations, or AI-related UX flows. |
| P5 | DOC | Conditional | Accepted decisions change terminology, user-facing language, documentation, or copy standards. |
| P5 | CPE | Conditional | Accepted decisions materially affect cost, latency, resource usage, or operational limits. |
| P5 | MED | Conditional | Accepted decisions materially affect media/render/export architecture or pipeline behaviour. |
| P5 | VIS | Conditional | Accepted decisions materially change design direction, visual tokens, or component patterns. |
| P5 | UX | Conditional | Accepted decisions materially change user journeys, interaction states, or accessibility requirements. |
| P5 | QA | Conditional | Accepted decisions materially change test strategy, security posture, reliability, or quality gates. |
| P5 | CMP | Conditional | Accepted roadmap materially changes product differentiation or positioning; otherwise reuse P1 benchmark and Chair analysis. |
| P5 | RED | Conditional | Challenge strategic, high-risk, irreversible, or cross-cutting decisions; not every routine decision. |
| P5 | VER | Mandatory | One consolidated sign-off over all accepted decisions and their verified evidence. |
| P6 | ARC, BE, AI, MED, QA, CPE, PMS | Conditional | Each assesses only workstreams touching its domain. Bundle all relevant workstreams into one invocation per role. |
| P6 | DOC | Conditional | Review pack clarity only when the generated pack contains substantive documents; no empty-template review. |
| P6 | UX / VIS / XAI / PMV | Conditional | Assess only if a readiness question in their domain remains unresolved after P5; otherwise skip with reason. |
| P6 | RED | Conditional | Run pre-mortem for high-risk, cross-cutting, or strategically consequential roadmap items. |
| P6 | SCR | On assignment | Not dispatched by default: the Chair generates the pack views with `build-pack-views.py` and checks consistency with `trace-check.py`. Dispatch only to fix a trace-check failure that needs judgement. This is removal of a no-longer-needed writing task, not a token-motivated skip. |
| P7 | ARC | Conditional | Only if changed manifests, architecture boundaries, or stack assumptions require refresh. |
| P7 | Original finding authors | On assignment | Dispatch only authors whose findings map to externally implemented decisions; bundle all mapped findings per role. |
| P7 | VER | Mandatory | Independently verify every claimed resolved/partially-resolved item and regression disposition. |
| P7 | Other specialists | Skip | Dispatch only if a concrete changed-area question cannot be answered by the original authors or VER. |

## Depth rule (P2, user-directed proportionality)

`state.json` `depth` is set at the end of P0 (`state.py depth`): `lite` when the repo has at most 5000 lines of source code (from the Atlas), otherwise `full`; the user may override with `state.py depth full`. In `lite`, P2 dispatches the **core set**: ARC, QA, PMV, plus by surface in `stack-profile.json`: UX and FE (ui), BE (server/api), AI (ai_layer), XAI (ai_layer and ui), MED (render_pipeline). PMS, CPE, DOC and VIS are not dispatched in P2 (PMS still runs in P0 and conditionally in P5); record `state.py skip <ROLE> "lite depth: small repo, no separate assignment"`. All roles stay installed and active. Tell the user at the end of Stage 2 that `depth full` re-runs them.

## Existing batch constraints

- P2 remains independent. Reviewers must not read other reviewers' findings. Use the P2 batches in `phase-P2.md` to respect measurement reuse and environment dependencies; skip only matrix-inapplicable roles, with a concrete phase-level reason.
- P3 cross-verification runs only after VER has assigned IDs. VER's planning and consolidation calls are intentionally separate.
- P4 runs one invocation per involved role per round, containing all that role's dispute assignments. Round 3 is only for genuinely new evidence. RED follows the conditional trigger above.
- P5/P6 document drafting and assessment are grouped by role. Do not split one role's work into multiple calls merely because it touches multiple documents/workstreams.

## Model-selection policy

Keep the `model:` assignments in each `.claude/agents/review-*.md` file as the baseline. They are already divided by reasoning demand:

- Higher-reasoning assignments: ARC, BE, AI, QA, RED, VER (`opus`).
- Pattern-heavy, product, UX, visual, documentation and planning assignments (`sonnet`).

Do not change models solely to save tokens. Use deterministic scripts for schema validation, reference checks, indexing, dependency checks, report rendering, and other mechanical work. The Chair may narrow an assignment or request a targeted follow-up when uncertainty remains; do not downgrade independent verification or security/architecture judgement for cost reasons. Record any deliberate model override and its reason if the platform permits it.

## Dispatch efficiency record

For every phase, record:

- dispatched role, task, phase, result, and whether it was a retry;
- skipped role and concise reason;
- number of assignments/findings/disputes/workstreams bundled into the invocation;
- input/output token counts only when the platform exposes actual usage.

Never estimate token counts. Use `unknown`/omit when unavailable. Review metrics are for evaluating committee efficiency only; they are not implementation-progress tracking.
