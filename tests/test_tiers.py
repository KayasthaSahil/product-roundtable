"""Tests for the optional Tree-sitter/adapter tiers and semantic ingest. Tree-sitter tests skip if not installed."""
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / '.claude' / 'skills' / 'codebase-atlas' / 'scripts' / 'atlas.py'
HAS_TS = all(importlib.util.find_spec(m) for m in ('tree_sitter', 'tree_sitter_javascript', 'tree_sitter_typescript', 'tree_sitter_go'))
NL = chr(10)


def lines(*xs):
    return NL.join(xs) + NL


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, rel, text):
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding='utf-8')

    def cli(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=self.root, text=True, capture_output=True, check=False)

    def records(self):
        return json.loads((self.root / '.review/codebase-atlas/evidence/source-index.json').read_text())['records']

    def manifest(self):
        return json.loads((self.root / '.review/codebase-atlas/manifest.json').read_text())


@unittest.skipUnless(HAS_TS, 'optional tree-sitter packages not installed')
class TreeSitterTierTests(Base):
    def test_syntax_tree_ignores_comments_and_counts_dynamic_behaviour_as_unresolved(self):
        self.write('package.json', '{"dependencies":{"express":"4","next":"14"}}')
        self.write('src/server.js', lines(
            "const app = require('express')();",
            "// app.get('/ghost', h)",
            "const p = '/dyn';",
            "app.get('/items', list);",
            "app.get(p, dyn);",
            "const m = require(process.env.X);",
            "async function f(n) { return import('./m-' + n); }"))
        self.write('pages/api/hello.ts', 'export default function handler() {}' + NL)
        self.assertEqual(self.cli('build').returncode, 0)
        recs = self.records()
        names = {(r['kind'], r['name']) for r in recs}
        self.assertIn(('api', '/items'), names)
        self.assertNotIn(('api', '/ghost'), names)
        self.assertIn(('api', '/api/hello'), names)  # Next.js file route
        for r in recs:
            if r['extraction'] == 'adapter':
                self.assertEqual(r['confidence'], 'INFERRED', r)
        ex = self.manifest()['coverage']['extraction']
        self.assertEqual(list(ex['by_language']['JavaScript']['tiers']), ['tree-sitter'])
        self.assertEqual(ex['unresolved_observed'].get('non-literal-route-path'), 1)
        self.assertEqual(ex['unresolved_observed'].get('dynamic-require'), 1)
        self.assertEqual(ex['unresolved_observed'].get('dynamic-import'), 1)
        self.assertEqual(self.cli('verify').returncode, 0)

    def test_go_routes_require_a_path_and_tests_are_found(self):
        self.write('main.go', lines('package main', 'func main() {', '  http.HandleFunc("/health", h)', '  cache.Get("key")', '}'))
        self.write('main_test.go', lines('package main', 'func TestMain(t *testing.T) {}'))
        self.cli('build')
        names = {(r['kind'], r['name']) for r in self.records()}
        self.assertIn(('api', '/health'), names)
        self.assertNotIn(('api', 'key'), names)
        self.assertIn(('test', 'TestMain'), names)


class SemanticIngestTests(Base):
    def facts(self, line=1):
        return {'tool': 'demo-analyzer 1.0',
                'facts': [{'kind': 'symbol', 'name': 'greet', 'path': 'a.py', 'line': line, 'description': 'resolved by analyzer'}],
                'edges': [{'from_path': 'b.py', 'to_path': 'a.py', 'type': 'CALLS', 'line': 1}]}

    def test_ingest_adds_verified_records_with_provenance_and_goes_stale_on_change(self):
        self.write('a.py', 'def greet(): pass' + NL)
        self.write('b.py', 'import a' + NL)
        self.cli('build')
        self.write('facts.json', json.dumps(self.facts()))
        out = self.cli('ingest', 'facts.json')
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        sem = [r for r in self.records() if r['extraction'] == 'semantic']
        self.assertEqual(len(sem), 1)
        self.assertEqual(sem[0]['confidence'], 'VERIFIED')
        self.assertEqual(sem[0]['discovery_method'], 'semantic:demo-analyzer 1.0')
        self.assertEqual(self.manifest()['coverage']['semantic']['edges'], 1)
        self.assertEqual(self.cli('verify').returncode, 0)
        self.write('a.py', 'def greet(): return 1' + NL)  # file changes after the analyzer ran
        self.cli('refresh', '--changed')
        self.assertEqual([r for r in self.records() if r['extraction'] == 'semantic'], [])
        self.assertEqual(self.manifest()['coverage']['semantic']['stale_skipped'], 2)

    def test_ingest_rejects_paths_outside_the_repository(self):
        self.write('a.py', 'x = 1' + NL)
        bad = self.facts()
        bad['facts'][0]['path'] = '../outside.py'
        self.write('facts.json', json.dumps(bad))
        out = self.cli('ingest', 'facts.json')
        self.assertNotEqual(out.returncode, 0)
        self.assertIn('ingest rejected', out.stderr + out.stdout)


class PythonFrameworkTests(Base):
    def test_fastapi_and_django_routes_are_adapter_tier_and_dynamic_paths_are_counted(self):
        self.write('api/main.py', lines('from fastapi import FastAPI', 'app = FastAPI()', 'P = "/dyn"', '@app.get("/items")', 'def items(): return []', '@app.get(P)', 'def dyn(): return []'))
        self.write('shop/urls.py', lines('from django.urls import path', 'urlpatterns = [path("cart/", view), path(NAME, view)]'))
        env_ok = self.cli('build')
        self.assertEqual(env_ok.returncode, 0, env_ok.stderr)
        recs = self.records()
        by = {(r['kind'], r['name']): r for r in recs}
        self.assertIn('/items', by[('api', 'items')]['description'])
        self.assertEqual(by[('api', 'items')]['extraction'], 'adapter')
        self.assertEqual(by[('api', 'items')]['confidence'], 'INFERRED')
        self.assertIn(('route', 'cart/'), by)
        ex = self.manifest()['coverage']['extraction']
        self.assertEqual(ex['unresolved_observed'].get('non-literal-route-path'), 2)
        self.assertEqual(self.cli('verify').returncode, 0)


if __name__ == '__main__':
    unittest.main()
