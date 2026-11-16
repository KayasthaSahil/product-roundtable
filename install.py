#!/usr/bin/env python3
"""Install (or update) the Product Review Committee into the current project.

  curl -fsSL https://raw.githubusercontent.com/KayasthaSahil/product-roundtable/main/install.py | python3 -
  irm https://raw.githubusercontent.com/KayasthaSahil/product-roundtable/main/install.py | python -

Copies the committee's agents, skills and hooks into ./.claude, and merges (never overwrites)
your existing .claude/settings.json hooks and .mcp.json. Safe to re-run to update.
Testing: python3 install.py --from <local checkout>
"""
import io, json, shutil, sys, tempfile, urllib.request, zipfile
from pathlib import Path

ZIP = "https://github.com/KayasthaSahil/product-roundtable/archive/refs/heads/main.zip"


def load(p):
    try:
        return json.loads(p.read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        return {}


def save(p, doc):
    p.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")


def source():
    if "--from" in sys.argv:
        return Path(sys.argv[sys.argv.index("--from") + 1]).resolve()
    print("Downloading product-roundtable ...")
    tmp = Path(tempfile.mkdtemp())
    with urllib.request.urlopen(ZIP, timeout=60) as r:
        zipfile.ZipFile(io.BytesIO(r.read())).extractall(tmp)
    return next(tmp.iterdir())


def main():
    src, dst = source() / ".claude", Path.cwd() / ".claude"
    (dst / "agents").mkdir(parents=True, exist_ok=True)
    for f in (src / "agents").glob("review-*.md"):
        shutil.copy2(f, dst / "agents" / f.name)
    for name in ("skills", "hooks"):
        for d in (src / name).iterdir():
            target = dst / name / d.name
            if d.is_dir():
                shutil.rmtree(target, ignore_errors=True)
                shutil.copytree(d, target, ignore=shutil.ignore_patterns("__pycache__"))
            else:
                (dst / name).mkdir(parents=True, exist_ok=True)
                shutil.copy2(d, target)

    # Merge hooks into settings.json without touching anything else.
    settings_path = dst / "settings.json"
    settings, ours = load(settings_path), load(src / "settings.json")
    hooks = settings.setdefault("hooks", {})
    for event, entries in ours.get("hooks", {}).items():
        mine = hooks.setdefault(event, [])
        have = json.dumps(mine)
        mine += [e for e in entries if json.dumps(e["hooks"][0]["command"]) not in have]
    save(settings_path, settings)

    # Merge the Playwright MCP server (used by the UI reviewers).
    mcp_path = Path.cwd() / ".mcp.json"
    mcp = load(mcp_path)
    mcp.setdefault("mcpServers", {}).setdefault("playwright", load(source_mcp(src))["mcpServers"]["playwright"])
    save(mcp_path, mcp)

    print("Installed. Open Claude Code in this folder and run:  /review-committee start")


def source_mcp(src):
    return src.parent / ".mcp.json"


main()
