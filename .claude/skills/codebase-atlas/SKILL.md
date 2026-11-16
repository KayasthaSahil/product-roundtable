---
name: codebase-atlas
description: Build and maintain a persistent, evidence-backed map of repository modules, symbols, routes, APIs, data models, integrations, AI/media components, tests and their relationships for the Product Review Committee. Shared factual context only; never a substitute for specialist judgement or direct source investigation.
---

# Codebase Atlas — Shared Codebase Intelligence System

## Purpose and non-negotiable boundaries

The Atlas reduces repeated repository discovery by maintaining a reusable, navigable description of the codebase. It does **not** reduce review depth, specialist responsibilities, agent count, source access, or independent judgement.

- All 17 specialist agents and the Chair remain installed, callable and active for the review cycle. Never merge or deactivate a specialist because the Atlas exists or because its extraction is incomplete. The existing `specialist-dispatch-matrix.md` remains authoritative for phase-specific invocation; SCIS must never be the reason for a phase skip. If an area is genuinely absent, record applicability under the existing matrix rather than removing the role.
- Every specialist still performs their complete assigned review and directly opens relevant source files, follows call/data paths, tests behaviour where required, and gathers their own evidence.
- The Atlas contains descriptive repository facts and traceable relationships only. It must not contain severity, quality ratings, recommendations, security verdicts, UX opinions, architectural judgements, or other specialist conclusions.
- P2 reviewers may share the same factual Atlas but must not read one another's findings, opinions, or work products. The Atlas must not encode another reviewer's conclusions.
- No token ceilings, file-count limits, depth limits, mandatory source-inspection limits, or agent reductions are introduced. Efficiency comes from reusing factual discovery, not from doing less meaningful work.
- An incomplete, stale, unavailable, or disputed Atlas never blocks a phase. The reviewer falls back to direct source inspection and records the limitation.
- The committee is a review, decision, and planning system. It may create implementation plans and tickets, but it must not modify product code, dispatch implementation agents, or track implementation progress.

## Canonical location

All generated data belongs under `.review/codebase-atlas/`:

```text
.review/codebase-atlas/
├── atlas.json                         # small index, snapshot and section pointers
├── manifest.json                      # freshness, extractor version and coverage
├── product/
│   ├── features.json                  # product capabilities mapped to source evidence
│   └── workflows.json                 # end-to-end user/system workflows
├── architecture/
│   ├── modules.json                   # module inventory and responsibilities
│   ├── relationships.json             # canonical graph nodes and edges
│   └── data-flows.json                # verified read/write and execution paths
├── interfaces/
│   ├── frontend.json                  # routes and UI components
│   ├── apis.json                      # API endpoints and call sites
│   └── integrations.json              # external systems and SDKs
├── testing/coverage-map.json          # test inventory and evidence-backed links
├── evidence/source-index.json         # source records, paths, symbols, lines, confidence
└── cache/file-records.json            # content-hash cache for deterministic extraction
```

JSON is canonical. Diagrams, summaries and navigation views are derived from these records; do not manually maintain duplicate diagrams as a second source of truth.

## P0 build procedure

The Principal Architect owns the initial technical extraction. The Chair owns product interpretation and the committee-wide Atlas contract.

1. Identify the repository snapshot: Git HEAD plus a working-tree content digest. The digest matters because uncommitted files are part of the review snapshot.
2. Run `python3 .claude/skills/codebase-atlas/scripts/atlas.py build` from the repository root. The scanner excludes generated/vendor/build folders and secret-like files; it does not read `.env` contents or credentials.
3. Run `python3 .claude/skills/codebase-atlas/scripts/atlas.py verify` and `.../atlas.py status`.
4. Review the extractor coverage and parser notes in `manifest.json`. Treat lexical extraction for non-Python languages as candidate discovery, not proof of complete semantics.
5. Inspect representative and high-impact source paths directly. Enrich `architecture/modules.json`, `product/features.json`, `product/workflows.json`, `architecture/data-flows.json`, and `interfaces/*` with source-grounded explanations and relationships. Every enriched fact must carry source evidence and a confidence state.
6. Build the normal P0 `existing-context.md`, `stack-profile.md`, `repo-map.md`, `product-brief.md`, and `review-scope.md` as before. The Atlas supplements these outputs; it does not replace them.
7. Record unresolved or partially mapped areas explicitly. Do not fill gaps with plausible guesses.

### Product facts versus implementation facts

`product/features.json` must distinguish:
- `intended`: what the product brief, requirements or owner documentation says should exist;
- `observed`: what the current source demonstrably implements;
- `gap`: a documented difference between intended and observed behaviour, without assigning severity or proposing a fix.

A workflow is not `VERIFIED` merely because its screens or modules exist. Verify the actual sequence and transitions through source, runtime evidence, or tests.

## Evidence and confidence contract

Every Atlas record or relationship must include, where applicable:

- stable record ID;
- descriptive name and type;
- repository-relative source path and line/symbol;
- snapshot identifier or digest;
- discovery method (`AST`, `import-parser`, `route-pattern`, `manual-source-trace`, `runtime`, `test`, etc.);
- confidence/verification state: `VERIFIED`, `INFERRED`, `PARTIAL`, or `UNVERIFIED`;
- last-verified snapshot.

Rules:
- `VERIFIED`: directly confirmed in source/runtime/test evidence at the recorded snapshot.
- `INFERRED`: plausible relationship discovered statically but not traced end to end.
- `PARTIAL`: only part of the path or contract is established.
- `UNVERIFIED`: retained as a question or candidate, not a fact.
- Never silently promote an inferred record to verified.
- An import edge is not proof of runtime invocation. A component name is not proof of a user workflow. A test file is not proof that a feature is covered.
- Prefer real parsers over patterns. Every record carries an `extraction` tier, strongest first: `semantic` (ingested external analyzer output), `ast` (Python's parser), `tree-sitter` (optional syntax-tree tier for JS/TS/TSX/Go), `adapter` (framework convention on top of a parse), `pattern` (regex fallback, not parsed), `heuristic` (name/path guess), `marker` (keyword hit), `minimal` (language with no structural extractor), `inventory` (file listing). `adapter`, `pattern`, `heuristic`, `marker` and `minimal` records are capped below `VERIFIED` (a convention is not proof), and `verify` fails if one claims it.
- Run `atlas.py coverage` after every build. It shows, per language, how many files were parsed versus pattern-matched or only listed, records by tier, how many imports resolved to repo modules, truncated marker hits, and the behaviours that are unresolved by design (dynamic imports, dependency injection, reflection, runtime-registered routes, config-built routes). A clean-looking map for a `pattern` or `minimal` language is never evidence of completeness; report the coverage warnings to specialists.
- Dynamic behaviour stays explicitly unresolved. Never guess it, and never let incomplete coverage restrict a specialist's investigation.

## Graph model

Use stable nodes for features, workflows, frontend routes/components, APIs, backend modules/symbols, database entities, external integrations, AI components, media components, tests, and configuration. Supported edge types include `USES`, `CALLS`, `IMPORTS`, `DEPENDS_ON`, `READS`, `WRITES`, `EXPOSES`, `TESTED_BY`, `IMPLEMENTS`, `SUPPORTS`, and `DEFINED_IN`.

Each edge must carry evidence and confidence. Do not invent a `CALLS`, `READS`, or `WRITES` edge from an import alone. JSON is the initial graph store; do not introduce a graph database unless a later measured requirement justifies it.

## Optional tiers (nothing here is mandatory)

The Atlas works with the Python standard library alone. Each tier below adds accuracy when its tooling exists, and `atlas.py coverage` always shows which tiers were actually used.

1. **Baseline (stdlib):** Python AST, regex fallback for other languages, all labelled by tier.
2. **Tree-sitter (optional):** `pip install -r .claude/skills/codebase-atlas/requirements-optional.txt` gives real syntax trees for JavaScript, TypeScript, TSX and Go. Comments and string contents stop being mistaken for code. Installing or removing it changes the extractor signature, so cached records are re-extracted automatically. Set `ATLAS_DISABLE_TREE_SITTER=1` to force the baseline (reproducible runs).
3. **Framework adapters (built on tier 2):** Express/Fastify-style routes, NestJS decorators, React Router (`<Route path>` and route-config objects), `fetch`/`axios` call sites, Go HTTP routers (net/http, chi, gin, echo style) and Next.js file-system routes (only when `next` is in `package.json`). Adapter facts are `INFERRED` at best. Anything not statically knowable (non-literal route paths, dynamic `import()`/`require()`, non-literal API URLs) is counted under "Unresolved in this repository", never guessed. Add your own with a plugin in `.claude/skills/codebase-atlas/adapters/` (example below); plugins load from the skill folder only, never from the repository under review.
4. **Semantic analyzers (optional, external):** any tool that resolves symbols across files (a `tsc` script, pyright, gopls, a SCIP converter) can write a JSON file and run `atlas.py ingest <file>`:

```json
{"tool": "name version",
 "facts": [{"kind": "symbol", "name": "greet", "path": "src/a.py", "line": 12, "description": "..."}],
 "edges": [{"from_path": "src/b.py", "to_path": "src/a.py", "type": "CALLS", "line": 3}]}
```

   Ingested facts are `VERIFIED` with the tool named as provenance. They are pinned to the file digests at ingest time and are skipped (counted as stale) once those files change, so re-run the analyzer and ingest again after edits. Paths outside the repository are rejected.

```python
# .claude/skills/codebase-atlas/adapters/my_framework.py   (loaded from the skill folder only)
from ts_adapters import adapter, _txt, _line, _lit, _args

@adapter('javascript', 'typescript', 'tsx')       # languages this adapter applies to
def my_routes(lang, idx, src, path, ctx, out):    # idx: Tree-sitter node type -> [nodes]
    for n in idx['call_expression']:
        f = n.child_by_field_name('function')
        if f is not None and _txt(f) == 'server.route':
            ctx['unresolved']['server-route-config-not-parsed'] += 1   # count what you cannot resolve; never guess
    # to emit a fact: out.append((kind, name, line, description, symbol, 'INFERRED', 'adapter'))
```

Java, Kotlin, Rust, C#, Ruby and PHP currently have no Tree-sitter adapter: they stay on the regex or minimal tier and `coverage` warns accordingly.

## Commands

Run from repository root:

```bash
python3 .claude/skills/codebase-atlas/scripts/atlas.py build
python3 .claude/skills/codebase-atlas/scripts/atlas.py status
python3 .claude/skills/codebase-atlas/scripts/atlas.py coverage   # tiers, tooling, unresolved behaviour, warnings
python3 .claude/skills/codebase-atlas/scripts/atlas.py ingest facts.json   # optional semantic analyzer output
python3 .claude/skills/codebase-atlas/scripts/atlas.py search "authentication"
python3 .claude/skills/codebase-atlas/scripts/atlas.py module MOD-0123456789
python3 .claude/skills/codebase-atlas/scripts/atlas.py feature "export"
python3 .claude/skills/codebase-atlas/scripts/atlas.py workflow "<workflow name>"
python3 .claude/skills/codebase-atlas/scripts/atlas.py dependencies MOD-0123456789
python3 .claude/skills/codebase-atlas/scripts/atlas.py verify
python3 .claude/skills/codebase-atlas/scripts/atlas.py refresh --changed
```

`build` reuses cached per-file extraction when the content digest is unchanged. `refresh --changed` reparses changed/added files, drops deleted files, and rebuilds the relationship graph from the current file records. It does not silently retain stale relationships. The manifest records what was parsed, reused and deleted. If the extractor schema changes, the cache is invalid, or freshness cannot be established, run `build --force`.

## Specialist protocol (mandatory on every invocation)

`build` and `refresh` also write a short per-role digest to `.review/codebase-atlas/digest/<ROLE>.md` (`atlas.py digest` regenerates it). Specialists read their digest, not this SKILL.

1. Read the relevant Atlas index/records (start with your digest) before broad repository discovery when the Atlas is available.
2. Use Atlas search/navigation to locate candidate files, symbols, related modules, routes, APIs, models, tests and integrations.
3. Open source files directly. Trace the paths that matter to your question; inspect additional source beyond the Atlas whenever needed. Atlas paths are leads, not a permitted-source boundary.
4. Independently reproduce or verify claims required by your specialist role. Do not cite an Atlas record as the sole evidence for a finding.
5. Challenge stale, missing, incorrect, or misleading Atlas facts with a structured discrepancy record (template below). Continue your review even if the discrepancy cannot be resolved immediately.
6. Keep your expert conclusions in your own review findings/debate/gate outputs. Never write them into the Atlas.
7. In P2, do not read other specialists' findings. Shared factual Atlas access does not weaken P2 independence.

### Specialist Atlas query focus

| Specialist | Useful Atlas starting points (not limits) | Full judgement remains with |
|---|---|---|
| PM — User Value | features, workflows, routes, capability gaps | user value, outcomes, user needs, completeness, prioritisation |
| PM — Scope & Simplicity | feature inventory, modules, dependencies, workflows | MVP boundary, complexity, scope discipline, simplicity |
| Competitive Analyst | intended features, observed capabilities, product surfaces | market comparison, differentiation, opportunity and positioning |
| Principal Architect | modules, imports, graph, data flows, integrations, build/config | architecture, boundaries, trade-offs, maintainability, migration |
| Frontend Engineer | routes, components, API call sites, frontend dependencies | frontend correctness, state, performance, accessibility implementation |
| Backend Engineer | APIs, backend modules, symbols, data models, integrations | backend correctness, contracts, jobs, data integrity, observability |
| AI Systems Engineer | AI components, prompts/config references, model/tool integrations, tests | AI architecture, reliability, evaluation, safety and reproducibility |
| Media Pipeline Engineer | media components, render/export modules, workflows, tests | media correctness, deterministic rendering, pipeline integrity |
| Visual Design Critic | routes, components, style/config files | visual hierarchy, typography, colour, polish, consistency |
| UX / Interaction Designer | workflows, routes, components, API transitions | interaction quality, usability, task completion, accessibility experience |
| AI Explainability & Control Designer | AI workflow records, output contracts, UI surfaces | explainability, user control, transparency and trust |
| UX Writer & Documentation Reviewer | routes, components, docs, config labels | language, terminology, content clarity and documentation quality |
| QA, Reliability & Security Engineer | APIs, trust boundaries, integrations, tests, data flows | security, reliability, failure modes, test adequacy and risk |
| Cost & Performance Engineer | model/API call sites, media pipeline, dependencies, data flows | latency, throughput, compute/token/storage cost and budgets |
| Red Team / Contrarian | feature/workflow graph, integrations, trust boundaries | adversarial challenge, abuse cases, hidden assumptions and pre-mortem |
| Evidence Verifier | source-index records and cited paths for assigned claims | independent evidence validity, reproducibility and verdicts |
| Committee Scribe & Reporter | Atlas only for factual labels/paths and cross-reference | faithful reporting; no new findings or judgements |

## Curated enrichment and rebuild safety

The extractor owns deterministic file/symbol/route/API/test discoveries. The Chair/Architect may enrich module records with fields such as `purpose`, `responsibilities`, `confidence`, and `last_verified_snapshot`; enrich interface records with contract/context fields; and add traced data flows. Rebuilds merge these curator-owned fields by stable record ID instead of replacing them. When a cited file or its reverse import-dependency closure changes, affected curated records are marked `freshness: STALE` and the manifest becomes `PARTIAL` until re-traced.

For a manually verified graph relationship, add a node/edge to `architecture/relationships.json` with `origin: "manual"`, a stable ID for manual nodes, an allowed edge type, exact evidence (`path` and `line`), confidence, and `last_verified_snapshot`. The next build preserves these manual nodes/edges; affected ones become stale rather than being silently deleted. Do not label an edge `CALLS`, `READS`, or `WRITES` unless the actual path was traced.

Curated record shapes (the extractor never writes these; the Chair/Architect curate them from source evidence):

`product/features.json` entries:
```json
{
  "id": "FEAT-001",
  "name": "Feature name",
  "intended": {
    "description": "What product documentation or product brief says should exist.",
    "sources": [{"path": "docs/requirements.md", "line_start": 1, "line_end": 5}],
    "confidence": "VERIFIED|INFERRED|PARTIAL|UNVERIFIED"
  },
  "observed": {
    "description": "What the current implementation demonstrably does.",
    "sources": [{"path": "src/feature.py", "line_start": 10, "line_end": 30, "symbol": "FeatureService"}],
    "confidence": "VERIFIED|INFERRED|PARTIAL|UNVERIFIED"
  },
  "gap": {
    "exists": false,
    "description": "Factual difference only; do not assign severity or propose a fix here."
  },
  "related_workflows": [],
  "snapshot": "git-head-or-tree-digest",
  "last_verified_snapshot": "git-head-or-tree-digest"
}
```

`product/workflows.json` entries:
```json
{
  "id": "FLOW-001",
  "name": "Workflow name",
  "actor": "User or system actor",
  "trigger": "Observable trigger",
  "steps": [
    {"order": 1, "description": "Observed action/transition", "source": {"path": "src/example.py", "line_start": 1, "line_end": 5}, "confidence": "VERIFIED"}
  ],
  "entry_points": [],
  "exit_states": [],
  "related_features": [],
  "snapshot": "git-head-or-tree-digest",
  "confidence": "VERIFIED|INFERRED|PARTIAL|UNVERIFIED"
}
```

## Two-way correction protocol

Specialists create `.review/codebase-atlas/discrepancies/<ROLE>-<NNN>.json` using `templates/discrepancy.json`. A discrepancy includes the Atlas record/edge ID, what is wrong or missing, exact source evidence, suggested correction, confidence, and affected snapshot. The Chair/Architect validates it against source before updating canonical Atlas data. Preserve an audit entry in `discrepancies/accepted-log.json`; do not silently overwrite. A disagreement about quality or interpretation is a specialist finding, not an Atlas discrepancy.

## Refresh and lifecycle

- Reuse the Atlas when the source snapshot and extractor version match.
- After changes, run `refresh --changed`; changed/added files are reparsed, deleted files removed, and graph relationships rebuilt.
- Structural changes, schema/extractor upgrades, cache corruption, or uncertain freshness require a full rebuild (`build --force`).
- P7 refreshes the Atlas for the changed snapshot before re-review. Reviewers then inspect the actual diff and source; Atlas refresh is not proof that a change is correct or resolved.
- Do not overwrite product-intent records with observed implementation or specialist opinions. Retain provenance and history.

## Quality and efficiency measurement

Track baseline versus subsequent reviews of comparable scope: initial build effort, cache reuse, repeated source discovery, discrepancy rate, stale/missing relationship rate, finding verification rate, important finding coverage, and overall phase/context consumption. Report measured deltas only; do not promise a token-saving percentage. A lower token count is not success if finding quality, coverage, independent judgement, or phase deliverables decline.

## Refresh semantics and known limits

- Per-file extraction is cached by content digest and by extractor signature (installing or removing Tree-sitter re-extracts). `refresh --changed` reparses changed or added files, removes deleted ones and rebuilds the graph.
- Changes propagate through reverse import dependencies. Curated features, workflows, module descriptions, data flows, interface enrichments, test metadata and manual graph edges survive rebuilds and are marked stale when the source they cite changes.
- Manual graph relationships must use `origin: "manual"` and carry exact source evidence. Specialist conclusions are never stored in the Atlas.
- `verify` checks source paths, line ranges, graph endpoints, duplicate IDs, confidence values, extraction-tier overclaims and repository path boundaries.
- Static import edges are `INFERRED`, never proof of runtime calls. Complete features, workflows, data flows and traced call/read/write relationships need source-level synthesis and verification by the Chair/Architect and specialists.
- Atlas freshness and coverage do not determine review quality. Specialists keep their full independent investigations.

Tests live outside the installed bundle, in the repository's `tests/` folder: `python3 -m unittest discover -s tests -v`. They use temporary fixture repositories and never inspect product source.

## Failure behaviour

If scanner/parser support is missing, a file is too large, a path is unreadable, or the Atlas is stale: mark the affected area partial/unverified, use direct source inspection, and continue. Never block P0–P7 or downgrade a specialist's scope because of Atlas limitations.
