#!/usr/bin/env python3
"""Build .review/report/index.html from canonical .review/ records and P0 product-context.json. Run from repo root.
Self-contained output (no external dependencies). Safe to run any time."""
import datetime, glob, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
R = ".review"

def load(p, default):
    try:
        return json.load(open(p, encoding="utf-8"))
    except Exception:
        return default

CAST = [
    ("CHR", "The Chair", "Holds the vision and makes the final call.", "#1f2a44"),
    ("PMV", "The Advocate", "Speaks for the people who will use the product.", "#b4532a"),
    ("PMS", "The Minimalist", "Asks of every feature: does it earn its place?", "#6b6f2a"),
    ("CMP", "The Scout", "Knows what the market already does well.", "#2f6f73"),
    ("ARC", "The Architect", "Sees the whole system and its load-bearing walls.", "#3b4a8c"),
    ("FE", "The Interface Engineer", "Cares how the UI is built, not just how it looks.", "#5b5fc7"),
    ("BE", "The Systems Engineer", "Makes sure every job finishes, or fails clearly.", "#2d5f8b"),
    ("AI", "The AI Engineer", "Keeps Claude reliable, predictable and steerable.", "#7a3f8f"),
    ("MED", "The Render Engineer", "Makes every frame land where it should.", "#8c3b5a"),
    ("VIS", "The Design Critic", "Spots the generic AI-generated look from across the room.", "#c0392b"),
    ("UX", "The Experience Designer", "Walks every flow, click by click.", "#d07a1f"),
    ("XAI", "The Explainer", "Makes the AI's choices visible and controllable.", "#9a6a0b"),
    ("DOC", "The Wordsmith", "Makes every label, message and doc clear.", "#4f7a3a"),
    ("QA", "The Skeptic", "Assumes it will break, and finds where.", "#5a4a3a"),
    ("CPE", "The Accountant", "Counts every token and every second.", "#3f7f5f"),
    ("RED", "The Contrarian", "Argues against the room, on purpose.", "#9b1c1c"),
    ("VER", "The Verifier", "Trusts nothing without evidence.", "#475569"),
    ("SCR", "The Narrator", "Tells the story faithfully from the record.", "#6d5b45"),
]
GLOSSARY = [
    ("Critical", "Security hole, data loss, fundamental failure or release blocker."),
    ("High", "Major defect, broken core workflow or significant architectural risk."),
    ("Medium", "Meaningful usability, maintainability, reliability or performance gain."),
    ("Low", "Minor polish or consistency."),
    ("Opportunity", "Strategic enhancement — not a problem today."),
    ("Verified", "Evidence checked by someone other than the author; the problem is real."),
    ("Unverified", "Not shown with evidence — cannot drive a decision."),
    ("Accepted with modifications", "Will be done, with changes agreed in debate."),
    ("Deferred", "Valid, but not now; a revisit trigger is recorded."),
    ("Requires experiment", "Outcome uncertain; a small spike decides it."),
    ("Workstream (WS)", "A group of accepted decisions delivered together, with one owner."),
    ("Strategic decision", "A direction-level call made by the Chair, flagged for your attention."),
]

state = load(f"{R}/state.json", {})
product_context = load(f"{R}/brief/product-context.json", {})
findings = []
for p in sorted(glob.glob(f"{R}/findings/*.json")):
    findings += load(p, {}).get("findings", [])
verdicts = {v["finding_id"]: v for v in load(f"{R}/verification/verification-log.json", {"verdicts": []}).get("verdicts", [])}
decisions = load(f"{R}/decisions/decision-log.json", {"decisions": []}).get("decisions", [])
fdec = {}
for d in decisions:
    for f in d.get("findings", []):
        fdec[f] = d
for f in findings:
    v = verdicts.get(f["id"])
    if v:
        f["verdict"] = v["verdict"]
        rc = v.get("reclassified") or {}
        if rc.get("severity"): f["severity"] = rc["severity"]
        if rc.get("category"): f["category"] = rc["category"]
    if f["id"] in fdec:
        f["disposition"] = fdec[f["id"]]["disposition"]; f["decision"] = fdec[f["id"]]["id"]

disputes = []
for dp in sorted(glob.glob(f"{R}/debates/DBT-*/dispute.json")):
    d = load(dp, None)
    if not d: continue
    folder = os.path.dirname(dp)
    d["positions"] = [load(p, {}) for p in sorted(glob.glob(f"{folder}/*.json")) if not p.endswith("dispute.json")]
    disputes.append(d)

roadmap = load(f"{R}/decisions/roadmap.json", {"workstreams": []}).get("workstreams", [])
tickets = [load(p, {}) for p in sorted(glob.glob(f"{R}/implementation/tickets/TASK-*.json"))]
gate = load(f"{R}/gate/readiness-gate.json", {"items": []}).get("items", [])
pack = sorted(os.path.relpath(p, f"{R}/implementation").replace(os.sep, "/")
              for p in glob.glob(f"{R}/implementation/**/*.md", recursive=True))

cast = []
for code, name, persona, color in CAST:
    cast.append({"code": code, "name": name, "persona": persona, "color": color})
real = [f for f in findings if f.get("kind") == "finding"]
counts = {"findings": len(real), "strengths": len(findings) - len(real),
          "verified": sum(1 for f in real if f.get("verdict") in ("verified", "partially-verified", "reclassified"))}

data = {"generated_at": datetime.datetime.now().strftime("%d %b %Y, %H:%M"),
        "state": {k: state.get(k) for k in ("status", "phase", "cycle", "phases")},
        "active_roles": state.get("active_roles", []), "product_context": product_context, "cast": cast, "findings": findings,
        "disputes": disputes, "decisions": decisions, "roadmap": roadmap, "tickets": tickets, "gate": gate, "pack": pack,
        "counts": counts, "glossary": GLOSSARY + [(c[0], c[1]) for c in CAST]}
tpl = open(os.path.join(HERE, "..", "templates", "report.html"), encoding="utf-8").read()
payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
os.makedirs(f"{R}/report", exist_ok=True)
open(f"{R}/report/index.html", "w", encoding="utf-8").write(tpl.replace("__DATA__", payload))
print(f"Built {R}/report/index.html — {len(product_context.get('features', []))} features, {len(real)} findings, {len(disputes)} debates, {len(decisions)} decisions, {len(tickets)} planning tickets.")
