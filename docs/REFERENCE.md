# Product Roundtable: Reference
*Short intro and one-command install: see the [README](../README.md). This page is the detailed reference.*

An autonomous review committee for [Claude Code](https://claude.com/claude-code), for **any software product**, with first-class guidance for **Python and React** projects. The main session acts as the **Chair** and orchestrates **17 specialist subagents** through eight phases (P0–P7). It produces two things:

- a product-first, evidence-led **HTML Review Report** (one offline file), and
- an **Implementation Planning Pack**: a roadmap plus self-contained, traceable, quality-reviewed **planning tickets** for work someone else will do later.

**It reviews and plans. It never changes your product code, dispatches coding agents, executes tickets or tracks delivery.** Approving a ticket approves it as part of the plan only.

## Works for any project

The committee is not tied to one product. In P0 the Chair learns the product from its own repository (README, docs, code, UI) and writes the real product name, users, workflows and quality bar into `.review/brief/product-brief.md` and `product-context.json`. Every agent then refers to "the product" as described there, and the HTML report shows the real product name.

- **Python and React** get dedicated investigation playbooks (`.claude/skills/review-committee/references/stack-playbooks.md`): FastAPI/Flask/Django, jobs, data access, security and tests on the Python side; components, hooks, state and data fetching, accessibility and bundle cost on the React side; and the API contract, auth and long-operation seams between them. The full-suite guard recognises `pytest`, `tox`, `nox`, `manage.py test`, `jest`, `vitest` and `react-scripts test`.
- **Other stacks** work through stack detection and the generic role checklists; the Atlas simply reports lower coverage for languages it can't parse.
- **Roles that don't apply are skipped, not forced.** The AI Systems Engineer (any LLM provider), the Media & Processing Pipeline Engineer and the Explainability Designer do a phase-level skip with a recorded reason when the product has no AI layer, no media/processing pipeline, or no AI-driven behaviour. Competitors are chosen from the brief and market search, not from a fixed list.
- **Owner-judged areas:** subjective or creative quality of any generated content stays with the product owner by default (change it in the brief). The committee reviews the system that produces it and its technical correctness.

## What's in this bundle

```
.claude/
  agents/      17 subagents (review-*.md): PMV PMS CMP ARC FE BE AI MED VIS UX XAI DOC QA CPE RED VER SCR
  skills/      review-committee (Chair runbook, charter, dispatch matrix, phase runbooks, state/index scripts)
               review-standards (finding format, severity, schemas, validator)
               stack-detection (P0 intake)        codebase-atlas (shared codebase map, see below)
               debate-protocol (P4)               verification-protocol (P3/P5/P7)
               implementation-pack (tickets, views, checkers)    report-builder (deterministic HTML report)
  hooks/       guard-writes.py, guard-bash.py, guard-read.py (+ _common.py)
  settings.json  registers the hooks
.mcp.json      Playwright MCP, pinned (browser for UI review)
tests/                         developer tests (not part of the install; copy only .claude/ and .mcp.json)
```

## Install

1. **Manual install (alternative to the one-command installer):** copy `.claude/` and `.mcp.json` into the root of the repository you want reviewed.
   - Already have `.claude/settings.json`? Merge the `"hooks"` block instead of overwriting.
   - Already have `.mcp.json`? Add the `"playwright"` entry to your `mcpServers`.
   - Committee files are prefixed `review-` or uniquely named, so existing agents and skills are untouched.
2. **Requirements:** Python 3.9+ (standard library only) and Node/npx (for Playwright MCP). The hooks try `python3` and fall back to `python`, so Windows works without an alias.
3. **Playwright MCP:** start Claude Code in the repo and approve the `playwright` server (`/mcp` shows status). The first run downloads a browser. Without it, UI roles inspect code and screenshots only and record the limitation.
4. **Optional, better code understanding:** `pip install -r .claude/skills/codebase-atlas/requirements-optional.txt` adds Tree-sitter parsing for JavaScript, TypeScript, TSX and Go. Nothing else is needed; see [Codebase Atlas](#codebase-atlas-shared-codebase-map).

`.review/` is created at runtime; `.review/runs/` and `.review/evidence/` are git-ignored automatically.

## Run

From the repo root in Claude Code:

| Command | What happens |
|---|---|
| `/review-committee start` | Initialise `.review/`, run **P0 Intake** (existing context, stack detection, Atlas, brief, scope) |
| `/review-committee next` | Run the next phase (P1 → P6). **Default: one phase per session** (`/clear` between phases) |
| `/review-committee status` | Where the review stands |
| `/review-committee report` | Rebuild the report |
| `/review-committee pause` / `resume` | Pause (guards off) / resume |
| `/review-committee ticket TASK-001` | Read-only: scope, dependencies, blockers, plan-readiness of a ticket |
| `/review-committee approve-plan TASK-001` | Record your approval of a ticket **as a plan item** (not implementation authorisation). Only acts on your explicit approval of that ticket or a listed set |
| `/review-committee rereview` | Optional **P7**: independently check changes made later by an external process (review only) |

To run several phases unattended, say so explicitly, e.g. `/review-committee next — run P1 through P6 without stopping`. Each phase still passes its own gate and state transition, and you get one consolidated summary at the end.

During a review the Chair never asks you routine questions. The only interactions are the two commands above and the end-of-phase progress note.

## Phases

| Phase | Purpose | Gate |
|---|---|---|
| **P0 Intake** | Existing context, stack, repo map, Atlas, product brief, scope, complexity budget | Brief, scope and validated `product-context.json` exist |
| **P1 Discovery** | First-time-user value, competitive benchmark, visual and UX first impressions | User profiles and competitive benchmark exist; findings and `product-context.json` validate |
| **P2 Independent review** | Each specialist reviews its area **without reading the others' findings** | Every assigned reviewer has a valid findings file, or a recorded matrix-based non-dispatch; every area covered |
| **P3 Verification** | Integrity checks, direct verification, cross-verification (never by the author) | Every finding has a verdict |
| **P4 Debate** | Structured disputes, Red Team challenges, Chair decides | Every dispute has a decision |
| **P5 Decision** | Every verified finding gets a disposition; roadmap; **planning tickets** with a Chair nine-point quality review; Verifier sign-off | `ticket-check` passes (enforced by `state.py advance`) |
| **P6 Readiness gate** | Go / Go-with-conditions / Hold per workstream; pack finalised; **review complete** | `ticket-check` and `trace-check` pass (enforced by `state.py advance`) |
| **P7 Re-review** *(optional)* | Verify externally implemented changes against the original findings | Verifier confirms each outcome |

`state.py advance` refuses to complete P5 or P6 if the deterministic checks fail. `--force` exists, is logged, and is for a recorded reason only.

## Outputs

- **Report:** `.review/report/index.html`. Self-contained, works offline, mobile-friendly. Built deterministically from `.review/brief/product-context.json` and the canonical records; no narrative is generated per phase.
- **Pack:** `.review/implementation/`. Start at `START-HERE.md`, pick a ticket from `tickets/INDEX.md`, open `tickets/TASK-NNN.json` and only the references it links. Stack and product context: `.review/brief/stack-profile.md` and `product-brief.md`.

Canonical records are JSON (findings, decisions, roadmap, tickets). Markdown indexes (`tickets/INDEX.md`, `PLAN/roadmap.md`, `DECISIONS/decision-log.md`) are **generated** by `build-pack-views.py` and never edited by hand.

### Who owns what

| Owner | Owns |
|---|---|
| **Chair** | Product brief, scope, decisions, roadmap, **tickets and TASK IDs** |
| **Specialists** | Findings, and the content of their domain `REFERENCES/*` documents (only when relevant) |
| **Scribe (on assignment only)** | Fixes pack content flagged by `trace-check.py`; views are script-generated |
| **Scripts** | Validation, indexing, dependency and trace checks, report rendering |

## Codebase Atlas (shared codebase map)

P0 builds a persistent map in `.review/codebase-atlas/` (modules, symbols, routes, APIs, data models, integrations, tests, relationships) so specialists don't each rediscover the repo. It is **navigation, not evidence**: every specialist still reads the source directly, and an incomplete or stale Atlas never blocks a phase or restricts an investigation.

The Atlas is explicit about how much it actually knows. Every record carries an extraction tier, and `atlas.py coverage` shows parsed-versus-guessed per language:

| Tier | Source | Can be VERIFIED? |
|---|---|---|
| `semantic` | Output of an external analyzer you ingest (tsc script, pyright, gopls, SCIP converter) | Yes, pinned to file digests |
| `ast` | Python's own parser | Yes |
| `tree-sitter` | Real syntax trees for JS/TS/TSX/Go (optional install) | Yes (syntax only) |
| `adapter` | Framework conventions: Express/Fastify, NestJS, React Router, fetch/axios, Go HTTP routers, Next.js file routes | **No**, INFERRED at best |
| `pattern`, `heuristic`, `marker`, `minimal`, `inventory` | Regex fallback, name guesses, keyword hits, unsupported languages, file listing | **No** |

Behaviour that can't be resolved statically (dynamic imports, non-literal route paths, dependency injection, reflection, config-built routes) is **counted as unresolved and never guessed**.

```bash
python3 .claude/skills/codebase-atlas/scripts/atlas.py build | status | coverage | verify | refresh --changed
python3 .claude/skills/codebase-atlas/scripts/atlas.py search "<term>" | module "<id-or-path>" | dependencies "<id-or-path>"
python3 .claude/skills/codebase-atlas/scripts/atlas.py feature "<name>" | workflow "<name>" | ingest facts.json
```

Languages without a Tree-sitter adapter (Java, Kotlin, Rust, C#, Ruby, PHP) stay on the regex or minimal tier, and `coverage` warns about it. Add adapters as plugins in `.claude/skills/codebase-atlas/adapters/`. Details: `.claude/skills/codebase-atlas/SKILL.md`.

## Safety guards (active only while a review is running)

- Writes are allowed **only inside `.review/`**. Production code is never modified.
- **Full test suite blocked** (default runner patterns plus `forbidden_commands` detected in P0). Targeted single tests: Bash timeout ≤ 5 min, max 5 per cycle.
- Blocked: git-mutating commands, dependency changes, deploys, destructive DB/file commands, reading or printing secrets (`.env` etc.).
- Guards switch **off** when the review is paused or complete. Emergency off: set env `REVIEW_GUARDS=off`.

## Customising for your product

Nothing needs editing before the first run. To adjust the committee for a specific product, change the brief, not the agents: the product name, owner-judged areas, constraints and out-of-scope list in `.claude/skills/review-committee/references/templates/product-brief.md` (copied into `.review/brief/` in P0) and `review-scope.md` drive every role. Add Atlas framework adapters in `.claude/skills/codebase-atlas/adapters/`.

## Cost and coordination

All 17 specialists stay installed and active; the dispatch matrix decides which are called in each phase, and a skip needs a concrete scope reason, never token savings. Compatible work for one role is bundled into one invocation per phase, agents get compact task-specific packets, and mechanical work (validation, indexing, dependency checks, report rendering) runs in scripts instead of model calls. Opus handles architecture, backend, AI, security, Red Team and verification judgement; Sonnet handles product, UX, visual, documentation and planning work. Dispatch metrics record calls, skips, retries and bundled assignments, plus token usage only when the platform reports it. Tokens are never estimated.

## Tests

```bash
python3 -m unittest discover -s tests   # Atlas, tiers, ingest, roster, ticket quality checker
```

The Tree-sitter tests skip automatically if the optional packages aren't installed. These tests use fixture repositories; they check the tooling and workflow contracts, not a live product.

## Reference

`.claude/skills/review-committee/references/`: `charter.md` (roles, phases, report and pack specs), `specialist-dispatch-matrix.md` (**authoritative** dispatch triggers), `dispatch-packet.md` (context profiles), `chair-decision-rules.md`, `ticket-generation.md`. Binding review rules: `.claude/skills/review-standards/references/review-standards.md`.
