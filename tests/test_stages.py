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
