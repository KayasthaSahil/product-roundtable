#!/usr/bin/env python3
"""Record the owner's explicit plan approval for several tickets at once (run from repo root).

  approve-plan.py --by "<owner name>" TASK-001 TASK-004     named tickets
  approve-plan.py --by "<owner name>" WS-02                 every eligible ticket in a workstream
  approve-plan.py --by "<owner name>" all-awaiting          every eligible ticket

Only run this after the user explicitly asked for these approvals. Approval covers inclusion in the
plan only; it never authorises implementation. Eligible = status AWAITING_OWNER_APPROVAL, readiness
Go / Go with conditions, no open conditions. Blocked, deferred or review-required tickets are skipped
and reported. The tickets are re-checked with ticket-check.py; on failure every file is restored.
"""
import datetime, glob, json, os, subprocess, sys

TICKETS = ".review/implementation/tickets"
HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    args = sys.argv[1:]
    if "--by" not in args or args.index("--by") + 1 >= len(args):
        sys.exit(__doc__)
    i = args.index("--by")
    by = args[i + 1].strip()
    selectors = [a for k, a in enumerate(args) if k not in (i, i + 1)]
    if not by or not selectors:
        sys.exit(__doc__)

    originals, tickets = {}, {}
    for path in sorted(glob.glob(f"{TICKETS}/TASK-*.json")):
        text = open(path, encoding="utf-8").read()
        originals[path] = text
        t = json.loads(text)
        tickets[t["id"]] = (path, t)

    chosen = []
    for s in selectors:
        if s == "all-awaiting":
            chosen += list(tickets)
        elif s.startswith("WS-"):
            chosen += [tid for tid, (_, t) in tickets.items() if t.get("workstream") == s]
        elif s in tickets:
            chosen.append(s)
        else:
            sys.exit(f"Unknown ticket or workstream: {s}")
    chosen = list(dict.fromkeys(chosen))

    now = datetime.date.today().isoformat()
    approved, skipped = [], []
    for tid in chosen:
        path, t = tickets[tid]
        r = t.get("readiness", {})
        if t.get("status") != "AWAITING_OWNER_APPROVAL":
            skipped.append((tid, f"status is {t.get('status')}"))
        elif r.get("verdict") not in ("Go", "Go with conditions") or r.get("open_conditions"):
            skipped.append((tid, "readiness not Go or has open conditions"))
        else:
            t["status"] = "APPROVED"
            t["owner_approval"] = {"status": "approved", "approved_by": by, "approved_at": now,
                                   "note": "Approval applies to inclusion in the plan only; it does not authorise implementation."}
            t.setdefault("quality_review", {})["reviewed_at"] = now
            open(path, "w", encoding="utf-8").write(json.dumps(t, indent=2, ensure_ascii=False) + "\n")
            approved.append(tid)

    if approved:
        check = subprocess.run([sys.executable, os.path.join(HERE, "ticket-check.py")], capture_output=True, text=True)
        if check.returncode:
            for path, text in originals.items():
                open(path, "w", encoding="utf-8").write(text)
            sys.exit("ticket-check failed, nothing was changed:\n" + (check.stdout or check.stderr)[:1500])
        subprocess.run([sys.executable, os.path.join(HERE, "build-pack-views.py"), "--phase", "P6"], capture_output=True, text=True)
    print(f"APPROVED ({len(approved)}): " + (", ".join(approved) or "none"))
    for tid, why in skipped:
        print(f"SKIPPED {tid}: {why}")


if __name__ == "__main__":
    main()
