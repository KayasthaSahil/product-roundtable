#!/usr/bin/env python3
"""Validate the ticket-first implementation planning pack (run from repo root)."""
import glob
import json
import os
import re
import subprocess
import sys

R = ".review"
I = f"{R}/implementation"
# Only generated views are required. REFERENCES/* exist only when a ticket needs them (no empty or speculative documents).
REQ = [
    "START-HERE.md",
    "PLAN/roadmap.md",
    "DECISIONS/decision-log.md",
    "tickets/INDEX.md",
]
def load(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def read(path):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ""

def main():
    errors = []
    for rel in REQ:
        path = f"{I}/{rel}"
        if not os.path.isfile(path):
            errors.append(f"missing required pack document: {rel}")
        elif "<!-- fill -->" in read(path):
            errors.append(f"unfilled section(s) in {rel}")


    # Collect canonical review IDs.
    ids = set()
    for path in glob.glob(f"{R}/findings/*.json"):
        for item in load(path, {}).get("findings", []):
            if item.get("id"):
                ids.add(item["id"])

    decisions_doc = load(f"{R}/decisions/decision-log.json", {"decisions": []})
    decisions = decisions_doc.get("decisions", [])
    ids.update(d.get("id") for d in decisions if d.get("id"))

    for path in glob.glob(f"{R}/debates/DBT-*/dispute.json"):
        ids.add(os.path.basename(os.path.dirname(path)))

    roadmap = load(f"{R}/decisions/roadmap.json", {"workstreams": []})
    workstreams = roadmap.get("workstreams", [])
    ids.update(w.get("id") for w in workstreams if w.get("id"))

    tickets = {}
    for path in glob.glob(f"{I}/tickets/TASK-*.json"):
        doc = load(path, None)
        if not isinstance(doc, dict):
            errors.append(f"cannot parse canonical ticket: {path}")
            continue
        tid = doc.get("id")
        if not tid:
            errors.append(f"ticket has no id: {path}")
            continue
        ids.add(tid)
        tickets[tid] = doc
        if os.path.basename(path) != tid + ".json":
            errors.append(f"ticket filename must match its id: {path}")

    decision_log = read(f"{I}/DECISIONS/decision-log.md")
    ticket_index = read(f"{I}/tickets/INDEX.md")
    roadmap_md = read(f"{I}/PLAN/roadmap.md")
    for d in decisions:
        did = d.get("id")
        if d.get("disposition") in ("Accepted", "Accepted with modifications"):
            if not d.get("workstream"):
                errors.append(f"{did} accepted but has no workstream")
            if did and did not in decision_log:
                errors.append(f"{did} accepted but is absent from DECISIONS/decision-log.md")
            if d.get("implementation_required") is True:
                for tid in d.get("ticket_ids", []):
                    if tid not in tickets:
                        errors.append(f"{did} references missing ticket {tid}")
                    elif did not in tickets[tid].get("decisions", []):
                        errors.append(f"{did} and {tid} do not link to each other")
            if d.get("implementation_required") is False and not d.get("no_ticket_reason", "").strip():
                errors.append(f"{did} says no implementation ticket is required but gives no reason")

    for ws in workstreams:
        wid = ws.get("id")
        if wid and wid not in roadmap_md:
            errors.append(f"{wid} from roadmap.json is absent from PLAN/roadmap.md")

    for tid in tickets:
        if tid not in ticket_index:
            errors.append(f"{tid} is absent from generated tickets/INDEX.md")

    # Validate all IDs mentioned in Markdown against canonical review/ticket records.
    pattern = re.compile(r"\b(SUT-[A-Z]{2,3}-\d{3}|DEC-\d{3}|DBT-\d{3}|WS-\d{2}|TASK-\d{3})\b")
    for path in glob.glob(f"{I}/**/*.md", recursive=True):
        for ref in set(pattern.findall(read(path))):
            if ref not in ids:
                errors.append(f"{os.path.relpath(path, I)} references unknown ID {ref}")

    # Orphan references are waste: warn when no ticket or roadmap entry names the file (delete it or link it).
    linked_text = read(f"{R}/decisions/roadmap.json") + "".join(json.dumps(t) for t in tickets.values())
    for path in glob.glob(f"{I}/REFERENCES/*.md"):
        name = os.path.basename(path)
        if name != "risk-register.md" and name not in linked_text:
            print(f"WARNING: REFERENCES/{name} is not linked from any ticket or workstream; link it or delete it")

    checker = ".claude/skills/implementation-pack/scripts/ticket-check.py"
    if os.path.isfile(checker):
        result = subprocess.run([sys.executable, checker], capture_output=True, text=True)
        if result.returncode:
            errors.append("ticket-check failed: " + (result.stdout.strip() or result.stderr.strip()))

    if errors:
        print(f"TRACE CHECK FAILED ({len(errors)} issue(s))")
        for error in errors[:100]:
            print(" -", error)
        return 1

    print(f"TRACE CHECK PASSED — {len(decisions)} decisions, {len(workstreams)} workstreams, {len(tickets)} tickets; ticket-first pack complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
