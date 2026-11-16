#!/usr/bin/env python3
"""Scan the repository (run from root) and print JSON describing manifests, configs, docs and size.
Skips vendored/generated folders. Read-only."""
import json, os, re, sys
from collections import Counter

SKIP = {".git", "node_modules", ".review", "dist", "build", "out", ".next", ".nuxt", ".svelte-kit", "coverage",
        ".venv", "venv", "env", "__pycache__", ".cache", ".turbo", ".parcel-cache", "target", "vendor", ".idea",
        ".vscode", ".gradle", "Pods", ".expo", "storybook-static", ".remotion", "tmp", ".pytest_cache", ".mypy_cache"}
MANIFESTS = {"package.json", "pnpm-workspace.yaml", "lerna.json", "turbo.json", "nx.json", "requirements.txt",
             "pyproject.toml", "setup.py", "Pipfile", "poetry.lock", "go.mod", "Cargo.toml", "pom.xml",
             "build.gradle", "build.gradle.kts", "composer.json", "Gemfile", "deno.json", "bun.lockb",
             "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "uv.lock", "Makefile", "justfile", "Procfile"}
CONFIG_RE = re.compile(r"^(tsconfig.*\.json|vite\.config\..*|next\.config\..*|nuxt\.config\..*|svelte\.config\..*|"
                       r"astro\.config\..*|webpack\.config\..*|remotion\.config\..*|tailwind\.config\..*|postcss\.config\..*|"
                       r"\.eslintrc.*|eslint\.config\..*|\.prettierrc.*|babel\.config\..*|docker-compose.*\.ya?ml|Dockerfile.*|"
                       r"\.env\.(example|sample|template)|prisma/schema\.prisma|schema\.prisma|drizzle\.config\..*|alembic\.ini|"
                       r"vercel\.json|netlify\.toml|fly\.toml|render\.yaml|nodemon\.json|ecosystem\.config\..*)$", re.I)
TEST_RE = re.compile(r"^(jest\.config\..*|vitest\.config\..*|vitest\.workspace\..*|playwright\.config\..*|cypress\.config\..*|"
                     r"pytest\.ini|conftest\.py|tox\.ini|\.mocharc.*|karma\.conf\..*|setupTests\..*)$", re.I)
CONTEXT_RE = re.compile(r"^(readme.*|claude\.md|agents\.md|gemini\.md|\.cursorrules|copilot-instructions\.md|contributing.*|"
                        r"changelog.*|architecture.*|design.*\.md|roadmap.*|todo.*|prd.*|spec.*\.md|adr.*\.md|plan.*\.md|notes.*\.md)$", re.I)
EXT = {".ts": "TypeScript", ".tsx": "TypeScript/React", ".js": "JavaScript", ".jsx": "JavaScript/React", ".mjs": "JavaScript",
       ".cjs": "JavaScript", ".py": "Python", ".go": "Go", ".rs": "Rust", ".java": "Java", ".kt": "Kotlin", ".rb": "Ruby",
       ".php": "PHP", ".cs": "C#", ".vue": "Vue", ".svelte": "Svelte", ".css": "CSS", ".scss": "SCSS", ".html": "HTML",
       ".sql": "SQL", ".sh": "Shell", ".swift": "Swift", ".dart": "Dart"}

out = {"manifests": [], "configs": [], "test_configs": [], "ci": [], "context_files": [], "docs_dirs": [],
       "claude_dir": [], "sample_dirs": [], "test_files_count": 0, "size": {"files": 0, "by_language": {}, "by_top_folder": {}},
       "package_scripts": {}}
lang, top = Counter(), Counter()
for dp, dns, fns in os.walk("."):
    rel = os.path.relpath(dp, ".")
    parts = [] if rel == "." else rel.split(os.sep)
    dns[:] = [d for d in dns if d not in SKIP and not (d.startswith(".") and d not in (".claude", ".github", ".gitlab"))]
    for d in dns:
        low = d.lower()
        if low in ("docs", "doc", "documentation", "adr", "adrs", "design", "specs"):
            out["docs_dirs"].append(os.path.join(rel, d))
        if low in ("samples", "sample", "examples", "example", "fixtures", "demo", "demos", "templates"):
            out["sample_dirs"].append(os.path.join(rel, d))
    for fn in fns:
        p = os.path.normpath(os.path.join(rel, fn))
        out["size"]["files"] += 1
        top[parts[0] if parts else "(root)"] += 1
        ext = os.path.splitext(fn)[1].lower()
        if ext in EXT:
            lang[EXT[ext]] += 1
        if fn in MANIFESTS:
            out["manifests"].append(p)
            if fn == "package.json":
                try:
                    out["package_scripts"][p] = json.load(open(p, encoding="utf-8")).get("scripts", {})
                except Exception:
                    pass
        if CONFIG_RE.match(fn) or CONFIG_RE.match(p.replace(os.sep, "/")):
            out["configs"].append(p)
        if TEST_RE.match(fn):
            out["test_configs"].append(p)
        if re.search(r"(\.|_)(test|spec)\.[a-z]+$|^test_.*\.py$", fn) or "__tests__" in parts:
            out["test_files_count"] += 1
        if (parts[:1] == [".github"] and "workflows" in parts) or fn in (".gitlab-ci.yml", "Jenkinsfile", "azure-pipelines.yml", "bitbucket-pipelines.yml"):
            out["ci"].append(p)
        is_doc = ext in (".md", ".mdx", ".txt", ".rst", "") or fn.lower() in (".cursorrules",)
        if parts[:2] == [".claude", "skills"] and re.search(r"(review-|stack-detection|debate-protocol|verification-protocol|report-builder|implementation-pack)", p):
            is_doc = False
        if (CONTEXT_RE.match(fn) and is_doc) or (is_doc and any(x in ("docs", "doc", "adr", "adrs") for x in [q.lower() for q in parts]) and ext in (".md", ".mdx", ".txt")):
            out["context_files"].append(p)
        if parts[:1] == [".claude"] and not re.search(r"(review-|review_committee|skills[\\/](review-|stack-detection|debate-protocol|verification-protocol|report-builder|implementation-pack))", p):
            out["claude_dir"].append(p)
out["size"]["by_language"] = dict(lang.most_common())
out["size"]["by_top_folder"] = dict(top.most_common(25))
for k in ("context_files", "configs", "claude_dir"):
    out[k] = sorted(set(out[k]))[:300]
print(json.dumps(out, indent=2))
