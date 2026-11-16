#!/usr/bin/env python3
"""PreToolUse guard for Bash during a review.

Blocks: full test-suite runs, destructive / git-mutating commands, dependency changes,
secret printing, and targeted test runs beyond the budget (5 per cycle, <=5 min each).
Extra patterns come from .review/brief/stack-profile.json:
  "forbidden_commands":   [regex, ...]  always blocked
  "targeted_test_runner": [regex, ...]  commands recognised as test runs
"""
import datetime, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import guards_active, read_event, deny, allow, review_dir, load_stack_profile

ev = read_event()
if not guards_active():
    allow()
ti = ev.get("tool_input", {}) or {}
cmd = (ti.get("command") or "").strip()
if not cmd:
    allow()
low = cmd.lower()
prof = load_stack_profile()

# 1. Destructive & git-mutating
DESTRUCTIVE = [
    (r"\bgit\s+(push|commit|reset|clean|checkout|switch|restore|stash|rebase|merge|cherry-pick|revert|am|apply|tag|branch\s+-[dD]|rm|mv)\b", "git commands that change the repository"),
    (r"\brm\s+(-[a-z]*r[a-z]*f|-[a-z]*f[a-z]*r|-r|--recursive)\b(?!.*\.review)", "recursive deletion outside .review/"),
    (r"\b(drop\s+(database|table|schema)|truncate\s+table)\b", "destructive database statements"),
    (r"\b(migrate\s+reset|db:reset|db:drop|prisma\s+migrate\s+reset|flushall|flushdb)\b", "database reset"),
    (r"\b(mkfs|dd\s+if=|shutdown|reboot|chmod\s+-R\s+777)\b", "system-level destructive commands"),
    (r"\b(npm|pnpm|yarn|bun)\s+(publish|deploy)\b|\bvercel\b|\bnetlify\s+deploy\b|\bfly\s+deploy\b", "publishing / deploying"),
    (r"\b(npm|pnpm|bun)\s+(i|install|add|remove|uninstall|update|upgrade)\s+[^-\s]", "changing dependencies (plain install with no package name is allowed)"),
    (r"\byarn\s+(add|remove|upgrade)\b|\bpip3?\s+(install|uninstall)\s+(?!-r\b)(?!-e\s+\.)[^-\s]|\bpoetry\s+(add|remove)\b|\buv\s+(add|remove)\b|\bcargo\s+(add|remove)\b|\bgo\s+get\b", "changing dependencies"),
]
for pat, why in DESTRUCTIVE:
    if re.search(pat, low):
        deny(f"Not allowed during the review: {why}. Command: {cmd}")

# 2. Secrets
if re.search(r"(^|[\s;&|])(printenv|env)(\s*$|\s*[;&|])|\bset\s*$", low) or \
   re.search(r"\b(cat|less|more|head|tail|type|bat|grep|rg|sed|awk)\b[^|;&]*\.env(?!\.(example|sample|template|dist))\b", low) or \
   re.search(r"echo\s+[^|;&]*\$\{?[a-z0-9_]*(key|secret|token|password)", low):
    deny("Printing secrets or environment values is not allowed. Cite where a secret lives, never its value.")

# 3. Stack-profile forbidden commands (full test suite etc.)
for pat in prof.get("forbidden_commands", []):
    try:
        if re.search(pat, cmd, re.I):
            deny(f"Command matches a forbidden pattern from stack-profile.json ({pat}). "
                 "The full test suite takes hours and is never run during the review; review tests statically.")
    except re.error:
        pass

# 4. Test runs: full suite blocked; targeted runs budgeted
RUNNERS = [r"\b(npm|pnpm|yarn|bun)\s+(run\s+)?test(:[\w-]+)?\b", r"\bnpx\s+(jest|vitest|playwright\s+test|mocha|cypress\s+run)\b",
           r"(^|[\s;&|/])(jest|vitest|mocha|ava|pytest|py\.test|phpunit|rspec)\b", r"\bpython3?\s+-m\s+(pytest|unittest)\b", r"\bmanage\.py\s+test\b", r"\breact-scripts\s+test\b", r"(^|[\s;&|/])(tox|nox)\b",
           r"\b(mvn|mvnw|\./mvnw)\b.*\b(test|verify)\b", r"\b(gradle|gradlew|\./gradlew)\b.*\btest\b", r"\bgo\s+test\b",
           r"\bcargo\s+test\b", r"\bdotnet\s+test\b", r"\bplaywright\s+test\b", r"\bcypress\s+run\b"] + prof.get("targeted_test_runner", [])
is_test = any(re.search(p, low) for p in RUNNERS)
if is_test:
    targeted = bool(re.search(r"(\s[\w./\\-]+\.(test|spec)\.[jt]sx?\b|\s[\w./\\-]*(test|spec)s?[\w./\\-]*\.(py|[jt]sx?|go|rb|java|kt)\b|"
                              r"\s-k\s|\s-t\s|--testNamePattern|--grep\s|::|-Dtest=|--tests\s|\s-run\s|--filter\s|--spec\s)", cmd))
    if re.search(r"\s\./\.\.\.|\s\.\.\.(\s|$)", cmd):
        targeted = False
    if not targeted:
        deny("Full test-suite runs are forbidden during the review (full suites can take hours). "
             "Review tests statically, reuse existing CI results, or run ONE targeted test file/case if it is the only way to verify a finding.")
    if "--watch" in low or " -w " in f" {low} ":
        deny("Watch mode is not allowed.")
    t = ti.get("timeout")
    if t is None or int(t) > 300000:
        deny("Targeted test runs must set the Bash timeout to at most 300000 ms (5 minutes).")
    budget_file = os.path.join(review_dir(), "runs", "targeted-tests.json")
    try:
        data = json.load(open(budget_file, encoding="utf-8"))
    except Exception:
        data = {"limit": 5, "runs": []}
    try:
        cycle = json.load(open(os.path.join(review_dir(), "state.json"), encoding="utf-8")).get("cycle", 1)
    except Exception:
        cycle = 1
    used = [r for r in data["runs"] if r.get("cycle", 1) == cycle]
    if len(used) >= data.get("limit", 5):
        deny(f"Targeted test budget exhausted ({len(used)}/{data.get('limit', 5)} this cycle). Verify statically instead and lower confidence if needed.")
    data["runs"].append({"cycle": cycle, "command": cmd, "at": datetime.datetime.now().isoformat(timespec="seconds")})
    os.makedirs(os.path.dirname(budget_file), exist_ok=True)
    json.dump(data, open(budget_file, "w", encoding="utf-8"), indent=2)
allow()
