import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

STATE = Path(__file__).resolve().parents[1] / '.claude' / 'skills' / 'review-committee' / 'scripts' / 'state.py'
ALL_ROLES = 'CHR,PMV,PMS,CMP,ARC,FE,BE,AI,MED,VIS,UX,XAI,DOC,QA,CPE,RED,VER,SCR'

class CommitteeRosterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        subprocess.run([sys.executable, str(STATE), 'init'], cwd=self.root, check=True, capture_output=True, text=True)

    def tearDown(self):
        self.tmp.cleanup()

    def run_state(self, *args):
        return subprocess.run([sys.executable, str(STATE), *args], cwd=self.root,
                              text=True, capture_output=True, check=False)

    def test_all_18_roles_are_active_by_default(self):
        state = json.loads((self.root / '.review/state.json').read_text())
        self.assertEqual(len(state['active_roles']), 18)
        self.assertIn('SCR', state['active_roles'])

    def test_roster_cannot_be_reduced(self):
        result = self.run_state('roles', 'CHR,ARC')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('All 18 committee roles', result.stderr)
        result = self.run_state('roles', ALL_ROLES)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_skip_for_atlas_or_token_savings_is_rejected(self):
        result = self.run_state('skip', 'BE', 'Skip because Atlas is incomplete')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('cannot be used to skip', result.stderr)

if __name__ == '__main__':
    unittest.main()
