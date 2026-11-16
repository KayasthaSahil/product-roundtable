#!/usr/bin/env python3
"""Build generated Markdown views from canonical planning JSON (stdlib only).

Run from repository root:
  python3 .claude/skills/implementation-pack/scripts/build-pack-views.py --phase P5
  python3 .claude/skills/implementation-pack/scripts/build-pack-views.py --phase P6

P5 builds the decision log, roadmap, and ticket index. P6 also incorporates the
readiness gate. It never changes canonical JSON or product files.
"""
import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

BASE = Path(".review/implementation")
DECISIONS = Path(".review/decisions/decision-log.json")
ROADMAP = Path(".review/decisions/roadmap.json")
GATE = Path(".review/gate/readiness-gate.json")
TICKETS = BASE / "tickets"


def load_json(path: Path, required=True):
    if not path.is_file():
        if required:
            raise ValueError(f"required canonical source is missing: {path}")
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(f"cannot parse {path}: {exc}") from exc


def md(value):
    if value is None or value == "":
        return "—"
    return str(value).replace("|", "\\|").replace("\n", " ").strip()


def bullet_list(items):
    items = [str(x).strip() for x in (items or []) if str(x).strip()]
    return "\n".join(f"- {x}" for x in items) if items else "- None recorded."


def build_decision_log(decisions):
    groups = [
        ("Accepted / Accepted with modifications", [d for d in decisions if d.get("disposition") in ("Accepted", "Accepted with modifications")]),
        ("Deferred", [d for d in decisions if d.get("disposition") == "Deferred"]),
        ("Requires experiment / additional evidence", [d for d in decisions if d.get("disposition") in ("Requires experiment", "Requires additional evidence")]),
        ("Rejected", [d for d in decisions if d.get("disposition") == "Rejected"]),
        ("Merged", [d for d in decisions if d.get("disposition") == "Merged"]),
    ]
    lines = ["# Decision Log", "", "*Generated from `.review/decisions/decision-log.json`. The JSON record is authoritative.*", ""]
    counts = defaultdict(int)
    for d in decisions:
        counts[d.get("disposition", "Unspecified")] += 1
    lines += ["## Summary", "", " | ".join(f"{k}: {v}" for k, v in sorted(counts.items())) or "No decisions recorded.", ""]
    strategic = [d for d in decisions if d.get("strategic")]
    if strategic:
        lines += ["## Strategic decisions", ""]
        for d in strategic:
            lines.append(f"- **{d.get('id')} — {md(d.get('title'))}:** {md(d.get('disposition'))}")
        lines.append("")
    seen = set()
    for title, docs in groups:
        if not docs:
            continue
        lines += [f"## {title}", ""]
        for d in docs:
            did = d.get("id", "DEC-UNKNOWN")
            if did in seen:
                continue
            seen.add(did)
            lines += [f"### {did} — {md(d.get('title'))}", "", f"**Disposition:** {md(d.get('disposition'))} · **Owner role:** {md(d.get('owner_role'))}", ""]
            if d.get("summary"):
                lines += [md(d["summary"]), ""]
            lines += ["**Rationale**", "", md(d.get("rationale")), ""]
            if d.get("modifications"):
                lines += ["**Accepted modifications**", "", md(d["modifications"]), ""]
            if d.get("tradeoffs"):
                lines += ["**Trade-offs**", "", md(d["tradeoffs"]), ""]
            if d.get("findings"):
                lines += [f"**Findings:** {', '.join(d['findings'])}"]
            if d.get("disputes"):
                lines += [f"**Debates:** {', '.join(d['disputes'])}"]
            if d.get("workstream"):
                lines += [f"**Workstream:** {d['workstream']}"]
            if d.get("ticket_ids"):
                lines += [f"**Planning tickets:** {', '.join(d['ticket_ids'])}"]
            elif d.get("implementation_required") is False:
                lines += [f"**No ticket reason:** {md(d.get('no_ticket_reason'))}"]
            if d.get("revisit_trigger"):
                lines += [f"**Revisit trigger:** {md(d['revisit_trigger'])}"]
            if d.get("acceptance_criteria"):
                lines += ["", "**Decision acceptance criteria**", "", bullet_list(d["acceptance_criteria"])]
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def build_roadmap(workstreams, gate):
    verdicts = {x.get("workstream"): x for x in (gate or {}).get("items", [])}
    ordered = sorted(workstreams, key=lambda w: (w.get("sequence", 10**6), w.get("id", "")))
    lines = ["# Product Change Roadmap", "", "*Generated from `.review/decisions/roadmap.json` and, when available, `.review/gate/readiness-gate.json`. The JSON records are authoritative.*", ""]
    if not ordered:
        lines += ["No workstreams recorded.", ""]
    else:
        lines += ["## Intended outcomes", ""]
        for w in ordered:
            lines.append(f"- **{w.get('id')} — {md(w.get('title'))}:** {md(w.get('outcome') or w.get('goal'))}")
        lines += ["", "## Workstreams", "", "| Workstream | Goal / outcome | Owner | Horizon | Sequence | Effort | Depends on | Decisions | Readiness |", "|---|---|---:|---|---:|---|---|---|---|"]
        for w in ordered:
            g = verdicts.get(w.get("id"), {})
            lines.append("| " + " | ".join([
                md(w.get("id")), md(w.get("outcome") or w.get("goal")), md(w.get("owner_role")),
                md(w.get("horizon")), md(w.get("sequence")), md(w.get("effort")),
                md(", ".join(w.get("depends_on", []))), md(", ".join(w.get("decisions", []))),
                md(g.get("verdict", "Not assessed")),
            ]) + " |")
        lines += ["", "## Planning horizons", ""]
        for horizon in ("Now", "Next", "Later"):
            group = [w for w in ordered if w.get("horizon") == horizon]
            if group:
                lines += [f"### {horizon}", ""]
                for w in group:
                    lines.append(f"- **{w.get('id')} — {md(w.get('title'))}:** {md(w.get('goal'))}")
                lines.append("")
        lines += ["## Sequencing rationale", "", "Sequence and dependencies are taken from the canonical roadmap. Independent workstreams may be planned in parallel where no dependency is recorded. Individual task ordering is shown in `../tickets/INDEX.md` and canonical ticket JSON.", ""]
        lines += ["## Readiness conditions", ""]
        if gate and gate.get("items"):
            for g in gate["items"]:
                lines.append(f"### {g.get('workstream')} — {md(g.get('verdict'))}")
                lines.append("")
                lines.append(f"**Risk:** {md(g.get('risk'))} · **Effort:** {md(g.get('effort'))} · **Regression risk:** {md(g.get('regression_risk'))}")
                lines.append("")
                lines.append(bullet_list(g.get("conditions", [])))
                lines.append("")
        else:
            lines += ["P6 readiness assessment has not yet been recorded.", ""]
    lines += ["## Ticket index", "", "See [`../tickets/INDEX.md`](../tickets/INDEX.md) for canonical ticket records and task-level dependencies.", ""]
    return "\n".join(lines).rstrip() + "\n"


def dependency_layers(tickets):
    graph = {tid: [d for d in doc.get("dependencies", []) if d.startswith("TASK-")] for tid, doc in tickets.items()}
    missing = [(tid, dep) for tid, deps in graph.items() for dep in deps if dep not in tickets]
    if missing:
        raise ValueError("ticket dependency references missing ticket(s): " + ", ".join(f"{a}->{b}" for a, b in missing))
    remaining = set(tickets)
    done = set()
    layers = []
    while remaining:
        ready = sorted(tid for tid in remaining if set(graph[tid]).issubset(done))
        if not ready:
            raise ValueError("ticket dependency graph contains a cycle")
        layers.append(ready)
        done.update(ready)
        remaining.difference_update(ready)
    return layers


def build_ticket_index(tickets, workstreams):
    seq = {w.get("id"): w.get("sequence", 10**6) for w in workstreams}
    priority_rank = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
    ordered = sorted(tickets.values(), key=lambda t: (seq.get(t.get("workstream"), 10**6), priority_rank.get(t.get("priority"), 9), t.get("id", "")))
    lines = ["# Planning Ticket Index", "", "*Generated from canonical `TASK-NNN.json` records. Do not edit ticket details or statuses independently here.*", ""]
    counts = defaultdict(int)
    for t in tickets.values():
        counts[t.get("status", "Unspecified")] += 1
    lines += ["## Planning summary", "", " | ".join(f"{k}: {v}" for k, v in sorted(counts.items())) or "No tickets generated.", "", "## Ticket index", "", "| Ticket | Title | Workstream | Priority | Proposed planning owner | Planning status | Quality review | Dependencies | Findings / decisions |", "|---|---|---|---|---|---|---|---|---|"]
    for t in ordered:
        lines.append("| " + " | ".join([
            md(t.get("id")), md(t.get("title")), md(t.get("workstream")), md(t.get("priority")),
            md(t.get("owner_role")), md(t.get("status")), md((t.get("quality_review") or {}).get("verdict", "Not reviewed")),
            md(", ".join(t.get("dependencies", []))), md(", ".join(t.get("findings", []) + t.get("decisions", []))),
        ]) + " |")
    lines += ["", "## Proposed dependency order", ""]
    layers = dependency_layers(tickets)
    if not layers:
        lines.append("No tickets recorded.")
    for i, layer in enumerate(layers, 1):
        lines += [f"### Dependency layer {i}", ""]
        for tid in layer:
            t = tickets[tid]
            lines.append(f"- **{tid} — {md(t.get('title'))}** ({md(t.get('status'))}); workstream {md(t.get('workstream'))}; dependencies: {md(', '.join(t.get('dependencies', [])))}")
        lines.append("")
    lines += ["## How to read a ticket", "", "Open the canonical JSON for the full objective, current and expected behaviour, rationale, scope, proposed steps, source inspection notes, dependencies, acceptance criteria, verification plan, rollback, and handoff requirements.", "", "`APPROVED` means owner approval of the plan only. The committee does not implement tickets or track delivery progress.", ""]
    return "\n".join(lines).rstrip() + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("P5", "P6"), default="P5")
    args = parser.parse_args()
    try:
        decision_doc = load_json(DECISIONS)
        roadmap_doc = load_json(ROADMAP)
        gate = load_json(GATE, required=(args.phase == "P6"))
        ticket_docs = {}
        TICKETS.mkdir(parents=True, exist_ok=True)
        for path in sorted(TICKETS.glob("TASK-*.json")):
            doc = load_json(path)
            tid = doc.get("id")
            if not tid or path.name != tid + ".json":
                raise ValueError(f"ticket id/filename mismatch: {path}")
            if tid in ticket_docs:
                raise ValueError(f"duplicate ticket id: {tid}")
            ticket_docs[tid] = doc

        outputs = {
            BASE / "DECISIONS" / "decision-log.md": build_decision_log(decision_doc.get("decisions", [])),
            BASE / "PLAN" / "roadmap.md": build_roadmap(roadmap_doc.get("workstreams", []), gate),
            TICKETS / "INDEX.md": build_ticket_index(ticket_docs, roadmap_doc.get("workstreams", [])),
        }
        if args.phase == "P6":
            tpl = Path(__file__).resolve().parent.parent / "templates" / "start-here.md"
            outputs[BASE / "START-HERE.md"] = tpl.read_text(encoding="utf-8")
        for path, content in outputs.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        print(f"PACK VIEWS BUILT ({args.phase}) — {len(ticket_docs)} tickets, {len(decision_doc.get('decisions', []))} decisions, {len(roadmap_doc.get('workstreams', []))} workstreams.")
        for path in outputs:
            print(f" - {path}")
        return 0
    except Exception as exc:
        print(f"PACK VIEW BUILD FAILED: {exc}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
