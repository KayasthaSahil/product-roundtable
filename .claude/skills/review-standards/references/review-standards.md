# Committee-Wide Review Standards

> Binding rules for every committee agent, in every phase.
> Companion to `charter.md` (the Charter). Where the two differ, **this document wins** for review rules; the Charter wins for roles and phases.
> Every agent loads these standards before doing any work.

---

## 1. Committee Objective

The committee does not exist to produce the longest list of criticisms or features. Its purpose is to systematically transform the product into a distinctive, polished, reliable, maintainable, production-quality product of its kind, judged against what the product itself promises and who it is for.

Every part of the product is judged against a high bar:

- **Frontend:** looks and feels like a professionally designed commercial product.
- **Backend:** reflects sound architecture and disciplined engineering.
- **AI integration:** reliable, predictable, and appropriately controllable.
- **Processing/media pipeline (if any):** consistently produces technically correct output.
- **Generated content (if any):** quality of text, images, audio, video or other generated output is **judged solely by the product owner** unless the brief says otherwise. The committee reviews only the system that produces it and its technical correctness.
- **Overall experience:** intuitive, coherent, and thoughtfully designed.

**Ultimate benchmark:** not whether the product works or how many features it has, but whether it is genuinely impressive to use, technically excellent underneath, and delivers results its users would be proud of.

---

## 2. Evidence-Based Findings

### 2.1 Required fields

Every finding must include:

| Field | Requirement |
|---|---|
| `id` | `SUT-<ROLE>-<NNN>` (e.g. `SUT-BE-007`) |
| `title` | One line naming the problem, not the solution |
| `role` | Role code of the author |
| `category` | Exactly one category from §4 |
| `severity` | Exactly one level from §3 |
| `location` | File path + line range, component, function, workflow, or screen |
| `evidence` | Concrete proof (see §2.2) |
| `repro_steps` | Steps to reproduce, where applicable |
| `problem` | What is actually wrong and why it matters |
| `current_behavior` | What the user/system actually does today; distinguish observed behaviour from the problem interpretation where useful |
| `root_cause` | Underlying cause if known; `unknown` if not |
| `impact` | Effect on users, engineering, performance, reliability, cost, or product quality |
| `recommendation` | Actionable change (see §6) |
| `alternatives` | Other approaches with trade-offs, where meaningful |
| `confidence` | `high` · `medium` · `low` (see §5) |
| `assumptions` | Everything assumed but not verified |
| `effort` | `S` · `M` · `L` · `XL` (rough estimate) |
| `related` | IDs of related findings |
| `handoff_to` | Role codes that should also look at this, if outside the author's area |

### 2.2 What counts as evidence

Valid evidence:
- File path with line range, plus a short excerpt of the relevant code.
- A command with its actual output (from the run log, §10).
- A screenshot or screen recording of the UI state.
- A rendered frame or media analysis output (for pipeline findings).
- Reproducible steps that a different agent can follow and observe the same result.
- For market claims: a dated, cited source.

Not evidence:
- "Best practice says…" without showing how the issue affects the product.
- Assumptions about code the agent has not opened.
- Guesses about runtime behaviour that was never observed.

### 2.3 Integrity rules

- **No unverified defects.** Never report a confirmed defect without enough evidence. Label uncertain issues honestly (`confidence: low`, list the assumptions).
- **Cite only what exists.** Every file, function, line, and screen referenced must exist exactly as cited. Fabricated or approximate references invalidate the finding.
- **Report root causes, not symptoms.** When several symptoms share one cause, raise one finding for the cause and list the symptoms in it.
- **Findings are append-only.** After verification a finding is never deleted. Corrections are recorded as amendments with a reason.

---

## 3. Severity Classification

| Level | Definition |
|---|---|
| **Critical** | Security vulnerability, data loss, fundamental product failure, or serious release blocker |
| **High** | Major functional defect, broken core workflow, significant architectural risk, or substantial quality problem |
| **Medium** | Meaningful usability, maintainability, reliability, or performance improvement |
| **Low** | Minor polish, consistency, or small improvement |
| **Opportunity** | Strategic enhancement or optional future capability; not a problem with the current product |

**Calibration rules**
- Severity reflects **actual impact**, not how strongly an agent feels about it.
- Severity is not priority. Severity describes impact; priority is decided by the Chair in P5.
- Judge severity by the product's real usage and scale, not hypothetical worst-case enterprise scenarios.
- Critical and High findings must include repro steps or direct code evidence.
- The Evidence Verifier may reclassify severity in P3, with a written reason. Severity disputes go to the Chair.

---

## 4. Finding Classification

Every finding belongs to exactly one category:

1. **Bug / Defect** — behaviour that is objectively wrong.
2. **Architectural Problem** — structural issue in boundaries, coupling, data flow, or responsibilities.
3. **UX / Usability Problem** — friction, confusion, or inefficiency in how users accomplish tasks.
4. **Visual Design Problem** — typography, layout, hierarchy, consistency, or polish.
5. **Performance / Cost Problem** — slowness, resource waste, or avoidable spend.
6. **Security / Reliability Risk** — vulnerability, failure mode, or fragility.
7. **Missing Capability** — something users need that does not exist.
8. **Redundancy / Complexity** — duplication, unnecessary abstraction, excess features or configuration.
9. **Documentation Problem** — wrong, missing, unclear, or outdated docs or product copy.
10. **Product Strategy Opportunity** — positioning, differentiation, or direction-level opportunity.

If an issue spans categories, split it into separate findings linked through `related`. Do not mix unrelated issues in one finding.

### 4.1 Strengths

Every reviewer also records **strengths**: things that work well and must be preserved through the redesign. Strengths use the same evidence rules but carry no severity. A review with no strengths recorded is incomplete.

---

## 5. Confidence Levels

| Level | Meaning |
|---|---|
| **High** | Directly observed or reproduced; evidence is unambiguous |
| **Medium** | Strong evidence, but some behaviour inferred rather than observed |
| **Low** | Plausible concern based on partial evidence; needs verification |

Low-confidence findings are valid and encouraged. They must not be presented as confirmed.

---

## 6. Recommendation Quality

Recommendations must be **actionable**. Vague statements such as "improve architecture", "make the UI cleaner", or "optimize performance" are rejected.

Every recommendation states:
1. **What** exactly needs to change (components, files, flows, contracts).
2. **Why** it needs to change (linked to the evidence).
3. **Expected outcome** once changed.
4. **Verification:** how anyone can confirm the outcome was achieved, as measurable or observable acceptance criteria.

Where appropriate, present **multiple approaches** with trade-offs (effort, risk, complexity, user impact).

**Proportionality:** recommend the simplest change that solves the problem. Additions must justify their maintenance cost. "Industry standard" is not a justification on its own; show why it matters for the product.

---

## 7. Review Conduct

- **Know the existing context first.** Read `.review/brief/existing-context.md` and the repo docs relevant to your area. Documented intent informs your review, but the code is the truth; report any gap between them.
- **Know the stack first.** Read `.review/brief/stack-profile.md` before reviewing. Judge code by the idioms and best practices of the stack actually in use, and by the project's own conventions. Never apply a foreign framework's standards.
- **Stay in your area.** Review deeply within your role. Observations outside it are recorded briefly with `handoff_to` the owning role, not developed into full findings.
- **Independence in P2.** Do not read other reviewers' findings during P2. First opinions must be your own.
- **No self-verification.** You never verify your own findings.
- **Quality over quantity.** There is no minimum number of findings. Padding with trivial items is a failure. Group minor Low-severity polish items into one consolidated finding per area.
- **Respect the original work.** Be direct about problems without hostility. Do not flatter the existing implementation, and do not dismiss it.
- **Plain language.** Every finding's `problem` and `impact` must be understandable to a non-specialist; they feed the Review Report.

---

## 8. Constructive Debate Rules

Every specialist must be willing to challenge another specialist's recommendation, respectfully and with evidence.

During debates, each participant must:
1. Present their original position and its supporting evidence.
2. Identify assumptions and weaknesses in opposing arguments.
3. Explain trade-offs and alternative solutions.
4. Acknowledge valid counterarguments explicitly.
5. Revise their conclusion when evidence justifies it. Changing position on new evidence is a strength, not a loss.
6. Record unresolved disagreements explicitly.

**Additional rules**
- Argue about the evidence and the outcome, never about the agent.
- New claims in a debate need the same evidence as findings.
- Rounds are capped (Charter §2.4). After the final round the Chair decides, and all dissent stays in the record.
- The Red Team may request reconsideration **once** per decision.

**The objective is to find the best decision, not to prove that one agent is right.**

---

## 9. Decision Log

Every significant recommendation gets a recorded disposition:

| Disposition | Meaning |
|---|---|
| **Accepted** | Will be implemented as recommended |
| **Accepted with modifications** | Will be implemented with stated changes |
| **Rejected** | Will not be implemented; reason recorded |
| **Deferred** | Valid, but not now; states the trigger for revisiting |
| **Requires experiment** | Needs a spike or prototype with defined success criteria |
| **Requires additional evidence** | Cannot be decided until specified evidence is gathered |

Each decision records:
- Decision ID (`DEC-<NNN>`) and linked finding IDs.
- Disposition and **rationale**.
- **Decision owner** (role code) and the deciding authority (Chair).
- **Dependencies** on other decisions or work.
- Trade-offs accepted and dissent recorded.
- For accepted items: acceptance criteria.

**Rejected recommendations never disappear from the record.** Duplicates are marked `merged into <ID>`, never deleted.

---

## 10. Execution Discipline (no wasted runs)

Long-running operations are expensive. They must not be repeated without reason.

### 10.1 Shared run log
- Every command that takes more than about 1 minute, or costs money (builds, full test suites, renders, live AI generation), is recorded in `.review/runs/run-log.json`: command, timestamp, git commit hash, duration, exit code, and output file path.
- Outputs are saved under `.review/runs/` and are **reusable by every agent**.

### 10.2 Test suite policy (the suite can take hours)
- **The full test suite is never run during the review (P0–P6).**
- Tests are reviewed **statically**: QA reads the test code, coverage reports, and any existing CI or test-result artifacts to judge coverage, quality and gaps.
- Existing results are reused where they exist (CI logs, previous reports). Their age and commit are recorded.
- **Targeted tests only:** a single test file or test case may run when it is the only way to verify a specific finding. Rules:
  - Requested by the Evidence Verifier or QA, with the reason logged.
  - Hard timeout of **5 minutes**. If it exceeds that, it is stopped, logged, and not retried.
  - Maximum **5 targeted test runs per review cycle** across the whole committee.
- The slowness of the test suite is itself a review topic. QA and the Cost & Performance Engineer assess why it is slow and recommend how to make it fast.
- In P7, only the tests linked to the changed items are run. A full run happens only if the implementation work has already made the suite fast enough.

### 10.3 Other run-once rules
- **Setup and build:** once per review cycle, in P0.
- **Renders:** a fixed set of representative sample projects rendered once by the Media Pipeline Engineer. Others reuse those files.
- **Live AI generation (Claude API calls):** a small fixed sample set, run once, outputs shared. No exploratory generation loops.
- **Dev server:** one shared instance per phase, stopped when the phase ends. No watch modes left running.
- **Before running anything long, check the run log.** If the same command already ran on the same commit, reuse its output.

### 10.4 When re-running is allowed
- The code has changed (P7, after implementation), and only for the affected areas.
- The Verifier needs to reproduce a specific disputed finding, using a **targeted** command (single test, single route, single render).
- A previous run failed for environmental reasons (logged with the cause).

### 10.5 Limits
- Every command runs with a timeout.
- Prefer static inspection over execution, and targeted execution over full runs.
- A command that fails twice for the same reason is logged as a finding and not retried again.

## 11. No Premature Implementation

The committee's job is review, analysis, debate, verification, and planning.

- Agents must **not** modify production code, configuration, assets, or design files during P0–P6.
- Agents write **only** inside `.review/`.
- Prototypes needed for a "Requires experiment" decision are planned, not built, unless the Chair explicitly assigns a separate, isolated experiment task (in a scratch branch or folder, never production code).
- The committee first agrees on **what** should change and **why**. Implementation happens after the review is complete.

---

## 12. Safety & Environment Rules

- No destructive commands (deleting data, resetting databases, force-pushing, wiping caches outside `.review/`).
- Never print, copy, or transmit secrets, API keys, or `.env` contents. A secrets finding cites the location, never the value.
- No external network calls that send project code or user data anywhere, except approved model and API calls in the sample runs.
- Spending on paid APIs during the review stays within the sample-run budget defined in P0.

---

## 13. Autonomy & Assumptions

- The review runs end to end with no human input.
- When information is missing or ambiguous, the agent makes the most reasonable assumption based on the product brief, records it in `assumptions`, and continues.
- Strategic decisions are made by the Chair and flagged `strategic` in the Review Report so the product owner can revisit them.
- An environment failure (app won't start, dependency missing) is logged as a finding. Review continues with whatever can still be examined.

---

## 14. Traceability

- Every item is traceable end to end: **Finding → Verification → Debate → Decision → Roadmap item → Implementation task → Re-review result**.
- IDs are stable and never reused: `SUT-<ROLE>-<NNN>`, `DBT-<NNN>`, `DEC-<NNN>`, `WS-<NN>`, `TASK-<NNN>`. TASK IDs identify canonical planning tickets for future implementation, stored in `.review/implementation/tickets/`. The committee creates and plans this work; it does not execute it.
- Every document in the Implementation Pack references the IDs it addresses.

---

## 15. Re-review Accountability (P7)

- The responsible specialists revisit **their own original findings** and check the actual implementation.
- A finding is **resolved** only when its acceptance criteria are satisfied **and** the relevant behaviour is verified with fresh evidence. The Evidence Verifier confirms.
- Outcome per finding: `resolved` · `partially-resolved` · `not-resolved` · `regressed`.
- The committee actively looks for **regressions and unintended consequences**. These become new findings linked to the change that caused them.
- "The code was changed" is not resolution. "The problem no longer occurs, here is the evidence" is.

---

## 16. Definition of a Good Review

A review meets this standard when:
- Every finding is evidenced, categorized, severity-calibrated, and actionable.
- Strengths are recorded alongside problems.
- No finding was verified by its own author.
- Every dispute ended in a recorded decision with rationale and dissent.
- Every recommendation has a disposition, including the rejected ones.
- The full test suite was never run, and no long-running operation was repeated without a logged reason.
- No production code was touched.
- The product owner can understand every outcome from the Review Report without reading raw data.
