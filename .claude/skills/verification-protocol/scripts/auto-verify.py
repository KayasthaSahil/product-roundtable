#!/usr/bin/env python3
"""P3 tier-1 scripted verification. Run from repo root BEFORE dispatching VER.

Critical/High, strategy/market claims, anything failing a check, and every 5th passing Medium
go to .review/verification/auto-queue.json for agent verification. Low/Opportunity and Medium
findings whose code excerpts are found at the cited lines get a scripted `verified` verdict in
.review/verification/by-AUTO.json (merged by VER's consolidation pass like any by-<ROLE>.json).
"""
import glob, json, os, re, sys

SAMPLE_EVERY = 5
norm = lambda s: re.sub(r"\s+", " ", s).strip()

def load(p):
    try: return json.load(open(p, encoding="utf-8"))
    except Exception: return {}

def check_evidence(e):
    """-> (ok, content_matched, problem)"""
    ref, typ = e.get("ref", ""), e.get("type")
    if typ == "code":
        m = re.match(r"^(.+?)(?::(\d+)(?:-(\d+))?)?$", ref)
        fp = m.group(1)
        if not os.path.isfile(fp): return False, False, f"path not found: {fp}"
        lines = open(fp, encoding="utf-8", errors="ignore").read().splitlines()
        if not m.group(2): return True, False, ""
        a, b = int(m.group(2)), int(m.group(3) or m.group(2))
        if b > len(lines): return False, False, f"{fp} has {len(lines)} lines, cited {b}"
        detail = [norm(x) for x in (e.get("detail") or "").splitlines() if len(norm(x)) >= 8]
        if not detail: return True, False, ""
        window = norm(" ".join(lines[max(0, a - 6):b + 5]))
        hit = sum(1 for d in detail if d.strip("…. ") in window)
        if hit * 2 < len(detail): return False, False, f"excerpt not found near {fp}:{a}"
        return True, True, ""
    if ref.startswith(".review/") and not os.path.exists(ref.split(":")[0]):
        return False, False, f"evidence file missing: {ref}"
    return True, False, ""

def main():
    findings = []
    for p in sorted(glob.glob(".review/findings/*.json")):
        findings += [f for f in load(p).get("findings", []) if f.get("kind") == "finding"]
    verdicts, queue, passing_medium = [], [], 0
    for f in sorted(findings, key=lambda x: x["id"]):
        sev, fid = f.get("severity"), f["id"]
        why = None
        if sev in ("Critical", "High"): why = "Critical/High: direct verification"
        elif f.get("category") == "Product Strategy Opportunity" or f.get("role") == "CMP": why = "market/strategy claim: needs dated source check"
        else:
            res = [check_evidence(e) for e in f.get("evidence", [])]
            bad = [r[2] for r in res if not r[0]]
            if not res: why = "no evidence"
            elif bad: why = "integrity check failed: " + "; ".join(bad[:2])
            elif sev == "Medium":
                if not any(r[1] for r in res): why = "Medium without a matched code excerpt: needs agent verification"
                elif not all(e.get("type") in ("code", "source", "document") for e in f["evidence"]): why = "Medium with behavioural evidence: needs agent verification"
                else:
                    passing_medium += 1
                    if passing_medium % SAMPLE_EVERY == 0: why = "Medium spot-check sample"
        if why: queue.append({"id": fid, "reason": why}); continue
        method = ("scripted-integrity: paths, line ranges and excerpt match checked" if sev == "Medium"
                  else "scripted-integrity: paths and line ranges checked (Low/Opportunity tier)")
        verdicts.append({"finding_id": fid, "verdict": "verified", "verifier": "VER", "method": method,
                         "notes": "Existence and content of cited references confirmed by script; behaviour not independently reproduced."})
    os.makedirs(".review/verification", exist_ok=True)
    json.dump({"verdicts": verdicts}, open(".review/verification/by-AUTO.json", "w", encoding="utf-8"), indent=2)
    json.dump({"queue": queue, "auto_verified": len(verdicts)}, open(".review/verification/auto-queue.json", "w", encoding="utf-8"), indent=2)
    print(f"auto-verified={len(verdicts)} queued-for-agents={len(queue)} (of {len(findings)} findings)")

if __name__ == "__main__":
    sys.exit(main())
