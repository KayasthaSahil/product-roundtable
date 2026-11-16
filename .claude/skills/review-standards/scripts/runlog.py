#!/usr/bin/env python3
"""Shared run log for long-running or paid commands (standards §10).

  python3 runlog.py find "<command>"            -> prints a prior run on the current commit, exit 0 if found, 1 if not
  python3 runlog.py add --cmd "<command>" --kind <setup|build|render|ai-generation|targeted-test|server|other>
                        --role <CODE> --exit <code> --duration <seconds> [--output <path>] [--note "<text>"]
  python3 runlog.py list [--kind <kind>]
"""
import argparse, json, os, subprocess, sys, datetime

def root():
    d = os.getcwd()
    while d != os.path.dirname(d):
        if os.path.isdir(os.path.join(d, ".review")):
            return d
        d = os.path.dirname(d)
    return os.getcwd()

LOG = os.path.join(root(), ".review", "runs", "run-log.json")

def commit():
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL, text=True).strip()
    except Exception:
        return "unknown"

def load():
    if os.path.exists(LOG):
        return json.load(open(LOG, encoding="utf-8"))
    return {"runs": []}

def save(d):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    json.dump(d, open(LOG, "w", encoding="utf-8"), indent=2)

ap = argparse.ArgumentParser()
ap.add_argument("action", choices=["find", "add", "list"])
ap.add_argument("command", nargs="?")
ap.add_argument("--cmd"); ap.add_argument("--kind", default="other"); ap.add_argument("--role", default="CHR")
ap.add_argument("--exit", type=int, default=0); ap.add_argument("--duration", type=float, default=0)
ap.add_argument("--output", default=""); ap.add_argument("--note", default="")
a = ap.parse_args()
d = load()
if a.action == "find":
    c = commit()
    hits = [r for r in d["runs"] if r["command"] == a.command and r["commit"] == c and r["exit"] == 0]
    if hits:
        print(json.dumps(hits[-1], indent=2)); sys.exit(0)
    print("No successful run of this command on the current commit."); sys.exit(1)
elif a.action == "add":
    d["runs"].append({"command": a.cmd, "kind": a.kind, "role": a.role, "commit": commit(),
                      "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
                      "duration_s": a.duration, "exit": a.exit, "output": a.output, "note": a.note})
    save(d); print("logged")
else:
    for r in d["runs"]:
        if a.kind in ("other",) and not sys.argv.count("--kind") or r["kind"] == a.kind:
            print(f"{r['timestamp']} [{r['kind']}] {r['role']} exit={r['exit']} {r['duration_s']}s :: {r['command']} -> {r['output']}")
