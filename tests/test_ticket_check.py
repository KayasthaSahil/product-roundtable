#!/usr/bin/env python3
"""Regression tests for fail-closed ticket quality and traceability checks."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / ".claude" / "skills" / "implementation-pack" / "scripts" / "ticket-check.py"


class TicketCheckTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / ".review/findings").mkdir(parents=True)
        (self.root / ".review/decisions").mkdir(parents=True)
        (self.root / ".review/implementation/tickets").mkdir(parents=True)
        (self.root / "src").mkdir()
        (self.root / "src/service.py").write_text("def run():\n    return True\n", encoding="utf-8")
        self.write_json(".review/findings/BE.json", {
            "role": "BE", "cycle": 1, "findings": [{
                "id": "SUT-BE-001", "kind": "finding", "title": "Run lock is not atomic",
                "role": "BE", "phase": "P2", "location": "src/service.py",
                "evidence": [{"type": "code", "ref": "src/service.py:1"}],
                "problem": "Concurrent run attempts can both enter the critical section.",
                "confidence": "high", "severity": "High", "category": "Security / Reliability Risk",
                "recommendation": {"what": "Use an atomic lock", "why": "Avoid concurrent writes.",
                                    "expected_outcome": "Only one owner acquires the lock.",
                                    "verification": "Run concurrent acquisition tests."},
                "impact": "Run state may become inconsistent."
            }]
        })
        self.write_json(".review/decisions/decision-log.json", {"decisions": [{
            "id": "DEC-001", "title": "Make run locking atomic", "findings": ["SUT-BE-001"],
            "disposition": "Accepted", "rationale": "Prevent concurrent mutation of one run.",
            "owner_role": "BE", "workstream": "WS-01", "implementation_required": True,
            "ticket_ids": ["TASK-001"]
        }]})
        self.write_json(".review/decisions/roadmap.json", {"workstreams": [{
            "id": "WS-01", "title": "Reliable run management", "goal": "Prevent conflicting run operations.",
            "owner_role": "BE", "horizon": "Now", "sequence": 1, "decisions": ["DEC-001"],
            "depends_on": [], "effort": "M", "outcome": "Run state remains consistent."
        }]})
        self.write_json(".review/implementation/tickets/TASK-001.json", self.ticket())

    def tearDown(self):
        self.temp.cleanup()

    def write_json(self, relative, data):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def ticket(self):
        checks = {
            "traceability": True, "behavior_clarity": True, "scope_decomposition": True,
            "source_grounding": True, "dependency_integrity": True, "acceptance_criteria": True,
            "verification_plan": True, "rollback_and_handoff": True, "status_and_gate_alignment": True,
        }
        return {
            "id": "TASK-001", "title": "Make run lock acquisition atomic", "status": "DRAFT",
            "priority": "High", "workstream": "WS-01", "findings": ["SUT-BE-001"],
            "decisions": ["DEC-001"], "disputes": [],
            "objective": "Ensure one process owns a run lock at a time.",
            "current_behavior": "Concurrent processes can enter the run operation without an atomic exclusion guarantee.",
            "expected_behavior": "Only one process can acquire the lock for a given run; competing attempts receive a safe conflict result.",
            "rationale": "Prevent concurrent mutation and inconsistent run state.",
            "scope": {"in_scope": ["Make run lock acquisition atomic", "Add contention handling"], "out_of_scope": ["Redesign the entire runner"]},
            "source_inspection": [{"item": "Existing run lock acquisition", "status": "verified", "evidence": ["src/service.py:1 inspected"]}],
            "implementation_locations": [{"path": "src/service.py", "symbol": "run", "status": "verified", "notes": "Current lock entry point."}],
            "dependencies": [], "owner_role": "BE", "effort": "M",
            "acceptance_criteria": [
                "When two processes acquire the same run lock concurrently, exactly one succeeds.",
                "A competing process receives a defined conflict result without changing run state."
            ],
            "rollback": "Revert the lock change and restore the previous lock configuration; no data migration is required.",
            "owner_approval": {"status": "pending", "approved_by": "", "approved_at": "", "note": "Plan approval only."},
            "readiness": {"verdict": "Hold", "conditions": [], "satisfied_conditions": [], "open_conditions": [], "assessed_by": [], "assessed_at": ""},
            "implementation_plan": [
                "Inspect the lock acquisition and release paths in the run service.",
                "Replace the non-atomic acquisition with an atomic lock operation.",
                "Add contention and interrupted-process test scenarios."
            ],
            "verification_plan": {"test_scenarios": ["Two simultaneous acquisitions", "Lock owner exits unexpectedly"],
                                  "required_checks": ["Exactly one acquisition succeeds", "Run state remains unchanged after conflict"],
                                  "test_commands": []},
            "handoff_requirements": ["Provide the changed-file summary.", "Provide exact test commands and results."],
            "quality_review": {"verdict": "PASS", "reviewed_by": "CHR", "reviewed_at": "2026-11-15T10:00:00+05:30", "checks": checks, "issues": []}
        }

    def run_check(self):
        return subprocess.run([sys.executable, str(SCRIPT), "--root", str(self.root)],
                              capture_output=True, text=True, cwd=self.root)

    def test_valid_ticket_passes(self):
        result = self.run_check()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("TICKET CHECK PASSED", result.stdout)

    def test_missing_review_directory_fails_closed(self):
        (self.root / ".review").rename(self.root / "review-hidden")
        result = self.run_check()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing review directory", result.stdout)

    def test_malformed_decision_log_fails_closed(self):
        (self.root / ".review/decisions/decision-log.json").write_text("{broken", encoding="utf-8")
        result = self.run_check()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("cannot read decision log", result.stdout)

    def test_missing_roadmap_fails_closed(self):
        (self.root / ".review/decisions/roadmap.json").unlink()
        result = self.run_check()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing required roadmap", result.stdout)

    def test_malformed_finding_record_fails_closed(self):
        (self.root / ".review/findings/BE.json").write_text("not-json", encoding="utf-8")
        result = self.run_check()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("cannot read finding record", result.stdout)

    def test_ticket_cannot_link_to_rejected_decision(self):
        doc = self.ticket()
        doc["decisions"] = ["DEC-002"]
        self.write_json(".review/implementation/tickets/TASK-001.json", doc)
        decisions = json.loads((self.root / ".review/decisions/decision-log.json").read_text())
        decisions["decisions"][0].update(id="DEC-002", disposition="Rejected", ticket_ids=["TASK-001"])
        self.write_json(".review/decisions/decision-log.json", decisions)
        roadmap = json.loads((self.root / ".review/decisions/roadmap.json").read_text())
        roadmap["workstreams"][0]["decisions"] = ["DEC-002"]
        self.write_json(".review/decisions/roadmap.json", roadmap)
        result = self.run_check()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not accepted", result.stdout)

    def test_accepted_decision_without_ticket_is_rejected(self):
        decisions = json.loads((self.root / ".review/decisions/decision-log.json").read_text())
        decisions["decisions"][0]["ticket_ids"] = []
        self.write_json(".review/decisions/decision-log.json", decisions)
        result = self.run_check()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("no ticket_ids", result.stdout)

    def test_dependency_cycle_is_rejected(self):
        doc = self.ticket()
        doc["dependencies"] = ["TASK-002"]
        self.write_json(".review/implementation/tickets/TASK-001.json", doc)
        second = self.ticket()
        second.update(id="TASK-002", title="Add a second lock verification task", dependencies=["TASK-001"])
        self.write_json(".review/implementation/tickets/TASK-002.json", second)
        result = self.run_check()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("ticket dependency cycle", result.stdout)

    def test_verified_missing_path_is_rejected(self):
        doc = self.ticket()
        doc["implementation_locations"][0]["path"] = "src/missing.py"
        self.write_json(".review/implementation/tickets/TASK-001.json", doc)
        result = self.run_check()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("verified implementation path does not exist", result.stdout)

    def test_quality_pass_requires_all_checks(self):
        doc = self.ticket()
        doc["quality_review"]["checks"]["source_grounding"] = False
        self.write_json(".review/implementation/tickets/TASK-001.json", doc)
        result = self.run_check()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("quality_review PASS has failed/missing checks", result.stdout)

    def test_awaiting_approval_requires_quality_pass(self):
        doc = self.ticket()
        doc["status"] = "AWAITING_OWNER_APPROVAL"
        doc["quality_review"]["verdict"] = "NOT_REVIEWED"
        self.write_json(".review/implementation/tickets/TASK-001.json", doc)
        result = self.run_check()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("requires quality_review.verdict=PASS", result.stdout)

    def test_valid_awaiting_owner_approval_passes(self):
        doc = self.ticket()
        doc["status"] = "AWAITING_OWNER_APPROVAL"
        doc["readiness"] = {"verdict": "Go", "conditions": [], "satisfied_conditions": [],
                            "open_conditions": [], "assessed_by": ["BE", "QA"], "assessed_at": "2026-11-15"}
        self.write_json(".review/implementation/tickets/TASK-001.json", doc)
        result = self.run_check()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_unknown_ticket_property_is_rejected(self):
        doc = self.ticket()
        doc["implementation_status"] = "IN_PROGRESS"
        self.write_json(".review/implementation/tickets/TASK-001.json", doc)
        result = self.run_check()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unexpected property 'implementation_status'", result.stdout)

    def test_vague_acceptance_criterion_is_rejected(self):
        doc = self.ticket()
        doc["acceptance_criteria"][0] = "The feature works correctly."
        self.write_json(".review/implementation/tickets/TASK-001.json", doc)
        result = self.run_check()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("is not testable", result.stdout)

    def test_generated_ticket_index_shows_quality_verdict(self):
        builder = Path(SCRIPT).parent / "build-pack-views.py"
        result = subprocess.run([sys.executable, str(builder), "--phase", "P5"],
                                capture_output=True, text=True, cwd=self.root)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        index = (self.root / ".review/implementation/tickets/INDEX.md").read_text(encoding="utf-8")
        self.assertIn("Quality review", index)
        self.assertIn("PASS", index)


if __name__ == "__main__":
    unittest.main(verbosity=2)
