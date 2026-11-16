import json, subprocess, sys, tempfile, unittest
from pathlib import Path

STATE = Path(__file__).resolve().parents[1] / '.claude' / 'skills' / 'review-committee' / 'scripts' / 'state.py'

class StageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.root = Path(self.tmp.name)
        self.run_state('init')

    def tearDown(self):
        self.tmp.cleanup()

    def run_state(self, *a):
        return subprocess.run([sys.executable, str(STATE), *a], cwd=self.root, text=True, capture_output=True)

    def phase(self):
        return json.loads((self.root / '.review/state.json').read_text())['phase']

    def advance_to(self, target):
        while self.phase() != target:
            r = self.run_state('advance'); self.assertEqual(r.returncode, 0, r.stderr)

    def test_debate_is_skipped_by_default(self):
        self.advance_to('P3')
        r = self.run_state('advance')
        self.assertIn('Stage 2/3 (Review) COMPLETE', r.stdout)
        s = json.loads((self.root / '.review/state.json').read_text())
        self.assertEqual(s['phase'], 'P5'); self.assertEqual(s['phases']['P4']['status'], 'skipped')

    def test_debate_opt_in_runs_p4(self):
        self.advance_to('P3'); self.run_state('advance')
        # P5 is ready, not complete: debate may still be requested and returns to P4
        r = self.run_state('debate'); self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.phase(), 'P4')
        self.run_state('advance'); self.assertEqual(self.phase(), 'P5')

    def test_debate_rejected_before_review_done(self):
        self.assertNotEqual(self.run_state('debate').returncode, 0)

    def test_stage_1_end_message(self):
        r = self.run_state('advance'); self.assertNotIn('COMPLETE', r.stdout)
        r = self.run_state('advance'); self.assertIn('Stage 1/3 (Understand) COMPLETE', r.stdout)

if __name__ == '__main__':
    unittest.main()


class DepthAndCleanupTests(StageTests):
    def test_depth_follows_repo_size_and_can_be_overridden(self):
        prof = self.root / '.review/brief'; prof.mkdir(parents=True, exist_ok=True)
        (prof / 'stack-profile.json').write_text(json.dumps({"size": {"files": 8}}))
        self.assertIn('lite', self.run_state('depth').stdout)
        (prof / 'stack-profile.json').write_text(json.dumps({"size": {"files": 400}}))
        self.assertIn('full', self.run_state('depth').stdout)
        self.assertIn('lite', self.run_state('depth', 'lite').stdout)

    def test_review_end_removes_env_and_playwright_noise_only(self):
        (self.root / '.review/runs/env/lib').mkdir(parents=True)
        shots = self.root / '.review/evidence/screenshots'; shots.mkdir(parents=True)
        (shots / 'page-1.yml').write_text('x'); (self.root / '.review/evidence/keep.png').write_text('x')
        self.run_state('start', 'P6')
        self.assertEqual(self.run_state('advance', '--force').returncode, 0)
        self.assertFalse((self.root / '.review/runs/env').exists())
        self.assertFalse((shots / 'page-1.yml').exists())
        self.assertTrue((self.root / '.review/evidence/keep.png').exists())


class CapsAndTokensTests(StageTests):
    VALIDATE = Path(__file__).resolve().parents[1] / '.claude' / 'skills' / 'review-standards' / 'scripts' / 'validate.py'

    def _finding(self, i, sev):
        return {"id": f"FND-BE-{i:03d}", "kind": "finding", "title": "t", "role": "BE", "phase": "P2", "category": "Bug / Defect",
                "severity": sev, "location": "x", "evidence": [{"type": "source", "ref": "doc"}], "problem": "p", "impact": "i",
                "recommendation": {"what": "w", "verification": "v"}, "confidence": "high"}

    def test_lite_depth_caps_findings_and_low_items(self):
        (self.root / '.review/brief').mkdir(parents=True, exist_ok=True)
        (self.root / '.review/brief/stack-profile.json').write_text(json.dumps({"size": {"files": 5}}))
        self.run_state('depth')
        doc = {"role": "BE", "cycle": 1, "findings": [self._finding(i, "Low") for i in range(1, 5)]}
        p = self.root / 'f.json'; p.write_text(json.dumps(doc))
        r = subprocess.run([sys.executable, str(self.VALIDATE), 'findings', str(p)], cwd=self.root, text=True, capture_output=True)
        self.assertNotEqual(r.returncode, 0); self.assertIn('Low/Opportunity findings exceeds', r.stdout)

    def test_total_tokens_are_recorded_and_summed(self):
        self.run_state('dispatch', 'ARC', 'x', '--result', 'complete', '--total-tokens', '1200')
        self.run_state('dispatch', 'QA', 'y', '--result', 'complete', '--total-tokens', '800')
        out = self.run_state('dispatch-metrics').stdout
        self.assertIn('this step=2000', out)


class DepthByLinesTests(StageTests):
    def test_depth_uses_atlas_lines_of_code(self):
        d = self.root / '.review/codebase-atlas/evidence'; d.mkdir(parents=True)
        (d / 'source-index.json').write_text(json.dumps({"sources": [
            {"path": "a.ts", "line_count": 4000}, {"path": "package-lock.json", "line_count": 90000}]}))
        self.assertIn('lite', self.run_state('depth').stdout)
        (d / 'source-index.json').write_text(json.dumps({"sources": [{"path": "a.ts", "line_count": 9000}]}))
        self.assertIn('full', self.run_state('depth').stdout)
