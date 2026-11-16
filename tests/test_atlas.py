import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / '.claude' / 'skills' / 'codebase-atlas' / 'scripts' / 'atlas.py'

class AtlasCliTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / 'app').mkdir()
        (self.root / 'tests').mkdir()
        (self.root / 'README.md').write_text('# Demo\n', encoding='utf-8')
        (self.root / 'app' / 'main.py').write_text(
            'from fastapi import FastAPI\napp = FastAPI()\n@app.get("/items")\ndef list_items():\n    return []\n',
            encoding='utf-8')
        (self.root / 'tests' / 'test_main.py').write_text('def test_items():\n    assert True\n', encoding='utf-8')

    def tearDown(self):
        self.tmp.cleanup()

    def run_cli(self, *args):
        env = {**os.environ, 'ATLAS_DISABLE_TREE_SITTER': '1'}  # these tests pin the stdlib-only baseline
        return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=self.root, env=env,
                              text=True, capture_output=True, check=False)

    def test_build_creates_index_and_verifiable_source_evidence(self):
        result = self.run_cli('build')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.root / '.review/codebase-atlas/atlas.json').is_file())
        self.assertTrue((self.root / '.review/codebase-atlas/manifest.json').is_file())
        source = json.loads((self.root / '.review/codebase-atlas/evidence/source-index.json').read_text())
        self.assertTrue(any(r['kind'] == 'api' and r['name'] == 'list_items' for r in source['records']))
        verify = self.run_cli('verify')
        self.assertEqual(verify.returncode, 0, verify.stdout + verify.stderr)

    def test_coverage_reports_extraction_tiers_and_never_overclaims(self):
        (self.root / 'web').mkdir()
        nl = chr(10)
        (self.root / 'web' / 'app.ts').write_text(nl.join(['// app.get("/ghost")', 'export function Page() {}', 'app.get("/real", h)', '']), encoding='utf-8')
        (self.root / 'svc.go').write_text(nl.join(['package main', 'import "net/http"', 'func main() {}', '']), encoding='utf-8')
        (self.root / 'broken.py').write_text('def (:' + nl, encoding='utf-8')
        self.assertEqual(self.run_cli('build').returncode, 0)
        manifest = json.loads((self.root / '.review/codebase-atlas/manifest.json').read_text())
        ex = manifest['coverage']['extraction']
        self.assertIn('ast', ex['by_language']['Python']['tiers'])
        self.assertIn('ast-failed', ex['by_language']['Python']['tiers'])
        self.assertEqual(list(ex['by_language']['TypeScript']['tiers']), ['pattern'])
        self.assertEqual(list(ex['by_language']['Go']['tiers']), ['minimal'])
        self.assertTrue(any('Go' in w and 'minimal' in w for w in ex['warnings']))
        self.assertTrue(any('ast-failed' in w for w in ex['warnings']))
        source = json.loads((self.root / '.review/codebase-atlas/evidence/source-index.json').read_text())
        for r in source['records']:
            if r['extraction'] in ('pattern', 'heuristic', 'marker', 'minimal'):
                self.assertNotEqual(r['confidence'], 'VERIFIED', r)
        out = self.run_cli('coverage')
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn('Unresolved by design', out.stdout)
        self.assertEqual(self.run_cli('verify').returncode, 0)

    def test_incremental_refresh_reuses_unchanged_files_and_removes_deleted(self):
        self.run_cli('build')
        (self.root / 'app' / 'main.py').write_text(
            'from fastapi import FastAPI\napp = FastAPI()\n@app.get("/items")\ndef list_items():\n    return [1]\n', encoding='utf-8')
        (self.root / 'tests' / 'test_main.py').unlink()
        result = self.run_cli('refresh', '--changed')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('parsed=1', result.stdout)
        self.assertIn('reused=1', result.stdout)
        self.assertIn('deleted=1', result.stdout)
        verify = self.run_cli('verify')
        self.assertEqual(verify.returncode, 0, verify.stdout + verify.stderr)


    def test_curated_features_and_workflows_join_the_relationship_graph(self):
        self.run_cli('build')
        atlas = self.root / '.review/codebase-atlas'
        (atlas / 'product/features.json').write_text(json.dumps({"features": [{
            "id": "FEAT-001", "name": "List items", "observed": {
                "description": "Returns items from the API", "confidence": "VERIFIED",
                "sources": [{"path": "app/main.py", "line_start": 3, "line_end": 5}]
            }, "related_workflows": ["FLOW-001"]
        }]}), encoding='utf-8')
        (atlas / 'product/workflows.json').write_text(json.dumps({"workflows": [{
            "id": "FLOW-001", "name": "Browse items", "actor": "User", "trigger": "Open items view",
            "steps": [{"order": 1, "description": "Call list endpoint", "source": {
                "path": "app/main.py", "line_start": 3, "line_end": 5
            }, "confidence": "VERIFIED"}], "confidence": "VERIFIED"
        }]}), encoding='utf-8')
        result = self.run_cli('build')
        self.assertEqual(result.returncode, 0, result.stderr)
        graph = json.loads((atlas / 'architecture/relationships.json').read_text())
        ids = {node['id'] for node in graph['nodes']}
        self.assertIn('FEAT-001', ids)
        self.assertIn('FLOW-001', ids)
        self.assertTrue(any(edge['source']=='FEAT-001' and edge['target']=='FLOW-001' and edge['type']=='USES' for edge in graph['edges']))
        self.assertEqual(self.run_cli('verify').returncode, 0)


    def test_dependency_change_marks_curated_feature_and_workflow_stale(self):
        (self.root / 'app' / 'models.py').write_text('class Item:\n    pass\n', encoding='utf-8')
        main = self.root / 'app' / 'main.py'
        main.write_text('from fastapi import FastAPI\nfrom .models import Item\napp = FastAPI()\n@app.get("/items")\ndef list_items():\n    return []\n', encoding='utf-8')
        self.run_cli('build')
        atlas = self.root / '.review/codebase-atlas'
        snapshot = json.loads((atlas / 'atlas.json').read_text())['snapshot']
        current = snapshot.get('git_head') if snapshot.get('git_head') != 'unknown' else snapshot['tree_digest']
        (atlas / 'product/features.json').write_text(json.dumps({"features": [{
            "id": "FEAT-DEPENDENT", "name": "List items", "last_verified_snapshot": current,
            "observed": {"description": "Returns items", "confidence": "VERIFIED", "sources": [
                {"path": "app/main.py", "line_start": 4, "line_end": 6}
            ]}
        }]}), encoding='utf-8')
        (atlas / 'product/workflows.json').write_text(json.dumps({"workflows": [{
            "id": "FLOW-DEPENDENT", "name": "Browse items", "actor": "User", "trigger": "Open items",
            "last_verified_snapshot": current, "steps": [{"order": 1, "description": "List items", "source": {
                "path": "app/main.py", "line_start": 4, "line_end": 6
            }, "confidence": "VERIFIED"}]
        }]}), encoding='utf-8')
        self.assertEqual(self.run_cli('build').returncode, 0)
        (self.root / 'app' / 'models.py').write_text('class Item:\n    id: int\n', encoding='utf-8')
        refresh = self.run_cli('refresh', '--changed')
        self.assertEqual(refresh.returncode, 0, refresh.stderr)
        feature = json.loads((atlas / 'product/features.json').read_text())['features'][0]
        workflow = json.loads((atlas / 'product/workflows.json').read_text())['workflows'][0]
        self.assertEqual(feature['freshness'], 'STALE')
        self.assertEqual(workflow['freshness'], 'STALE')
        manifest = json.loads((atlas / 'manifest.json').read_text())
        self.assertEqual(manifest['refresh_state'], 'PARTIAL')
        self.assertEqual(self.run_cli('verify').returncode, 0)



    def test_curator_enrichment_survives_rebuild_and_is_invalidated_on_change(self):
        (self.root / 'app' / 'main.py').write_text(
            'from fastapi import FastAPI\napp = FastAPI()\n@app.get("/items")\ndef list_items():\n    return []\n', encoding='utf-8')
        self.run_cli('build')
        atlas = self.root / '.review/codebase-atlas'
        modules_path = atlas / 'architecture/modules.json'
        modules = json.loads(modules_path.read_text())
        module = next(m for m in modules['modules'] if m['path']=='app/main.py')
        module['purpose'] = 'Handles the item listing endpoint'
        module['last_verified_snapshot'] = json.loads((atlas/'atlas.json').read_text())['snapshot']['tree_digest']
        modules_path.write_text(json.dumps(modules), encoding='utf-8')
        apis_path = atlas / 'interfaces/apis.json'
        apis = json.loads(apis_path.read_text())
        apis['review_note'] = 'Curator-owned top-level metadata'
        apis['apis'][0]['contract_summary'] = 'Returns a list of items'
        apis['apis'][0]['last_verified_snapshot'] = module['last_verified_snapshot']
        apis_path.write_text(json.dumps(apis), encoding='utf-8')
        flows_path = atlas / 'architecture/data-flows.json'
        flows_path.write_text(json.dumps({'flows': [{
            'id': 'FLOW-DATA-001', 'name': 'Item listing data flow',
            'steps': [{'source': {'path': 'app/main.py', 'line': 4}}],
            'last_verified_snapshot': module['last_verified_snapshot']
        }]}), encoding='utf-8')
        graph_path = atlas / 'architecture/relationships.json'
        graph = json.loads(graph_path.read_text())
        graph['nodes'].append({'id': 'MANUAL-NODE-1', 'type': 'concept', 'label': 'Item listing contract', 'origin': 'manual'})
        graph['edges'].append({'source': 'MANUAL-NODE-1', 'target': module['id'], 'type': 'SUPPORTS',
                               'evidence': {'path': 'app/main.py', 'line': 4}, 'confidence': 'VERIFIED',
                               'origin': 'manual', 'last_verified_snapshot': module['last_verified_snapshot']})
        graph_path.write_text(json.dumps(graph), encoding='utf-8')
        self.assertEqual(self.run_cli('build').returncode, 0)
        modules = json.loads(modules_path.read_text())
        self.assertEqual(next(m for m in modules['modules'] if m['path']=='app/main.py')['purpose'], 'Handles the item listing endpoint')
        apis = json.loads(apis_path.read_text())
        self.assertEqual(apis['review_note'], 'Curator-owned top-level metadata')
        self.assertEqual(apis['apis'][0]['contract_summary'], 'Returns a list of items')
        graph = json.loads(graph_path.read_text())
        self.assertIn('MANUAL-NODE-1', {n['id'] for n in graph['nodes']})
        self.assertTrue(any(e.get('origin')=='manual' for e in graph['edges']))
        (self.root / 'app/main.py').write_text((self.root/'app/main.py').read_text()+'\n# changed\n', encoding='utf-8')
        self.assertEqual(self.run_cli('refresh','--changed').returncode, 0)
        modules = json.loads(modules_path.read_text())
        self.assertEqual(next(m for m in modules['modules'] if m['path']=='app/main.py')['freshness'], 'STALE')
        flows = json.loads(flows_path.read_text())
        self.assertEqual(flows['flows'][0]['freshness'], 'STALE')
        graph = json.loads(graph_path.read_text())
        self.assertTrue(any(e.get('origin')=='manual' and e.get('freshness')=='STALE' for e in graph['edges']))
        manifest = json.loads((atlas/'manifest.json').read_text())
        self.assertEqual(manifest['refresh_state'], 'PARTIAL')
        verify = self.run_cli('verify')
        self.assertEqual(verify.returncode, 0, verify.stdout + verify.stderr)
        self.assertIn('stale curated evidence', verify.stdout)

    def test_verify_rejects_evidence_paths_outside_repository(self):
        self.run_cli('build')
        atlas = self.root / '.review/codebase-atlas'
        (atlas / 'product/features.json').write_text(json.dumps({"features": [{
            "id": "FEAT-ESCAPE", "name": "Bad reference",
            "intended": {"description": "", "confidence": "UNVERIFIED", "sources": [
                {"path": "../../outside-secret.txt", "line_start": 1, "line_end": 1}
            ]},
            "observed": {"description": "", "confidence": "UNVERIFIED", "sources": []},
            "gap": {"exists": False, "description": ""}
        }]}), encoding='utf-8')
        self.run_cli('build')
        result = self.run_cli('verify')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('escapes repository', result.stdout)

    def test_status_detects_unrefreshed_source_change(self):
        self.run_cli('build')
        with (self.root / 'app' / 'main.py').open('a', encoding='utf-8') as f:
            f.write('\n# changed\n')
        result = self.run_cli('status')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('Source freshness: STALE', result.stdout)

if __name__ == '__main__':
    unittest.main()

class AtlasIgnoresCommitteeFiles(unittest.TestCase):
    def test_claude_dir_is_not_indexed_and_verify_passes(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / 'app.py').write_text('def f():\n    return 1\n', encoding='utf-8')
            (root / '.claude' / 'skills' / 'x').mkdir(parents=True)
            (root / '.claude' / 'skills' / 'x' / 'tool.py').write_text('import stripe\n', encoding='utf-8')
            env = {**os.environ, 'ATLAS_DISABLE_TREE_SITTER': '1'}
            run = lambda *a: subprocess.run([sys.executable, str(SCRIPT), *a], cwd=root, env=env, text=True, capture_output=True)
            self.assertEqual(run('build').returncode, 0)
            src = json.loads((root / '.review/codebase-atlas/evidence/source-index.json').read_text())
            self.assertFalse(any(s['path'].startswith('.claude') for s in src['sources']))
            self.assertEqual(run('verify').returncode, 0)
