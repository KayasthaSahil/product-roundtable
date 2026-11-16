---
name: stack-detection
description: P0 intake procedure for the product review committee — collect all existing repository context (README, CLAUDE.md, docs, ADRs, .claude/ content), detect the tech stack and commands, map the repo, and run setup/build once. Produces existing-context.md, stack-profile.md, stack-profile.json and repo-map.md. Also used before P7 to refresh the stack profile.
---

# Stack Detection & Repository Intake

Run from the repo root. Never modify anything outside `.review/`.

## Step 0 — Build the shared Codebase Atlas
Read `.claude/skills/codebase-atlas/SKILL.md`. Run `python3 .claude/skills/codebase-atlas/scripts/atlas.py build`, followed by `verify` and `status`. The Atlas is a factual navigation aid only. Continue full repository intake and direct source inspection; Atlas gaps never block P0.

## Step 1 — Scan
`python3 .claude/skills/stack-detection/scripts/scan-manifests.py > .review/brief/scan.json`
It lists manifests, lockfiles, configs, test configs, CI files, Docker files, docs, agent-context files, sample/fixture folders, and file counts by language and top-level folder. It skips vendored and generated folders.

## Step 2 — Existing context → `.review/brief/existing-context.md`
Read every context source from the scan (`context_files`): README*, CLAUDE.md, AGENTS.md, other AI-agent files, `docs/`, ADRs, PRDs, specs, design notes, roadmaps, CHANGELOG, existing `.claude/` agents/skills/commands (excluding the committee's own `review-*` files and skills), TODO/FIXME clusters, `.env.example`, sample projects.
For large docs, read the headings and the sections relevant to product intent and architecture.
Fill `templates/existing-context.md` (a compact table: path, one-line intent, trust, plus doc/code gaps; do not summarise docs the reader can open). Give each source a **trust level** by spot-checking claims against the code:
- `verified` — claims match the code · `unverified` — not checked · `outdated` — contradicts the code (note what).

## Step 3 — Stack profile → `.review/brief/stack-profile.md` + `.review/brief/stack-profile.json`
From manifests and configs (never guess versions — read them), fill `templates/stack-profile.md` and write the JSON:
```json
{
  "languages": ["..."],
  "surfaces": {"ui": true, "api": true, "cli": false, "render_pipeline": true, "ai_layer": true},
  "frameworks": {"frontend": "...", "backend": "...", "render": "...", "ai_sdk": "...", "db": "...", "queue": "..."},
  "commands": {"install": "...", "build": "...", "dev": "...", "dev_url": "http://localhost:...",
               "lint": "...", "typecheck": "...", "single_test": "<how to run ONE test file/case>"},
  "forbidden_commands": ["<regex that matches the FULL test suite invocation(s)>", "..."],
  "targeted_test_runner": ["<regex matching this project's test runner commands>"],
  "test_suite_note": "Full suite may take hours; never run during the review.",
  "size": {"files": 0, "by_language": {}},
  "notes": ["..."]
}
```
### Python and React quick hints

Detect and record these explicitly; they are the most common stacks.

- **Python:** `pyproject.toml` (`[tool.poetry]`, `[project]`, uv/hatch/pdm sections), `requirements*.txt`, `Pipfile`, `uv.lock`, `poetry.lock`. Frameworks: `manage.py` or `settings.py` (Django), imports of `fastapi`/`flask`/`starlette`/`aiohttp`. Data: `alembic.ini`, SQLAlchemy/Django ORM models, `pydantic`. Jobs: `celery`, `rq`, `dramatiq`, APScheduler. Tests: `pytest.ini`, `[tool.pytest]`, `tox.ini`/`noxfile.py`, `conftest.py`. Types/lint: `mypy`, `pyright`, `ruff`, `flake8`.
- **React:** `package.json` with `react`; build tool by config file (`vite.config.*`, `next.config.*`, `react-scripts`, `remix.config.*`, `webpack.config.*`); TypeScript if `tsconfig.json`. State/data: `redux`/`@reduxjs/toolkit`, `zustand`, `@tanstack/react-query`, `swr`, `apollo`. Tests: `jest`, `vitest`, `@testing-library/*`, `cypress`, `playwright`. Router: `react-router*`, Next `app/` or `pages/`.
- **Single-test commands to record in `single_test`:** `pytest path/to/test_file.py::test_name`, `python manage.py test app.tests.TestCase.test_name`, `vitest run path/to/file.test.ts -t "name"`, `jest path/to/file.test.ts -t "name"`.
- **`forbidden_commands` examples:** `^(python3? -m )?pytest\s*$`, `\btox\b`, `\bnox\b`, `manage\.py test\s*$`, `^npm (run )?test$`, `\bnpm run test:all\b`, `react-scripts test`, `^(vitest|jest)\s*$`, `make test`, CI scripts that call the suite.

**`forbidden_commands` is critical:** it must match every way the full suite is started in this repo (e.g. `^npm (run )?test$`, `\bnpm run test:all\b`, CI scripts that call the suite, Makefile targets like `make test`). Read `package.json` scripts / Makefile / CI config to find them. The Bash guard enforces this list.

## Step 4 — Repo map → `.review/brief/repo-map.md`
Generate it from the Atlas (no manual writing): `python3 .claude/skills/codebase-atlas/scripts/atlas.py repo-map`. Optionally append up to 10 verified data-flow lines at the bottom.

## Step 5 — Setup and build once
1. Check the run log first: `python3 .claude/skills/review-standards/scripts/runlog.py find "<install cmd>"`.
2. Run install and build **once** (Bash timeout ≤ 10 min each; plain install only, never add/remove packages).
3. Log each: `runlog.py add --cmd "<cmd>" --kind setup|build --role ARC --exit <code> --duration <s> --output .review/runs/<name>.log --note "..."` (save output with `> .review/runs/<name>.log 2>&1`).
4. If a step fails twice, stop retrying; record it in `stack-profile.md` → "Environment issues" and as a finding.

## P7 refresh
The P7 runbook owns the Codebase Atlas refresh. Do not rebuild it again when it is already current for this snapshot; if this skill is invoked independently and the Atlas has not yet been refreshed, run `python3 .claude/skills/codebase-atlas/scripts/atlas.py refresh --changed` (or `build --force` if freshness/schema is uncertain), then `verify`. Re-run Step 1 and Step 3 only if manifests changed since the base commit (`git diff --name-only <base>..HEAD`). Note changes at the bottom of `stack-profile.md`.
