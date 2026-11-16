#!/usr/bin/env python3
"""Fail-closed validation of the Review Committee's planning tickets.

Run from the repository root:
  python3 .claude/skills/implementation-pack/scripts/ticket-check.py
  python3 .claude/skills/implementation-pack/scripts/ticket-check.py --root /path/to/repo

This validates planning records only. It never executes ticket steps or tracks
implementation progress.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_SCHEMA = SCRIPT_DIR.parents[1] / "review-standards" / "schemas" / "ticket.schema.json"
VALID_STATUSES = {
    "DRAFT", "REVIEW_REQUIRED", "AWAITING_OWNER_APPROVAL", "APPROVED",
    "BLOCKED", "DEFERRED", "REJECTED",
}
ACCEPTED = {"Accepted", "Accepted with modifications"}
VAGUE_CRITERION = re.compile(
    r"^(?:it |the feature |the system )?(?:works? correctly|works? as expected|"
    r"is user[- ]friendly|is improved|is robust|is handled properly|is seamless)[.! ]*$",
    re.IGNORECASE,
)


def read_json(path: Path, label: str, errors: list[str], *, required: bool = True):
    if not path.exists():
        if required:
            errors.append(f"missing required {label}: {path}")
        return None
    try:
        with path.open(encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"cannot read {label} {path}: {exc}")
        return None


def require_list(doc, key: str, label: str, errors: list[str]) -> list:
    if not isinstance(doc, dict):
        errors.append(f"{label} must be a JSON object")
        return []
    value = doc.get(key)
    if not isinstance(value, list):
        errors.append(f"{label}.{key} must be an array")
        return []
    return value


def unique_values(values, label: str, errors: list[str]):
    seen = set()
    for value in values:
        if value in seen:
            errors.append(f"{label}: duplicate reference {value}")
        seen.add(value)


def safe_repo_path(raw: str) -> bool:
    if not isinstance(raw, str) or not raw.strip():
        return False
    value = raw.replace("\\", "/")
    if value.startswith("/") or re.match(r"^[A-Za-z]:", value):
        return False
    return all(part not in ("", ".", "..") for part in value.split("/"))


def load_schema(schema_path: Path, errors: list[str]):
    schema = read_json(schema_path, "ticket schema", errors)
    if not isinstance(schema, dict):
        errors.append("ticket schema must be a JSON object")
        return {}
    return schema


def schema_validate(doc, schema, label: str, errors: list[str]):
    # Reuse the same schema validator as all other committee records.
    validator_path = SCRIPT_DIR.parents[1] / "review-standards" / "scripts"
    sys.path.insert(0, str(validator_path))
    try:
        from validate import check
    except Exception as exc:  # fail closed if the shared validator is unavailable
        errors.append(f"cannot load shared schema validator: {exc}")
        return
    check(doc, schema, label, errors)


def validate_source_record(doc, schema_name: str, label: str, errors: list[str]):
    schema_path = SCRIPT_DIR.parents[1] / "review-standards" / "schemas" / f"{schema_name}.schema.json"
    schema = read_json(schema_path, f"{schema_name} schema", errors)
    if not isinstance(schema, dict):
        errors.append(f"{schema_name} schema must be a JSON object")
        return
    schema_validate(doc, schema, label, errors)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="repository root (default: current directory)")
    parser.add_argument("--schema", default=str(DEFAULT_SCHEMA), help="ticket JSON schema path")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    review = root / ".review"
    implementation = review / "implementation"
    tickets_dir = implementation / "tickets"
    errors: list[str] = []
    warnings: list[str] = []

    # Required sources are explicit. Missing or malformed inputs must never
    # collapse to empty defaults and produce a false PASS.
    if not review.is_dir():
        errors.append(f"missing review directory: {review}")
    findings_dir = review / "findings"
    if not findings_dir.is_dir():
        errors.append(f"missing required findings directory: {findings_dir}")
    if not tickets_dir.is_dir():
        errors.append(f"missing required tickets directory: {tickets_dir}")

    schema = load_schema(Path(args.schema).resolve(), errors)
    decision_doc = read_json(review / "decisions" / "decision-log.json", "decision log", errors)
    roadmap_doc = read_json(review / "decisions" / "roadmap.json", "roadmap", errors)
    decisions = require_list(decision_doc, "decisions", "decision log", errors)
    workstreams = require_list(roadmap_doc, "workstreams", "roadmap", errors)
    if decision_doc is not None:
        validate_source_record(decision_doc, "decisions", "decision-log.json", errors)
    if roadmap_doc is not None:
        validate_source_record(roadmap_doc, "roadmap", "roadmap.json", errors)

    # Load all finding records strictly; a malformed source record is an error.
    findings_by_id = {}
    finding_files = sorted(findings_dir.glob("*.json")) if findings_dir.is_dir() else []
    for path in finding_files:
        record = read_json(path, "finding record", errors)
        if record is not None:
            validate_source_record(record, "findings-file", f"finding record {path.name}", errors)
        items = require_list(record, "findings", f"finding record {path.name}", errors)
        for item in items:
            if not isinstance(item, dict) or not isinstance(item.get("id"), str):
                errors.append(f"{path}: every finding must be an object with an id")
                continue
            fid = item["id"]
            if fid in findings_by_id:
                errors.append(f"duplicate finding id across source records: {fid}")
            else:
                findings_by_id[fid] = item

    # Debate references are optional, but any supplied dispute record must be valid.
    dispute_ids = set()
    debates_dir = review / "debates"
    if debates_dir.exists():
        for path in sorted(debates_dir.glob("DBT-*/dispute.json")):
            dispute = read_json(path, "dispute record", errors)
            if dispute is not None:
                validate_source_record(dispute, "dispute", f"dispute record {path}", errors)
            did = path.parent.name
            if isinstance(dispute, dict) and dispute.get("id") != did:
                errors.append(f"{path}: dispute id {dispute.get('id')} does not match directory {did}")
            if did in dispute_ids:
                errors.append(f"duplicate dispute id: {did}")
            dispute_ids.add(did)

    decisions_by_id = {}
    for decision in decisions:
        if not isinstance(decision, dict) or not isinstance(decision.get("id"), str):
            errors.append("every decision must be an object with an id")
            continue
        did = decision["id"]
        if did in decisions_by_id:
            errors.append(f"duplicate decision id: {did}")
        else:
            decisions_by_id[did] = decision
        for fid in decision.get("findings", []):
            if fid not in findings_by_id:
                errors.append(f"{did}: references unknown finding {fid}")

    workstreams_by_id = {}
    for workstream in workstreams:
        if not isinstance(workstream, dict) or not isinstance(workstream.get("id"), str):
            errors.append("every workstream must be an object with an id")
            continue
        wid = workstream["id"]
        if wid in workstreams_by_id:
            errors.append(f"duplicate workstream id: {wid}")
        else:
            workstreams_by_id[wid] = workstream
        unique_values(workstream.get("decisions", []), f"{wid}.decisions", errors)
        unique_values(workstream.get("depends_on", []), f"{wid}.depends_on", errors)
        for did in workstream.get("decisions", []):
            if did in decisions_by_id and decisions_by_id[did].get("disposition") not in ACCEPTED:
                errors.append(f"{wid}: non-accepted decision {did} cannot be in an implementation workstream")
            if did not in decisions_by_id:
                errors.append(f"{wid}: references unknown decision {did}")
        for dep in workstream.get("depends_on", []):
            if dep == wid:
                errors.append(f"{wid}: cannot depend on itself")
            elif dep not in {w.get("id") for w in workstreams if isinstance(w, dict)}:
                errors.append(f"{wid}: unknown workstream dependency {dep}")

    # Workstream dependencies are also a planning graph; reject cycles here.
    ws_graph = {wid: list(ws.get("depends_on", [])) for wid, ws in workstreams_by_id.items()}
    ws_visiting: set[str] = set()
    ws_visited: set[str] = set()
    def visit_workstream(node: str):
        if node in ws_visiting:
            errors.append(f"workstream dependency cycle includes {node}")
            return
        if node in ws_visited:
            return
        ws_visiting.add(node)
        for nxt in ws_graph.get(node, []):
            if nxt in ws_graph:
                visit_workstream(nxt)
        ws_visiting.remove(node)
        ws_visited.add(node)
    for node in ws_graph:
        visit_workstream(node)

    ticket_files = sorted(tickets_dir.glob("*.json")) if tickets_dir.is_dir() else []
    tickets: dict[str, tuple[dict, Path]] = {}
    for path in ticket_files:
        if not re.fullmatch(r"TASK-\d{3}\.json", path.name):
            errors.append(f"unexpected JSON file in canonical ticket directory: {path.name}; expected TASK-NNN.json")
        doc = read_json(path, "ticket", errors)
        if not isinstance(doc, dict):
            continue
        tid = doc.get("id")
        if not isinstance(tid, str) or not re.fullmatch(r"TASK-\d{3}", tid):
            errors.append(f"{path}: ticket id must match TASK-NNN")
            continue
        if tid in tickets:
            errors.append(f"duplicate ticket id: {tid}")
            continue
        tickets[tid] = (doc, path)
        if path.name != f"{tid}.json":
            errors.append(f"{path}: filename must match {tid}.json")
        schema_validate(doc, schema, tid, errors)

    # Ticket-level quality and semantic checks.
    for tid, (ticket, path) in tickets.items():
        prefix = f"{tid} ({path.name})"
        if ticket.get("status") not in VALID_STATUSES:
            errors.append(f"{prefix}: unsupported planning status {ticket.get('status')!r}")

        for field in ("findings", "decisions", "disputes", "dependencies"):
            values = ticket.get(field, [])
            if isinstance(values, list):
                unique_values(values, f"{tid}.{field}", errors)
        for dispute_id in ticket.get("disputes", []):
            if dispute_id not in dispute_ids:
                errors.append(f"{tid}: unknown dispute {dispute_id}")

        linked_decisions = []
        for did in ticket.get("decisions", []):
            decision = decisions_by_id.get(did)
            if not decision:
                errors.append(f"{tid}: unknown decision {did}")
                continue
            linked_decisions.append(decision)
            if decision.get("disposition") not in ACCEPTED:
                errors.append(f"{tid}: decision {did} is {decision.get('disposition')!r}, not accepted")
            if tid not in decision.get("ticket_ids", []):
                errors.append(f"{tid}: decision {did} does not link back through ticket_ids")
            if decision.get("workstream") and decision.get("workstream") != ticket.get("workstream"):
                errors.append(f"{tid}: workstream differs from linked decision {did}")

        if not linked_decisions:
            errors.append(f"{tid}: must link to at least one existing accepted decision")

        current = re.sub(r"\s+", " ", str(ticket.get("current_behavior", "")).strip()).casefold()
        expected = re.sub(r"\s+", " ", str(ticket.get("expected_behavior", "")).strip()).casefold()
        if current and expected and current == expected:
            errors.append(f"{tid}: current_behavior and expected_behavior are identical; describe the actual change")

        linked_finding_ids = set()
        for decision in linked_decisions:
            linked_finding_ids.update(decision.get("findings", []))
        for fid in ticket.get("findings", []):
            finding = findings_by_id.get(fid)
            if not finding:
                errors.append(f"{tid}: unknown finding {fid}")
                continue
            if finding.get("kind") != "finding":
                errors.append(f"{tid}: {fid} is a strength, not an actionable finding")
            if fid not in linked_finding_ids:
                errors.append(f"{tid}: finding {fid} is not connected to any linked decision")

        workstream_id = ticket.get("workstream")
        workstream = workstreams_by_id.get(workstream_id)
        if not workstream:
            errors.append(f"{tid}: unknown workstream {workstream_id}")
        else:
            for decision in linked_decisions:
                if decision.get("id") not in workstream.get("decisions", []):
                    errors.append(f"{tid}: workstream {workstream_id} does not include linked decision {decision.get('id')}")

        # Verified source claims must be backed by evidence and existing paths.
        for index, item in enumerate(ticket.get("source_inspection", [])):
            if not isinstance(item, dict):
                continue
            if item.get("status") == "verified" and not item.get("evidence"):
                errors.append(f"{tid}: source_inspection[{index}] is verified but has no evidence")

        for index, location in enumerate(ticket.get("implementation_locations", [])):
            if not isinstance(location, dict):
                continue
            raw_path = location.get("path", "")
            if not safe_repo_path(raw_path):
                errors.append(f"{tid}: implementation_locations[{index}] path must be a safe repository-relative path")
                continue
            if location.get("status") == "verified" and not (root / raw_path).exists():
                errors.append(f"{tid}: verified implementation path does not exist: {raw_path}")
            if location.get("status") == "candidate_to_verify" and not location.get("notes"):
                warnings.append(f"{tid}: candidate path {raw_path} should explain what must be verified")

        # Acceptance criteria should be observable, not generic assurances.
        criteria = ticket.get("acceptance_criteria", [])
        for index, criterion in enumerate(criteria):
            if isinstance(criterion, str) and VAGUE_CRITERION.fullmatch(criterion.strip()):
                errors.append(f"{tid}: acceptance_criteria[{index}] is not testable: {criterion!r}")
        if len(criteria) == 1:
            warnings.append(f"{tid}: only one acceptance criterion; check normal, failure and boundary behaviour where relevant")

        plan = ticket.get("implementation_plan", [])
        if len(plan) < 2:
            errors.append(f"{tid}: implementation_plan needs at least two ordered, ticket-specific steps")
        if all(isinstance(step, str) and step.lower().startswith(("future implementer:", "make the smallest coherent change", "add or update the targeted tests", "review the eventual change")) for step in plan):
            errors.append(f"{tid}: implementation_plan contains only generic boilerplate; add ticket-specific steps")

        verification = ticket.get("verification_plan", {})
        if isinstance(verification, dict):
            scenarios = verification.get("test_scenarios", [])
            checks = verification.get("required_checks", [])
            if not scenarios:
                errors.append(f"{tid}: verification_plan must contain concrete test_scenarios")
            if not checks:
                errors.append(f"{tid}: verification_plan must contain required_checks")
            if len(scenarios) == 1:
                warnings.append(f"{tid}: one test scenario only; consider failure and boundary scenarios")

        # A Chair-recorded quality review is required before owner handoff.
        quality = ticket.get("quality_review", {})
        quality_verdict = quality.get("verdict") if isinstance(quality, dict) else None
        quality_checks = quality.get("checks", {}) if isinstance(quality, dict) else {}
        quality_issues = quality.get("issues", []) if isinstance(quality, dict) else []
        required_quality_checks = (
            "traceability", "behavior_clarity", "scope_decomposition", "source_grounding",
            "dependency_integrity", "acceptance_criteria", "verification_plan",
            "rollback_and_handoff", "status_and_gate_alignment",
        )
        if quality_verdict in ("NOT_REVIEWED", "REVISE"):
            errors.append(f"{tid}: ticket quality review is unresolved ({quality_verdict}); complete corrections before P5 can pass")
        if quality_verdict == "BLOCKED" and ticket.get("status") != "BLOCKED":
            errors.append(f"{tid}: quality_review BLOCKED requires planning status BLOCKED")
        if quality_verdict in ("PASS", "REVISE", "BLOCKED"):
            if quality.get("reviewed_by") != "CHR":
                errors.append(f"{tid}: completed quality review must be recorded by CHR")
            reviewed_at = quality.get("reviewed_at", "")
            try:
                datetime.fromisoformat(str(reviewed_at).replace("Z", "+00:00"))
            except ValueError:
                errors.append(f"{tid}: completed quality review requires an ISO-8601 reviewed_at timestamp")
        if quality_verdict == "PASS":
            failed_checks = [name for name in required_quality_checks if quality_checks.get(name) is not True]
            if failed_checks:
                errors.append(f"{tid}: quality_review PASS has failed/missing checks: {', '.join(failed_checks)}")
            if quality_issues:
                errors.append(f"{tid}: quality_review PASS cannot retain open issues")
        elif quality_verdict == "REVISE" and not quality_issues:
            errors.append(f"{tid}: quality_review REVISE must explain its issues")
        elif quality_verdict == "BLOCKED" and not quality_issues:
            errors.append(f"{tid}: quality_review BLOCKED must explain its blocker")

        # Approval and readiness are planning-only states.
        status = ticket.get("status")
        approval = ticket.get("owner_approval", {})
        approval_status = approval.get("status") if isinstance(approval, dict) else None
        readiness = ticket.get("readiness", {})
        verdict = readiness.get("verdict") if isinstance(readiness, dict) else None
        conditions = readiness.get("conditions", []) if isinstance(readiness, dict) else []
        satisfied = readiness.get("satisfied_conditions", []) if isinstance(readiness, dict) else []
        open_conditions = readiness.get("open_conditions", []) if isinstance(readiness, dict) else []
        unique_values(conditions, f"{tid}.readiness.conditions", errors)
        unique_values(satisfied, f"{tid}.readiness.satisfied_conditions", errors)
        unique_values(open_conditions, f"{tid}.readiness.open_conditions", errors)
        if set(satisfied) & set(open_conditions):
            errors.append(f"{tid}: a readiness condition cannot be both satisfied and open")
        if set(satisfied) | set(open_conditions) != set(conditions):
            errors.append(f"{tid}: readiness conditions must be fully classified as satisfied or open")
        if verdict == "Go" and open_conditions:
            errors.append(f"{tid}: Go readiness cannot contain open conditions")
        if status in ("DRAFT", "AWAITING_OWNER_APPROVAL", "APPROVED") and quality_verdict != "PASS":
            errors.append(f"{tid}: {status} requires quality_review.verdict=PASS")
        if status == "REVIEW_REQUIRED" and quality_verdict not in ("REVISE", "NOT_REVIEWED"):
            warnings.append(f"{tid}: REVIEW_REQUIRED should identify unresolved quality issues")
        if status == "DRAFT":
            if verdict != "Hold" or (isinstance(readiness, dict) and (readiness.get("assessed_at") or readiness.get("assessed_by"))):
                errors.append(f"{tid}: DRAFT must remain unassessed (readiness Hold) until P6")
        if status == "AWAITING_OWNER_APPROVAL":
            if not readiness.get("assessed_by") or not readiness.get("assessed_at"):
                errors.append(f"{tid}: AWAITING_OWNER_APPROVAL requires P6 assessor roles and assessment date")
            else:
                try:
                    datetime.fromisoformat(str(readiness.get("assessed_at")).replace("Z", "+00:00"))
                except ValueError:
                    errors.append(f"{tid}: readiness.assessed_at must be an ISO-8601 date or timestamp")
            if approval_status != "pending":
                errors.append(f"{tid}: AWAITING_OWNER_APPROVAL requires pending owner approval")
            if verdict not in ("Go", "Go with conditions") or open_conditions:
                errors.append(f"{tid}: AWAITING_OWNER_APPROVAL requires Go/Go-with-conditions and no open conditions")
            if ticket.get("blocker"):
                errors.append(f"{tid}: AWAITING_OWNER_APPROVAL cannot have an active blocker")
        if status == "APPROVED":
            if not readiness.get("assessed_by") or not readiness.get("assessed_at"):
                errors.append(f"{tid}: APPROVED requires P6 assessor roles and assessment date")
            else:
                try:
                    datetime.fromisoformat(str(readiness.get("assessed_at")).replace("Z", "+00:00"))
                except ValueError:
                    errors.append(f"{tid}: readiness.assessed_at must be an ISO-8601 date or timestamp")
            if approval_status != "approved":
                errors.append(f"{tid}: APPROVED requires explicit owner_approval.status=approved")
            if not approval.get("approved_by") or not approval.get("approved_at"):
                errors.append(f"{tid}: APPROVED requires approved_by and approved_at")
            else:
                try:
                    datetime.fromisoformat(str(approval.get("approved_at")).replace("Z", "+00:00"))
                except ValueError:
                    errors.append(f"{tid}: owner_approval.approved_at must be an ISO-8601 date or timestamp")
            if verdict not in ("Go", "Go with conditions") or open_conditions:
                errors.append(f"{tid}: APPROVED requires Go/Go-with-conditions and no open conditions")
            if ticket.get("blocker"):
                errors.append(f"{tid}: APPROVED ticket cannot have an active blocker")
        if approval_status == "approved" and status != "APPROVED":
            errors.append(f"{tid}: owner approval is approved but planning status is not APPROVED")
        if status == "BLOCKED" and not ticket.get("blocker"):
            errors.append(f"{tid}: BLOCKED ticket must state blocker")
        if status == "DEFERRED" and not ticket.get("revisit_trigger"):
            errors.append(f"{tid}: DEFERRED ticket must state revisit_trigger")
        if status == "REJECTED" and approval_status not in ("rejected", "pending"):
            errors.append(f"{tid}: REJECTED must not retain approved owner approval")
        if status in ("DRAFT", "REVIEW_REQUIRED", "BLOCKED", "DEFERRED", "REJECTED") and approval_status == "approved":
            errors.append(f"{tid}: {status} cannot carry approved owner approval")

    # Cross-record ticket references and dependency graph.
    for tid, (ticket, _) in tickets.items():
        for dep in ticket.get("dependencies", []):
            if dep == tid:
                errors.append(f"{tid}: cannot depend on itself")
            elif dep.startswith("TASK-"):
                if dep not in tickets:
                    errors.append(f"{tid}: missing ticket dependency {dep}")
                elif ticket.get("status") in ("AWAITING_OWNER_APPROVAL", "APPROVED") and tickets[dep][0].get("status") in ("BLOCKED", "DEFERRED", "REJECTED"):
                    errors.append(f"{tid}: cannot be plan-ready while dependency {dep} is {tickets[dep][0].get('status')}")
            elif dep.startswith("DEC-"):
                if dep not in decisions_by_id:
                    errors.append(f"{tid}: unknown decision dependency {dep}")
                elif decisions_by_id[dep].get("disposition") not in ACCEPTED:
                    errors.append(f"{tid}: decision dependency {dep} is not accepted")
            elif dep.startswith("WS-") and dep not in workstreams_by_id:
                errors.append(f"{tid}: unknown workstream dependency {dep}")

    graph = {tid: [d for d in doc.get("dependencies", []) if isinstance(d, str) and d.startswith("TASK-")] for tid, (doc, _) in tickets.items()}
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str):
        if node in visiting:
            errors.append(f"ticket dependency cycle includes {node}")
            return
        if node in visited:
            return
        visiting.add(node)
        for nxt in graph.get(node, []):
            if nxt in graph:
                visit(nxt)
        visiting.remove(node)
        visited.add(node)

    for node in graph:
        visit(node)

    # Every accepted decision must explicitly map to one or more tickets or
    # give a reason why no implementation planning ticket is required.
    for did, decision in decisions_by_id.items():
        if decision.get("disposition") in ACCEPTED:
            assigned_ws = decision.get("workstream")
            if not assigned_ws or assigned_ws not in workstreams_by_id:
                errors.append(f"{did}: accepted decision must reference an existing workstream")
            elif did not in workstreams_by_id[assigned_ws].get("decisions", []):
                errors.append(f"{did}: assigned workstream {assigned_ws} does not include this decision")
        if decision.get("disposition") not in ACCEPTED:
            if decision.get("implementation_required") is True or decision.get("ticket_ids"):
                errors.append(f"{did}: non-accepted decision cannot require or link implementation tickets")
            continue
        if "implementation_required" not in decision:
            errors.append(f"{did}: accepted decision missing implementation_required")
            continue
        refs = decision.get("ticket_ids", [])
        unique_values(refs, f"{did}.ticket_ids", errors)
        if decision.get("implementation_required") is True:
            if not refs:
                errors.append(f"{did}: implementation_required=true but no ticket_ids")
            for ref in refs:
                if ref not in tickets:
                    errors.append(f"{did}: linked ticket does not exist: {ref}")
                elif did not in tickets[ref][0].get("decisions", []):
                    errors.append(f"{did}: {ref} does not link back to decision")
        else:
            if not isinstance(decision.get("no_ticket_reason"), str) or not decision["no_ticket_reason"].strip():
                errors.append(f"{did}: implementation_required=false needs no_ticket_reason")
            if refs:
                errors.append(f"{did}: no-ticket decision must not list ticket_ids")

    if errors:
        print(f"TICKET CHECK FAILED ({len(errors)} error(s), {len(warnings)} warning(s))")
        for item in errors[:150]:
            print(" - ERROR:", item)
        for item in warnings[:50]:
            print(" - WARNING:", item)
        return 1

    print(f"TICKET CHECK PASSED — {len(tickets)} tickets, {len(decisions_by_id)} decisions, {len(findings_by_id)} findings, {len(workstreams_by_id)} workstreams.")
    if warnings:
        print(f"QUALITY WARNINGS ({len(warnings)}):")
        for item in warnings[:50]:
            print(" - WARNING:", item)
    print("Planning records, traceability, approval states and dependency graph are valid. No implementation status is tracked.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
