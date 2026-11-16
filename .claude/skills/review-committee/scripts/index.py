#!/usr/bin/env python3
"""Compact index of findings so the Chair never loads raw files into context. Run from repo root.

  index.py                      one line per finding: id | sev | category | area | verdict | disposition | title
  index.py --role BE            filter by role      --severity High   --verdict verified   --undecided
  index.py --counts             counts by severity / category / role / verdict
  index.py --show FND-BE-004    print one finding in full
"""
import glob, json, os, sys
from collections import Counter

def load(p, default):
    try:
        return json.load(open(p, encoding="utf-8"))
    except Exception:
        return default

F = []
for p in sorted(glob.glob(".review/findings/*.json")):
    F += load(p, {}).get("findings", [])
V = {v["finding_id"]: v for v in load(".review/verification/verification-log.json", {"verdicts": []})["verdicts"]}
D = {}
for d in load(".review/decisions/decision-log.json", {"decisions": []})["decisions"]:
    for f in d.get("findings", []):
        D[f] = d
a = sys.argv[1:]
def opt(k):
    return a[a.index(k) + 1] if k in a else None
if "--show" in a:
    fid = opt("--show")
    for f in F:
        if f["id"] == fid:
            print(json.dumps(f, indent=2, ensure_ascii=False))
            if fid in V: print("VERDICT:", json.dumps(V[fid], ensure_ascii=False))
            if fid in D: print("DECISION:", D[fid]["id"], D[fid]["disposition"])
    sys.exit()
rows = []
for f in F:
    rc = (V.get(f["id"], {}).get("reclassified") or {})
    if rc.get("severity"): f["severity"] = rc["severity"]
    if rc.get("category"): f["category"] = rc["category"]
    sev = f.get("severity") or ("STRENGTH" if f.get("kind") == "strength" else "-")
    ver = V.get(f["id"], {}).get("verdict", "-")
    dec = D.get(f["id"], {}).get("disposition", "-")
    if opt("--role") and f.get("role") != opt("--role"): continue
    if opt("--severity") and sev != opt("--severity"): continue
    if opt("--verdict") and ver != opt("--verdict"): continue
    if "--undecided" in a and (dec != "-" or f.get("kind") == "strength" or ver in ("unverified", "duplicate")): continue
    rows.append((f, sev, ver, dec))
if "--counts" in a:
    for name, key in [("severity", lambda r: r[1]), ("category", lambda r: r[0].get("category") or "Strength"),
                      ("role", lambda r: r[0].get("role")), ("verdict", lambda r: r[2]), ("disposition", lambda r: r[3])]:
        c = Counter(key(r) for r in rows)
        print(f"{name}: " + ", ".join(f"{k}={v}" for k, v in c.most_common()))
    sys.exit()
for f, sev, ver, dec in rows:
    print(f"{f['id']} | {sev} | {f.get('category') or '-'} | {f.get('area', '-')} | {ver} | {dec} | {f['title']}")
print(f"-- {len(rows)} item(s)")
