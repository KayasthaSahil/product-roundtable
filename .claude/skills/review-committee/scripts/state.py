#!/usr/bin/env python3
"""Review state machine. Run from the repo root.

  state.py init                 create .review/ structure, status=active, phase=P0, record base commit
  state.py status               print current state
  state.py start <phase>        mark phase in progress (P0..P7)
  state.py advance [--force]    mark current step complete and move to the next (P6 -> review complete); P5/P6 run ticket-check/trace-check first.
                                P4 (debate) is skipped unless `debate` was requested.
  state.py debate               opt in to the P4 debate step (allowed after P3 and before P5 completes)
  state.py benchmark            opt in to the P1 competitive benchmark (CMP)
  state.py depth [lite|full]    review depth for P2: no argument = decide from code size (lite when <= 5000 lines of source code, from the Atlas)
  state.py dispatch <ROLE> "<task>" [--result complete|partial|blocked] [--bundle-count N] [--retry-of ID] [--input-tokens N --output-tokens N] [--total-tokens N] [--context-profile PROFILE]
  state.py skip <ROLE> "<reason>"                                      log an intentional skip
  state.py dispatch-metrics [--json]                                   summarise calls, skips, retries and reported tokens
  state.py roles <ROLE,ROLE,...>   set the active roles (from review-scope)
  state.py pause | resume       pause/resume (guards are off while paused or complete)
  state.py rereview             open P7 to review externally implemented changes
  state.py set <key> <value>    set a top-level key (e.g. dev_server_url)
"""
import json, os, subprocess, sys, datetime

PHASES = ["P0", "P1", "P2", "P3", "P4", "P5", "P6", "P7"]
# User-facing stages group the internal steps. P4 (debate) and P7 (re-review) are optional.
STAGES = [("1/3 Understand", ["P0", "P1"]), ("2/3 Review", ["P2", "P3"]), ("3/3 Plan", ["P4", "P5", "P6"])]
STAGE_END = {"P1": "Stage 1/3 (Understand)", "P3": "Stage 2/3 (Review)", "P6": "Stage 3/3 (Plan)"}
def stage_of(ph):
    return next((n for n, steps in STAGES if ph in steps), "Optional re-review")
REQUIRED_ROLES = ["CHR", "PMV", "PMS", "CMP", "ARC", "FE", "BE", "AI", "MED", "VIS", "UX", "XAI", "DOC", "QA", "CPE", "RED", "VER", "SCR"]
DIRS = ["brief", "findings", "verification", "decisions", "gate", "report", "implementation",
        "runs", "evidence", "codebase-atlas/discrepancies"]  # others (debates, rereview, ...) are created when first used
ROOT = os.getcwd()
R = os.path.join(ROOT, ".review")
P = os.path.join(R, "state.json")

def now():
    return datetime.datetime.now().isoformat(timespec="seconds")

def git(*a):
    try:
        return subprocess.check_output(["git", *a], stderr=subprocess.DEVNULL, text=True).strip()
    except Exception:
        return "unknown"

def load():
    if not os.path.exists(P):
        sys.exit("No review found. Run: state.py init")
    return json.load(open(P, encoding="utf-8"))

def save(s):
    s["updated_at"] = now()
    json.dump(s, open(P, "w", encoding="utf-8"), indent=2)

def cleanup_review_workspace():
    """Delete bulky, regenerable scratch at the end of the review (never findings, decisions, tickets or cited evidence)."""
    import glob, shutil
    for pat in ("runs/env", "runs/venv*", "runs/tmp", "evidence/screenshots/page-*.yml", "evidence/screenshots/console-*.log"):
        for p in glob.glob(os.path.join(R, pat)):
            shutil.rmtree(p, ignore_errors=True) if os.path.isdir(p) else os.remove(p)

cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
if cmd == "init":
    if os.path.exists(P):
        sys.exit("A review already exists (.review/state.json). Use status / resume / rereview.")
    for d in DIRS:
        os.makedirs(os.path.join(R, d), exist_ok=True)
    s = {"status": "active", "cycle": 1, "phase": "P0", "base_commit": git("rev-parse", "HEAD"),
         "started_at": now(), "active_roles": REQUIRED_ROLES.copy(), "dev_server_url": None, "debate": False, "benchmark": False, "depth": "full",
         "phases": {p: {"status": "pending"} for p in PHASES}, "dispatches": [], "dispatch_skips": []}
    s["phases"]["P0"] = {"status": "in_progress", "started_at": now()}
    save(s)
    json.dump({"limit": 5, "runs": []}, open(os.path.join(R, "runs", "targeted-tests.json"), "w"), indent=2)
    json.dump({"runs": []}, open(os.path.join(R, "runs", "run-log.json"), "w"), indent=2)
    gi = os.path.join(R, ".gitignore")
    open(gi, "w").write("runs/\nevidence/\n")
    print("Review initialised. Phase P0 in progress. Guards are ACTIVE.")
elif cmd == "status":
    s = load()
    print(f"Status: {s['status']} · Cycle {s['cycle']} · Stage {stage_of(s['phase'])} · Step {s['phase']} · Base commit {s['base_commit'][:10]}")
    print(f"Options: debate={'on' if s.get('debate') else 'off'} · competitive benchmark={'on' if s.get('benchmark') else 'off'}")
    print("Phases: " + "  ".join(f"{p}:{s['phases'][p]['status']}" for p in PHASES))
    print("Active roles: " + (", ".join(s["active_roles"]) or "(not set)"))
    last = s["dispatches"][-8:]
    if last:
        print("Recent dispatches:")
        for d in last:
            print(f"  {d['at']} {d['phase']} {d['role']}: {d['task']} -> {d.get('result', '?')}")
elif cmd == "start":
    s = load(); ph = sys.argv[2]
    s["phase"] = ph; s["phases"][ph] = {"status": "in_progress", "started_at": now()}; save(s); print(f"{ph} in progress")
elif cmd == "advance":
    s = load(); ph = s["phase"]
    # Deterministic gates: P5 needs ticket-check; P6 needs ticket-check + trace-check. --force is logged.
    gates = {"P5": ["ticket-check.py"], "P6": ["ticket-check.py", "trace-check.py"]}.get(ph, [])
    if s.get("phases", {}).get(ph, {}).get("gate_forced") is None:
        for g in gates:
            r = subprocess.run([sys.executable, os.path.join(ROOT, ".claude", "skills", "implementation-pack", "scripts", g)], capture_output=True, text=True)
            if r.returncode:
                if "--force" in sys.argv:
                    s["phases"][ph]["gate_forced"] = f"{g} failed; forced {now()}"
                else:
                    sys.exit(f"Cannot advance {ph}: {g} failed. {(r.stdout or r.stderr).strip()[:1500]} -- Fix the records, or use --force (logged) only with a recorded reason.")
    s["phases"][ph]["status"] = "complete"; s["phases"][ph]["completed_at"] = now()
    if ph == "P6":
        cleanup_review_workspace()
        s["status"] = "complete"; s["completed_at"] = now()
        print("P6 complete. REVIEW COMPLETE. Guards are now OFF. Report and implementation pack are final.")
    elif ph == "P7":
        s["status"] = "complete"; print("P7 complete. Re-review finished. Guards OFF.")
    else:
        nxt = PHASES[PHASES.index(ph) + 1]
        if nxt == "P4" and not s.get("debate"):
            s["phases"]["P4"] = {"status": "skipped", "reason": "debate not requested; Chair decides disagreements in P5"}
            nxt = "P5"
        s["phase"] = nxt; s["phases"][nxt] = {"status": "ready"}
        print(f"{ph} complete. Next step: {nxt}")
        if ph in STAGE_END:
            print(f"{STAGE_END[ph]} COMPLETE. Tell the user and stop; `next` starts the following stage.")
    save(s)
elif cmd == "dispatch":
    s = load(); role, task = sys.argv[2], sys.argv[3]
    args = sys.argv[4:]
    def opt(name, default=None):
        return args[args.index(name) + 1] if name in args and args.index(name) + 1 < len(args) else default
    record = {"id": f"DSP-{len(s.get('dispatches', [])) + 1:04d}", "at": now(), "phase": s["phase"],
              "cycle": s.get("cycle", 1), "role": role, "task": task, "result": opt("--result", "dispatched"),
              "bundle_count": int(opt("--bundle-count", "1")), "retry_of": opt("--retry-of"),
              "context_profile": opt("--context-profile")}
    for flag, key in (("--input-tokens", "input_tokens"), ("--output-tokens", "output_tokens"), ("--total-tokens", "total_tokens")):
        value = opt(flag)
        if value is not None:
            try: record[key] = int(value)
            except ValueError: sys.exit(f"{flag} must be an integer reported by the platform")
    if record["bundle_count"] < 1: sys.exit("--bundle-count must be at least 1")
    s.setdefault("dispatches", []).append(record); save(s); print(record["id"])
elif cmd == "skip":
    s = load(); role, reason = sys.argv[2], sys.argv[3]
    if not reason.strip(): sys.exit("Skip reason must not be empty")
    low_reason = reason.lower()
    if any(term in low_reason for term in ("atlas", "token saving", "save tokens", "reduce token", "resource saving", "cost saving", "reduce agent", "agent count")):
        sys.exit("Invalid phase skip: SCIS or resource/token savings cannot be used to skip a specialist. Use the specialist-dispatch-matrix.md applicability trigger.")
    s.setdefault("dispatch_skips", []).append({"at": now(), "phase": s["phase"], "cycle": s.get("cycle", 1), "role": role, "reason": reason})
    save(s); print("skip logged")
elif cmd == "dispatch-metrics":
    s = load(); cycle = s.get("cycle", 1)
    ds = [d for d in s.get("dispatches", []) if d.get("cycle", 1) == cycle]
    skips = [d for d in s.get("dispatch_skips", []) if d.get("cycle", 1) == cycle]
    known_in = [d["input_tokens"] for d in ds if isinstance(d.get("input_tokens"), int)]
    known_out = [d["output_tokens"] for d in ds if isinstance(d.get("output_tokens"), int)]
    phase = s.get("phase", "P0")
    phase_ds = [d for d in ds if d.get("phase") == phase]
    phase_skips = [d for d in skips if d.get("phase") == phase]
    phase_in = [d["input_tokens"] for d in phase_ds if isinstance(d.get("input_tokens"), int)]
    phase_out = [d["output_tokens"] for d in phase_ds if isinstance(d.get("output_tokens"), int)]
    phase_total = [d["total_tokens"] for d in phase_ds if isinstance(d.get("total_tokens"), int)]
    all_total = [d["total_tokens"] for d in ds if isinstance(d.get("total_tokens"), int)]
    phase_summary = {"dispatch_count": len(phase_ds), "skip_count": len(phase_skips),
                     "retry_count": sum(1 for d in phase_ds if d.get("retry_of")),
                     "bundled_assignments": sum(d.get("bundle_count", 1) for d in phase_ds),
                     "reported_input_tokens": sum(phase_in) if phase_in else None,
                     "reported_output_tokens": sum(phase_out) if phase_out else None,
                     "reported_total_tokens": sum(phase_total) if phase_total else None}
    s.setdefault("phases", {}).setdefault(phase, {"status": "in_progress"})["dispatch_metrics"] = phase_summary
    save(s)
    summary = {"cycle": cycle, **phase_summary, "cycle_total_tokens": sum(all_total) if all_total else None,
               "token_usage_records": sum(1 for d in ds if "input_tokens" in d or "output_tokens" in d),
               "by_phase": {ph: {"dispatches": sum(1 for d in ds if d.get("phase") == ph),
                                  "skips": sum(1 for d in skips if d.get("phase") == ph)} for ph in PHASES}}
    if "--json" in sys.argv:
        print(json.dumps(summary, indent=2))
    else:
        print(f"Dispatch metrics · cycle {cycle}")
        print(f"Calls: {summary['dispatch_count']} · bundled assignments: {summary['bundled_assignments']} · skips: {summary['skip_count']} · retries: {summary['retry_count']}")
        print("Reported tokens: input=" + (str(summary["reported_input_tokens"]) if summary["reported_input_tokens"] is not None else "unknown") +
              " · output=" + (str(summary["reported_output_tokens"]) if summary["reported_output_tokens"] is not None else "unknown"))
        print("Total reported tokens: this step=" + (str(phase_summary["reported_total_tokens"]) if phase_summary["reported_total_tokens"] is not None else "unknown") +
              " · whole review so far=" + (str(summary["cycle_total_tokens"]) if summary["cycle_total_tokens"] is not None else "unknown"))
        for ph, values in summary["by_phase"].items():
            if values["dispatches"] or values["skips"]: print(f"  {ph}: {values['dispatches']} calls, {values['skips']} skips")
elif cmd == "roles":
    s = load(); requested = [r.strip() for r in sys.argv[2].split(",") if r.strip()]
    missing = [r for r in REQUIRED_ROLES if r not in requested]
    unknown = [r for r in requested if r not in REQUIRED_ROLES]
    if missing or unknown:
        sys.exit("Role inventory rejected. All 18 committee roles must remain active/callable. Missing: " + ",".join(missing) + "; unknown: " + ",".join(unknown))
    s["active_roles"] = REQUIRED_ROLES.copy(); save(s); print("all 18 committee roles active/callable; phase dispatch remains governed by specialist-dispatch-matrix.md")
elif cmd == "debate":
    s = load()
    if s["phases"]["P3"].get("status") != "complete" or s["phases"]["P5"].get("status") == "complete":
        sys.exit("Debate can be requested after P3 (Review stage) is complete and before P5 completes.")
    s["debate"] = True; s["phase"] = "P4"; s["phases"]["P4"] = {"status": "in_progress", "started_at": now()}
    if s["phases"]["P5"].get("status") in ("ready", "in_progress"): s["phases"]["P5"] = {"status": "pending"}
    save(s); print("Debate enabled. P4 in progress; run it, then `advance` continues to P5.")
elif cmd == "depth":
    s = load()
    if len(sys.argv) > 2:
        if sys.argv[2] not in ("lite", "full"): sys.exit("depth must be lite or full")
        s["depth"] = sys.argv[2]
    else:
        code_ext = (".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".java", ".kt", ".go", ".rs", ".rb", ".php", ".cs", ".vue", ".svelte", ".sql", ".html", ".css", ".scss")
        loc = None
        try:
            src = json.load(open(os.path.join(R, "codebase-atlas", "evidence", "source-index.json"), encoding="utf-8"))["sources"]
            loc = sum(x.get("line_count", 0) for x in src if x["path"].lower().endswith(code_ext))
        except Exception:
            try:  # fallback: file count from the stack profile (<= 50 files)
                loc = 0 if json.load(open(os.path.join(R, "brief", "stack-profile.json"), encoding="utf-8"))["size"]["files"] <= 50 else 10**9
            except Exception:
                loc = None
        s["depth"] = "lite" if isinstance(loc, int) and loc <= 5000 else "full"
        print(f"Source lines: {loc}")
    save(s); print(f"Review depth: {s['depth']}")
elif cmd == "benchmark":
    s = load(); s["benchmark"] = True; save(s); print("Competitive benchmark enabled for P1 (CMP).")
elif cmd in ("pause", "resume"):
    s = load()
    if s["status"] == "complete" and cmd == "resume":
        sys.exit("Review is complete. Use rereview for P7.")
    s["status"] = "paused" if cmd == "pause" else "active"; save(s); print(f"Review {s['status']}. Guards {'OFF' if cmd == 'pause' else 'ON'}.")
elif cmd == "rereview":
    s = load(); s["cycle"] += 1; s["status"] = "active"; s["phase"] = "P7"
    os.makedirs(os.path.join(R, "rereview"), exist_ok=True)
    s["phases"]["P7"] = {"status": "in_progress", "started_at": now(), "head_commit": git("rev-parse", "HEAD")}
    save(s); print(f"P7 re-review opened (cycle {s['cycle']}). Base commit {s['base_commit'][:10]} -> HEAD {s['phases']['P7']['head_commit'][:10]}")
elif cmd == "set":
    s = load(); s[sys.argv[2]] = sys.argv[3]; save(s); print("set")
else:
    print(__doc__)
