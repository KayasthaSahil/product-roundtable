#!/usr/bin/env python3
"""Evidence-backed Codebase Atlas for Product Review Committee.

Commands (run from repository root):
  atlas.py build [--force]       Build/reuse deterministic repository intelligence
  atlas.py refresh --changed     Refresh after source changes; unchanged file records are reused
  atlas.py status                Show snapshot, freshness and coverage
  atlas.py coverage              Show extraction tiers per language, tooling, unresolved behaviour and warnings
  atlas.py ingest <facts.json>   Ingest verified output of an external semantic analyzer (see SKILL.md)
  atlas.py search <query>        Search Atlas records and relationships
  atlas.py module <id-or-path>   Show a module/file record
  atlas.py feature <id-or-name> Show a product feature record
  atlas.py workflow <id-or-name>Show a workflow record
  atlas.py dependencies <id-or-path> Show direct incoming/outgoing graph edges
  atlas.py verify                Validate evidence paths, line ranges and graph references

The Atlas is descriptive, not evaluative. It never stores specialist judgements.
"""
from __future__ import annotations
import argparse, ast, hashlib, json, os, re, subprocess, sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path.cwd()
OUT = ROOT / '.review' / 'codebase-atlas'
CACHE = OUT / 'cache' / 'file-records.json'
SCHEMA_VERSION = '1.1.0'
# Extraction tiers, strongest first. Only 'ast' and 'inventory' may claim VERIFIED confidence.
# ast = real parser; pattern = language-aware regex (fallback); heuristic = name/path guess;
# marker = keyword hit; minimal = language without a structural extractor; inventory = file existence.
PATTERN_TIERS = {'pattern', 'heuristic', 'marker', 'minimal', 'adapter'}  # capped below VERIFIED
# tree-sitter = syntax tree (optional install); adapter = framework convention on top of a parse; semantic = ingested analyzer output.
sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    import ts_adapters as TS  # optional tier; works without any third-party package
except Exception:
    TS = None
FRAMEWORKS = set(); EXTRACTOR_SIG = 'builtin'
TIER_NOTES = {
    'tree-sitter': 'parsed into a real syntax tree (optional tier); syntax is exact, framework/dynamic behaviour may still be missing',
    'adapter': 'derived from a framework convention on top of a parse; INFERRED at best',
    'semantic': 'ingested from an external semantic analyzer; provenance names the tool',
    'ast': 'parsed with a real parser; structure is reliable, framework/dynamic behaviour may still be missing',
    'pattern': 'regex fallback, NOT parsed: records are leads only; unusual styles are missed, commented/string code may be misread',
    'minimal': 'no structural extractor: only file inventory, import patterns and keyword markers; treat the map as largely absent',
    'ast-failed': 'parser failed on these files (syntax error or unreadable); no structure extracted',
    'inventory': 'listed only; contents not analysed',
}
IGNORE_DIRS = {'.git','.review','.venv','venv','env','node_modules','vendor','dist','build','coverage','.next','.nuxt','.turbo','__pycache__','.mypy_cache','.pytest_cache','target','bin','obj','Pods'}
SECRET_NAMES = {'.env','.env.local','.env.production','.npmrc','.pypirc','id_rsa','id_ed25519'}
CODE_EXTS = {'.py','.pyi','.js','.jsx','.ts','.tsx','.mjs','.cjs','.java','.kt','.go','.rs','.rb','.php','.cs','.vue','.svelte','.html','.css','.scss','.sql'}
TEXT_EXTS = {'.py','.pyi','.js','.jsx','.ts','.tsx','.mjs','.cjs','.java','.kt','.go','.rs','.rb','.php','.cs','.vue','.svelte','.html','.css','.scss','.sql','.yaml','.yml','.toml','.json','.xml','.md','.sh','.bash','.gradle','.properties','.ini','.cfg','.conf','.dockerfile'}

def now(): return datetime.now(timezone.utc).isoformat(timespec='seconds')
def sha(s: str) -> str: return hashlib.sha256(s.encode('utf-8', errors='replace')).hexdigest()
def read_json(p, default):
    try: return json.loads(p.read_text(encoding='utf-8'))
    except Exception: return default
def write_json(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
def rel(p: Path) -> str: return p.relative_to(ROOT).as_posix()
def git(*args):
    try: return subprocess.check_output(['git', *args], cwd=ROOT, stderr=subprocess.DEVNULL, text=True).strip()
    except Exception: return 'unknown'
def walk_files():
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = sorted(d for d in dirs if d not in IGNORE_DIRS and not d.startswith('.venv'))
        for name in sorted(files):
            p = Path(base) / name
            if p.is_symlink(): continue
            if name in SECRET_NAMES or name.startswith('.env.') or any(x in name.lower() for x in ('secret','credential','private-key')): continue
            if p.suffix.lower() in TEXT_EXTS or name in {'Dockerfile','Makefile','Procfile','Justfile'}:
                try:
                    if p.stat().st_size <= 1_500_000: yield p
                except OSError: pass

def line_of(text, pos): return text.count('\n', 0, pos) + 1

def rec(kind, rid, name, path, line=1, symbol=None, description='', confidence='VERIFIED', method='static-parser', tier='inventory'):
    if tier in PATTERN_TIERS and confidence == 'VERIFIED': confidence = 'INFERRED'  # never claim more than the method supports
    return {'id':rid,'kind':kind,'name':name,'path':path,'line':line,'symbol':symbol or name,'description':description,'confidence':confidence,'verification':'VERIFIED' if confidence=='VERIFIED' else 'INFERRED','discovery_method':method,'extraction':tier}

def extract_file(path, text):
    ext = Path(path).suffix.lower(); rows=[]; imports=[]; symbols=[]; tags=[]
    lang = {'.py':'Python','.pyi':'Python','.js':'JavaScript','.jsx':'JavaScript/JSX','.ts':'TypeScript','.tsx':'TypeScript/TSX','.java':'Java','.kt':'Kotlin','.go':'Go','.rs':'Rust','.rb':'Ruby','.php':'PHP','.cs':'C#','.vue':'Vue','.svelte':'Svelte','.sql':'SQL'}.get(ext, 'Config/Markup')
    is_code = ext in CODE_EXTS
    py = ext in {'.py','.pyi'}
    ftier = 'ast' if py else 'pattern' if ext in {'.js','.jsx','.ts','.tsx','.mjs','.cjs','.vue','.svelte','.java'} else 'minimal' if is_code else 'inventory'
    truncated = 0
    ts_res = TS.extract(ext, text, path, FRAMEWORKS) if (TS and TS.supported(ext)) else None
    if ts_res is not None: ftier = 'tree-sitter'
    unresolved = {}; parse_errors = 0
    module_id = ('MOD-' if is_code else 'FILE-') + sha(path)[:10].upper()
    rows.append(rec('module' if is_code else 'file', module_id, Path(path).stem or path, path, 1, description=f'{lang} source module; purpose requires source-level interpretation.' if is_code else f'{lang} repository file; purpose requires source-level interpretation.', method='file-inventory',tier='inventory'))
    def add(kind, name, line, desc='', symbol=None, confidence='VERIFIED', tier=None):
        rid = {'symbol':'SYM','route':'ROUTE','api':'API','entity':'ENT','test':'TEST','integration':'INT','ai_component':'AI','media_component':'MEDIA','config':'CFG','frontend_component':'UI','database_model':'DBM'}.get(kind,'REC') + '-' + sha(f'{path}:{kind}:{name}')[:10].upper()
        _t=tier or ('ast' if py else 'pattern'); rows.append(rec(kind,rid,name,path,line,symbol,desc,confidence,{'ast':'ast-extractor','tree-sitter':'tree-sitter','adapter':'framework-adapter'}.get(_t,'language-aware-pattern'),_t))
        return rid
    if ext in {'.py','.pyi'}:
        try:
            tree=ast.parse(text)
            for n in ast.walk(tree):
                if isinstance(n,(ast.Import,ast.ImportFrom)):
                    names=[a.name for a in n.names] if isinstance(n,ast.Import) else [n.module or '']
                    imports.extend([x for x in names if x])
                if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
                    symbols.append(n.name); add('symbol',n.name,n.lineno,'Python '+('class' if isinstance(n,ast.ClassDef) else 'function/async function'),n.name)
                    if isinstance(n,ast.ClassDef):
                        bases=' '.join(ast.unparse(b) if hasattr(ast,'unparse') else '' for b in n.bases)
                        if re.search(r'Model|Base|DeclarativeBase|Document',bases): add('database_model',n.name,n.lineno,'Python model class',n.name)
                if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
                    dec=' '.join(ast.unparse(d) if hasattr(ast,'unparse') else '' for d in n.decorator_list)
                    if re.search(r'route\(|get\(|post\(|put\(|patch\(|delete\(|api_view|path\(',dec):
                        lit=None
                        for d in n.decorator_list:
                            if isinstance(d,ast.Call) and d.args and isinstance(d.args[0],ast.Constant) and isinstance(d.args[0].value,str): lit=d.args[0].value; break
                        if lit is None and any(isinstance(d,ast.Call) and d.args for d in n.decorator_list): unresolved['non-literal-route-path']=unresolved.get('non-literal-route-path',0)+1
                        add('api',n.name,n.lineno,'Python route/view inferred from decorator'+(f' (path {lit})' if lit else ''),n.name,'INFERRED','adapter')
                if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id in ('path','re_path') and Path(path).name=='urls.py':
                    a0=n.args[0] if n.args else None
                    if isinstance(a0,ast.Constant) and isinstance(a0.value,str): add('route',a0.value or '/',n.lineno,'Django URL pattern (urls.py)',None,'INFERRED','adapter')
                    else: unresolved['non-literal-route-path']=unresolved.get('non-literal-route-path',0)+1
            if 'test' in Path(path).name.lower() or '/tests/' in '/'+path.lower(): add('test',Path(path).stem,1,'Test file identified by name/path','', 'INFERRED','heuristic')
        except (SyntaxError, ValueError):
            ftier = 'ast-failed'
    elif ts_res is not None:
        imports.extend(ts_res['imports']); unresolved = ts_res['unresolved']; parse_errors = ts_res['parse_errors']
        for kind_, name_, line_, desc_, symbol_, conf_, tier_ in ts_res['rows']:
            if kind_ == 'symbol': symbols.append(name_)
            add(kind_, name_, line_, desc_, symbol_, conf_, tier_)
        if ext != '.go' and re.search(r'\.(test|spec)\.', path): add('test', Path(path).stem, 1, 'Test file identified by name/path', '', 'INFERRED', 'heuristic')
    elif ext in {'.js','.jsx','.ts','.tsx','.mjs','.cjs','.vue','.svelte'}:
        for m in re.finditer(r"(?:import|export)\s+(?:type\s+)?(?:[^;\n]*?\s+from\s+)?['\"]([^'\"]+)['\"]",text): imports.append(m.group(1))
        for m in re.finditer(r'\b(?:export\s+)?(?:default\s+)?(?:function|class|const|let)\s+([A-Z_$][\w$]*)',text):
            name=m.group(1); symbols.append(name); add('symbol',name,line_of(text,m.start()),'JavaScript/TypeScript exported or declared symbol',name)
            if name[:1].isupper() and (ext in {'.jsx','.tsx','.vue','.svelte'} or re.search(r'<'+re.escape(name)+r'\b',text)): add('frontend_component',name,line_of(text,m.start()),'Frontend component candidate',name,'INFERRED')
        for m in re.finditer(r'\b(?:path|route)\s*:\s*[\'\"]([^\'\"]+)',text): add('route',m.group(1),line_of(text,m.start()),'Client route declaration')
        for m in re.finditer(r'\b(?:fetch|axios\.(?:get|post|put|patch|delete))\s*\(\s*[`\'\"]([^`\'\"]+)',text): add('api',m.group(1),line_of(text,m.start()),'Client-side API call site')
        if 'test' in Path(path).name.lower() or re.search(r'\.(test|spec)\.',path): add('test',Path(path).stem,1,'Test file identified by name/path','', 'INFERRED','heuristic')
    elif ext == '.java':
        imports += re.findall(r'^\s*import\s+([\w.]+)',text,re.M)
        for m in re.finditer(r'\b(class|interface|enum|record)\s+(\w+)',text):
            name=m.group(2); symbols.append(name); add('symbol',name,line_of(text,m.start()),'Java '+m.group(1),name)
            if re.search(r'@(Entity|Table)\b',text[max(0,m.start()-500):m.start()]): add('database_model',name,line_of(text,m.start()),'JPA entity class',name)
        for m in re.finditer(r'@(Get|Post|Put|Patch|Delete|Request)Mapping\s*(?:\(\s*(?:value\s*=\s*)?["\']([^"\']*)',text): add('api',m.group(2) or m.group(1),line_of(text,m.start()),'Spring mapping annotation')
    else:
        for m in re.finditer(r'^\s*(?:import|from|require\s*\(|use\s+|#include)\s+["\']?([\w./@-]+)',text,re.M): imports.append(m.group(1))
        if 'test' in Path(path).name.lower() or '/tests/' in '/'+path.lower() or '/spec/' in '/'+path.lower(): add('test',Path(path).stem,1,'Test file identified by name/path','', 'INFERRED','heuristic')
    if TS:
        for kind_, name_, line_, desc_, symbol_, conf_, tier_ in TS.file_routes(path, FRAMEWORKS): add(kind_, name_, line_, desc_, symbol_, conf_, tier_)
    for imp in sorted(set(imports)):
        iid='IMP-'+sha(f'{path}:{imp}')[:10].upper()
        rows.append(rec('import',iid,imp,path,1,imp,'Static import/dependency reference','VERIFIED','import-parser','ast' if ftier=='ast' else 'tree-sitter' if ftier=='tree-sitter' else 'pattern'))
    # Cross-cutting markers; these are evidence-bearing discovery records, not quality assessments.
    for pattern, kind, desc in [
        (r'\b(openai|anthropic|langchain|langgraph|llamaindex|transformers|torch|gemini|vertexai)\b','ai_component','AI SDK/model/framework reference'),
        (r'\b(ffmpeg|remotion|moviepy|opencv|pillow|sharp|canvas|render)\b','media_component','Media/rendering library or operation reference'),
        (r'\b(sqlalchemy|django\.db|prisma|typeorm|sequelize|mongoose|EntityManager|JpaRepository)\b','database_model','Database/ORM reference'),
        (r'\b(stripe|aws|s3|gcs|firebase|supabase|redis|rabbitmq|kafka|sendgrid|twilio)\b','integration','External service/integration reference')]:
        hits = list(re.finditer(pattern,text,re.I)); truncated += max(0, len(hits)-8)
        for m in hits[:8]: add(kind,m.group(1),line_of(text,m.start()),desc,m.group(1),'INFERRED','marker')
    if Path(path).name.lower() in {'package.json','pyproject.toml','requirements.txt','pom.xml','build.gradle','build.gradle.kts','cargo.toml','go.mod','dockerfile','docker-compose.yml','docker-compose.yaml','vite.config.js','vite.config.ts','next.config.js','next.config.ts','webpack.config.js'}:
        add('config',Path(path).name,1,'Build, dependency or runtime configuration file',None,'VERIFIED','heuristic')
    return {'path':path,'digest':sha(text),'language':lang,'module_id':module_id,'is_code':is_code,'records':rows,'imports':sorted(set(imports)),'symbols':symbols,'line_count':text.count('\n')+1,'extraction':{'tier':ftier,'truncated_markers':truncated,'unresolved':unresolved,'parse_errors':parse_errors},'extractor':EXTRACTOR_SIG}

def merge_records(new_records, old_records, current_snapshot, changed_paths, impacted_modules, path_to_module):
    """Keep curator-authored fields while refreshing deterministic fields."""
    old_by_id={r.get('id'):r for r in old_records if r.get('id')}
    merged=[]; seen=set()
    for record in new_records:
        old=old_by_id.get(record.get('id'),{})
        if record.get('id'): seen.add(record['id'])
        item={**old, **record}
        path=item.get('path')
        module_id=path_to_module.get(path)
        impacted=bool(path in changed_paths or (module_id and module_id in impacted_modules))
        if old:
            if impacted:
                item['freshness']='STALE'
            elif old.get('last_verified_snapshot'):
                item['freshness']='CURRENT'; item['last_verified_snapshot']=current_snapshot
            else:
                item.setdefault('freshness','UNVERIFIED')
        else:
            item.setdefault('freshness','UNVERIFIED')
        item['snapshot']=current_snapshot
        merged.append(item)
    current_paths=set(path_to_module)
    for oid, old in old_by_id.items():
        if oid in seen: continue
        opath=old.get('path')
        if opath and opath not in current_paths:
            old['freshness']='STALE'
        elif opath and (opath in changed_paths or path_to_module.get(opath) in impacted_modules):
            old['freshness']='STALE'
        else:
            old.setdefault('freshness','UNVERIFIED')
        old['snapshot']=current_snapshot
        merged.append(old)
    return merged

def evidence_paths(value):
    found=set()
    if isinstance(value,dict):
        for k,v in value.items():
            if k in {'path','source_path'} and isinstance(v,str) and v: found.add(v)
            else: found.update(evidence_paths(v))
    elif isinstance(value,list):
        for v in value: found.update(evidence_paths(v))
    return found

TS_LANGS = {'JavaScript', 'JavaScript/JSX', 'TypeScript', 'TypeScript/TSX', 'Go'}

def extraction_coverage(file_records, records, imp_total, imp_resolved):
    langs = {}; unres = Counter()
    for d in file_records.values():
        e = d.get('extraction') or {'tier': 'unknown', 'truncated_markers': 0}
        row = langs.setdefault(d['language'], {'tiers': {}, 'files': 0, 'lines': 0, 'truncated_markers': 0})
        row['tiers'][e['tier']] = row['tiers'].get(e['tier'], 0) + 1
        row['files'] += 1; row['lines'] += d.get('line_count', 0); row['truncated_markers'] += e.get('truncated_markers', 0)
        row['parse_errors'] = row.get('parse_errors', 0) + e.get('parse_errors', 0)
        unres.update(e.get('unresolved') or {})
    warnings = []
    for lang, row in sorted(langs.items()):
        for tier, n in row['tiers'].items():
            if tier in ('pattern', 'minimal', 'ast-failed', 'unknown'):
                hint = f" Optional upgrade: {TS.REQUIREMENTS}" if (TS and lang in TS_LANGS and tier in ('pattern', 'minimal')) else ''
                warnings.append(f"{lang}: {n}/{row['files']} file(s) [{tier}] - {TIER_NOTES.get(tier, 'extraction tier unknown; rebuild with --force')}.{hint}")
        if row.get('parse_errors'): warnings.append(f"{lang}: {row['parse_errors']} file(s) parsed with syntax-tree error nodes (partial parse)")
        if row['truncated_markers']: warnings.append(f"{lang}: {row['truncated_markers']} keyword-marker hit(s) beyond the per-file cap were not recorded")
    by_tier = dict(Counter(r.get('extraction', 'unknown') for r in records))
    return {'by_language': langs, 'records_by_tier': by_tier,
            'imports': {'total': imp_total, 'resolved_to_repo_module': imp_resolved, 'not_resolved': imp_total - imp_resolved,
                        'note': 'not_resolved = external packages, dynamic imports or paths the extractor could not match; never guessed'},
            'unresolved_by_design': ['dynamic imports/requires', 'dependency injection', 'reflection', 'runtime-registered routes', 'routes built from config'],
            'unresolved_observed': dict(unres), 'frameworks_detected': sorted(FRAMEWORKS),
            'tooling': (TS.status() if TS else {'tree_sitter': None, 'languages': {}, 'adapters': [], 'install': 'ts_adapters.py missing'}),
            'warnings': warnings}

def merge_semantic(records, edges, file_records, path_to_module):
    """Add facts ingested from external semantic analyzers. Facts about files that changed since ingest are skipped (stale)."""
    doc = read_json(OUT/'semantic'/'facts.json', {})
    stats = {'tools': [], 'records': 0, 'edges': 0, 'stale_skipped': 0}
    for b in doc.get('batches', []):
        tool = b.get('tool', 'unknown'); stats['tools'].append(tool); digs = b.get('file_digests', {})
        fresh = lambda p: p in file_records and file_records[p].get('digest') == digs.get(p)
        for f in b.get('facts', []):
            if not fresh(f['path']): stats['stale_skipped'] += 1; continue
            rid = 'SEM-' + sha(f"{tool}:{f['path']}:{f['kind']}:{f['name']}:{f.get('line',1)}")[:10].upper()
            records.append(rec(f['kind'], rid, f['name'], f['path'], int(f.get('line', 1)), f.get('symbol'), f.get('description', ''), 'VERIFIED', 'semantic:' + tool, 'semantic')); stats['records'] += 1
        for e in b.get('edges', []):
            sp, tp = e['from_path'], e['to_path']
            if not (fresh(sp) and fresh(tp)): stats['stale_skipped'] += 1; continue
            edges.append({'source': path_to_module[sp], 'target': path_to_module[tp], 'type': e.get('type', 'USES'), 'evidence': {'path': sp, 'line': int(e.get('line', 1))}, 'confidence': 'VERIFIED', 'origin': 'semantic-analyzer', 'tool': tool}); stats['edges'] += 1
    return stats

def ingest(file):
    """Validate and store output of an external analyzer (tsc script, pyright, gopls, SCIP converter...), then refresh."""
    try: doc = json.loads(Path(file).read_text(encoding='utf-8'))
    except Exception as exc: sys.exit(f'cannot read {file}: {exc}')
    errs = []
    if not isinstance(doc.get('tool'), str) or not doc['tool'].strip(): errs.append('tool: non-empty string required (name and version of the analyzer)')
    paths = set()
    for i, f in enumerate(doc.get('facts', [])):
        if not all(isinstance(f.get(k), str) and f.get(k) for k in ('kind', 'name', 'path')) or not isinstance(f.get('line', 1), int): errs.append(f'facts[{i}]: kind, name, path (strings) and integer line required')
        else: paths.add(f['path'])
    for i, e in enumerate(doc.get('edges', [])):
        if not all(isinstance(e.get(k), str) and e.get(k) for k in ('from_path', 'to_path')): errs.append(f'edges[{i}]: from_path and to_path required')
        else: paths.update([e['from_path'], e['to_path']])
    digs = {}
    for p in sorted(paths):
        full = (ROOT / p).resolve()
        if not full.is_relative_to(ROOT.resolve()) or not full.is_file(): errs.append(f'path not a file inside the repository: {p}'); continue
        digs[p] = sha(full.read_text(encoding='utf-8', errors='replace'))
    if errs: sys.exit('ingest rejected:\n  - ' + '\n  - '.join(errs[:30]))
    cur = read_json(OUT/'semantic'/'facts.json', {'batches': []})
    batches = [b for b in cur.get('batches', []) if b.get('tool') != doc['tool']]
    batches.append({'tool': doc['tool'], 'ingested_at': now(), 'file_digests': digs, 'facts': doc.get('facts', []), 'edges': doc.get('edges', [])})
    write_json(OUT/'semantic'/'facts.json', {'batches': batches})
    print(f"Ingested {len(doc.get('facts', []))} fact(s), {len(doc.get('edges', []))} edge(s) from {doc['tool']}; facts are pinned to the current file digests and go stale if those files change.")
    build(False, True)

def build(force=False, changed_only=False):
    global FRAMEWORKS, EXTRACTOR_SIG
    FRAMEWORKS = TS.detect_frameworks(ROOT) if TS else set()
    EXTRACTOR_SIG = ('builtin' if not TS else TS.signature()) + '|' + ','.join(sorted(FRAMEWORKS))
    OUT.mkdir(parents=True,exist_ok=True)
    old_manifest=read_json(OUT/'manifest.json',{})
    if old_manifest.get('extraction_version') not in (None, SCHEMA_VERSION): force=True
    cache_obj=read_json(CACHE,{'files':{}})
    old_cache=cache_obj.get('files',{}) if isinstance(cache_obj,dict) and isinstance(cache_obj.get('files',{}),dict) else {}
    file_records={}; parsed=0; reused=0; deleted=[]
    current=set()
    for p in walk_files():
        path=rel(p); current.add(path)
        try: content=p.read_text(encoding='utf-8',errors='replace')
        except Exception: continue
        digest=sha(content); old=old_cache.get(path)
        if not force and old and old.get('digest')==digest and old.get('extractor')==EXTRACTOR_SIG:
            file_records[path]=old; reused+=1
        else:
            file_records[path]=extract_file(path,content); parsed+=1
    deleted=sorted(set(old_cache)-current)
    changed_paths={path for path,d in file_records.items() if not old_cache.get(path) or old_cache[path].get('digest')!=d.get('digest')}
    changed_paths.update(deleted)
    records=[]; modules=[]; edges=[]; source_index=[]
    path_to_module={p:d['module_id'] for p,d in file_records.items()}
    module_by_name={Path(p).stem:mid for p,mid in path_to_module.items()}
    imp_total=imp_resolved=0
    for path,d in sorted(file_records.items()):
        records.extend(d['records'])
        if d.get('is_code'):
            modules.append({'id':d['module_id'],'path':path,'name':Path(path).stem,'language':d['language'],'line_count':d['line_count'],'digest':d['digest']})
        source_index.append({'path':path,'digest':d['digest'],'language':d['language'],'line_count':d['line_count'],'module_id':d['module_id']})
        for imp in d['imports']:
            target=None; imp_total+=1
            norm=imp.replace('.','/').replace('\\','/')
            for candidate,mid in path_to_module.items():
                stem=Path(candidate).with_suffix('').as_posix()
                if norm.endswith(stem) or stem.endswith(norm) or Path(candidate).stem==imp.split('/')[-1].split('.')[-1]:
                    target=mid; break
            if target: imp_resolved+=1
            if target and target!=d['module_id']:
                edges.append({'source':d['module_id'],'target':target,'type':'IMPORTS','evidence':{'path':path,'line':1},'confidence':'INFERRED','origin':'static-extractor'})
    semantic_stats = merge_semantic(records, edges, file_records, path_to_module)
    # Product features/workflows are curated by the Chair from source evidence.
    # Include them in the canonical graph when present; do not infer them from file names.
    feature_file=OUT/'product'/'features.json'; workflow_file=OUT/'product'/'workflows.json'
    if not feature_file.exists(): write_json(feature_file,{'features':[],'note':'Populate from product brief and source evidence; keep intent distinct from observed implementation.'})
    if not workflow_file.exists(): write_json(workflow_file,{'workflows':[],'note':'Populate only after tracing complete user-visible or system workflows.'})
    features=read_json(feature_file,{'features':[]}).get('features',[])
    workflows=read_json(workflow_file,{'workflows':[]}).get('workflows',[])
    # Compute changed modules and their reverse import-dependency closure.
    changed_module_ids={path_to_module[path] for path in changed_paths if path in path_to_module}
    impacted_modules=set(changed_module_ids)
    import_edges=[e for e in edges if e.get('type')=='IMPORTS']
    grew=True
    while grew:
        grew=False
        for edge in import_edges:
            if edge.get('target') in impacted_modules and edge.get('source') not in impacted_modules:
                impacted_modules.add(edge['source']); grew=True
    snapshot={'git_head':git('rev-parse','HEAD'),'tree_digest':sha('|'.join(f"{x['path']}:{x['digest']}" for x in source_index)),'dirty':bool(git('status','--porcelain'))}
    current_snapshot=snapshot['git_head'] if snapshot['git_head']!='unknown' else snapshot['tree_digest']
    previous_modules=read_json(OUT/'architecture'/'modules.json',{}).get('modules',[])
    modules=merge_records(modules,previous_modules,current_snapshot,changed_paths,impacted_modules,path_to_module)
    def assess_curated(item, kind):
        if kind=='feature':
            refs=item.get('intended',{}).get('sources',[])+item.get('observed',{}).get('sources',[])
        else:
            refs=[step.get('source',{}) for step in item.get('steps',[])]
        paths={ref.get('path') for ref in refs if ref.get('path')}
        cited_modules={path_to_module[path] for path in paths if path in path_to_module}
        impacted=bool(paths & changed_paths or cited_modules & impacted_modules)
        previously_verified=item.get('last_verified_snapshot')
        if previously_verified==current_snapshot:
            item['freshness']='CURRENT'
        elif impacted:
            item['freshness']='STALE'
        elif previously_verified:
            item['freshness']='CURRENT'; item['last_verified_snapshot']=current_snapshot
        else:
            item['freshness']='UNVERIFIED'
        item['snapshot']=current_snapshot
        return item['freshness']
    for feature in features: assess_curated(feature,'feature')
    for workflow in workflows: assess_curated(workflow,'workflow')
    stale_features=sum(1 for x in features if x.get('freshness')=='STALE')
    stale_workflows=sum(1 for x in workflows if x.get('freshness')=='STALE')
    # Group file records into navigable module map; links to source modules are deterministic.
    bykind=Counter(r['kind'] for r in records)
    nodes=[{'id':m['id'],'type':'module','label':m['name'],'path':m['path'],'origin':'static-extractor'} for m in modules]
    nodes.extend({'id':r['id'],'type':'file','label':r['name'],'path':r['path'],'origin':'static-extractor'} for r in records if r['kind']=='file')
    for r in records:
        if r['kind'] not in {'module','file','import'}:
            nodes.append({'id':r['id'],'type':r['kind'],'label':r['name'],'path':r['path'],'line':r['line'],'origin':'static-extractor'})
            edges.append({'source':r['id'],'target':next((m['id'] for m in modules if m['path']==r['path']),path_to_module.get(r['path'],'')),'type':'DEFINED_IN','evidence':{'path':r['path'],'line':r['line']},'confidence':r['confidence'],'origin':'static-extractor'})
    for feature in features:
        fid=feature.get('id')
        if not fid: continue
        nodes.append({'id':fid,'type':'feature','label':feature.get('name',fid),'origin':'curated'})
        observed=feature.get('observed',{})
        for src in observed.get('sources',[]):
            path=src.get('path'); target=path_to_module.get(path)
            if target:
                edges.append({'source':fid,'target':target,'type':'IMPLEMENTS','evidence':{'path':path,'line':src.get('line_start',1)},'confidence':('PARTIAL' if feature.get('freshness')=='STALE' else observed.get('confidence','INFERRED')),'freshness':feature.get('freshness','UNVERIFIED'),'origin':'curated','last_verified_snapshot':feature.get('last_verified_snapshot')})
        for wid in feature.get('related_workflows',[]):
            if any(w.get('id')==wid for w in workflows) and observed.get('sources'):
                edges.append({'source':fid,'target':wid,'type':'USES','evidence':{'path':observed['sources'][0].get('path',''),'line':observed['sources'][0].get('line_start',1)},'confidence':('PARTIAL' if feature.get('freshness')=='STALE' else feature.get('confidence','INFERRED')),'freshness':feature.get('freshness','UNVERIFIED'),'origin':'curated','last_verified_snapshot':feature.get('last_verified_snapshot')})
    for workflow in workflows:
        wid=workflow.get('id')
        if not wid: continue
        nodes.append({'id':wid,'type':'workflow','label':workflow.get('name',wid),'origin':'curated'})
        for step in workflow.get('steps',[]):
            src=step.get('source',{}); path=src.get('path'); target=path_to_module.get(path)
            if target:
                edges.append({'source':wid,'target':target,'type':'USES','evidence':{'path':path,'line':src.get('line_start',1)},'confidence':('PARTIAL' if workflow.get('freshness')=='STALE' else step.get('confidence',workflow.get('confidence','INFERRED'))),'freshness':workflow.get('freshness','UNVERIFIED'),'origin':'curated','last_verified_snapshot':workflow.get('last_verified_snapshot')})
    previous_graph=read_json(OUT/'architecture'/'relationships.json',{'nodes':[],'edges':[]})
    manual_nodes=[n for n in previous_graph.get('nodes',[]) if n.get('origin')=='manual']
    manual_edges=[e for e in previous_graph.get('edges',[]) if e.get('origin')=='manual']
    for node in manual_nodes:
        npath=node.get('path')
        if npath in changed_paths or (path_to_module.get(npath) in impacted_modules): node['freshness']='STALE'
    for edge in manual_edges:
        ev=edge.get('evidence',{}); epath=ev.get('path')
        if epath in changed_paths or (path_to_module.get(epath) in impacted_modules):
            edge['freshness']='STALE'; edge['confidence']='PARTIAL'
    node_map={n['id']:n for n in nodes}
    previous_nodes={n.get('id'):n for n in previous_graph.get('nodes',[]) if n.get('id')}
    for n in manual_nodes: node_map[n['id']]={**node_map.get(n['id'],{}),**n}
    for edge in manual_edges:
        for endpoint in (edge.get('source'),edge.get('target')):
            if endpoint and endpoint not in node_map and endpoint in previous_nodes:
                stale_node={**previous_nodes[endpoint],'origin':'manual','freshness':'STALE'}
                node_map[endpoint]=stale_node
    edge_map={(e.get('source'),e.get('target'),e.get('type')):e for e in edges}
    for e in manual_edges: edge_map[(e.get('source'),e.get('target'),e.get('type'))]=e
    nodes=list(node_map.values()); edges=list(edge_map.values())
    graph={'nodes':nodes,'edges':edges}
    for r in records:

        r['snapshot']=snapshot['git_head'] if snapshot['git_head']!='unknown' else snapshot['tree_digest']
        r['last_verified_snapshot']=r['snapshot'] if r.get('confidence')=='VERIFIED' else None
    for e in edges:
        e['snapshot']=snapshot['git_head'] if snapshot['git_head']!='unknown' else snapshot['tree_digest']
        if e.get('confidence')=='VERIFIED' and not e.get('last_verified_snapshot'): e['last_verified_snapshot']=e['snapshot']
        elif e.get('origin')=='static-extractor' and e.get('confidence')!='VERIFIED': e['last_verified_snapshot']=None
    for src in source_index: src['snapshot']=snapshot['git_head'] if snapshot['git_head']!='unknown' else snapshot['tree_digest']
    write_json(CACHE,{'files':file_records,'updated_at':now()})
    accepted_log=OUT/'discrepancies'/'accepted-log.json'
    if not accepted_log.exists(): write_json(accepted_log,{'entries':[]})
    write_json(feature_file,{'features':features})
    write_json(workflow_file,{'workflows':workflows})
    write_json(OUT/'evidence'/'source-index.json',{'snapshot':snapshot,'sources':source_index,'records':records})
    write_json(OUT/'architecture'/'modules.json',{'modules':modules})
    write_json(OUT/'architecture'/'relationships.json',graph)
    old_flows=read_json(OUT/'architecture'/'data-flows.json',{'flows':[]})
    old_flows.setdefault('note','Populate only after tracing concrete read/write and call paths. Do not infer complete business flows from imports.')
    for flow in old_flows.get('flows',[]):
        fpaths=evidence_paths(flow)
        if fpaths & changed_paths or any(path_to_module.get(x) in impacted_modules for x in fpaths): flow['freshness']='STALE'
        elif flow.get('last_verified_snapshot'): flow['freshness']='CURRENT'; flow['last_verified_snapshot']=current_snapshot
        else: flow.setdefault('freshness','UNVERIFIED')
        flow['snapshot']=current_snapshot
    old_front=read_json(OUT/'interfaces'/'frontend.json',{})
    old_api=read_json(OUT/'interfaces'/'apis.json',{})
    old_int=read_json(OUT/'interfaces'/'integrations.json',{})
    old_tests=read_json(OUT/'testing'/'coverage-map.json',{})
    frontend={**old_front,'components':merge_records([r for r in records if r['kind']=='frontend_component'],old_front.get('components',[]),current_snapshot,changed_paths,impacted_modules,path_to_module),
              'routes':merge_records([r for r in records if r['kind']=='route'],old_front.get('routes',[]),current_snapshot,changed_paths,impacted_modules,path_to_module)}
    apis={**old_api,'apis':merge_records([r for r in records if r['kind']=='api'],old_api.get('apis',[]),current_snapshot,changed_paths,impacted_modules,path_to_module)}
    integrations={**old_int,'integrations':merge_records([r for r in records if r['kind']=='integration'],old_int.get('integrations',[]),current_snapshot,changed_paths,impacted_modules,path_to_module)}
    coverage={**old_tests,'tests':merge_records([r for r in records if r['kind']=='test'],old_tests.get('tests',[]),current_snapshot,changed_paths,impacted_modules,path_to_module)}
    coverage.setdefault('note','Test-to-feature coverage requires direct test and behaviour mapping; absence of a link is not proof of missing coverage.')
    stale_modules=sum(1 for x in modules if x.get('freshness')=='STALE')
    stale_flows=sum(1 for x in old_flows.get('flows',[]) if x.get('freshness')=='STALE')
    stale_interfaces=sum(1 for group in (frontend.get('components',[]),frontend.get('routes',[]),apis.get('apis',[]),integrations.get('integrations',[])) for x in group if x.get('freshness')=='STALE')
    stale_tests=sum(1 for x in coverage.get('tests',[]) if x.get('freshness')=='STALE')
    stale_manual_edges=sum(1 for x in edges if x.get('origin')=='manual' and x.get('freshness')=='STALE')
    manifest={'schema_version':SCHEMA_VERSION,'created_at':now(),'updated_at':now(),'snapshot':snapshot,'extraction_version':SCHEMA_VERSION,'files_scanned':len(source_index),'files_parsed':parsed,'files_reused':reused,'files_deleted':deleted,'coverage':{'languages':dict(Counter(x['language'] for x in source_index)),'record_types':dict(bykind),'source_files_indexed':len(source_index),'product_features':len(features),'workflows':len(workflows),'graph_nodes':len(nodes),'graph_edges':len(edges),'stale_features':stale_features,'stale_workflows':stale_workflows,'stale_modules':stale_modules,'stale_data_flows':stale_flows,'stale_interfaces':stale_interfaces,'stale_tests':stale_tests,'stale_manual_edges':stale_manual_edges,'extraction':extraction_coverage(file_records,records,imp_total,imp_resolved),'semantic':semantic_stats,'parser_notes':['Python uses the Python AST (tier ast). JavaScript/TypeScript/Java use regex fallback (tier pattern); other code languages are inventory/import/marker only (tier minimal). Records from pattern/heuristic/marker/minimal tiers are never VERIFIED. Unresolved relationships stay unresolved rather than guessed. See `atlas.py coverage`.','Framework-specific routes and relationships may be partial; specialists must inspect source directly.']},'refresh_state':('PARTIAL' if any((stale_features,stale_workflows,stale_modules,stale_flows,stale_interfaces,stale_tests,stale_manual_edges)) else 'CURRENT')}
    write_json(OUT/'architecture'/'data-flows.json',old_flows)
    write_json(OUT/'interfaces'/'frontend.json',frontend)
    write_json(OUT/'interfaces'/'apis.json',apis)
    write_json(OUT/'interfaces'/'integrations.json',integrations)
    write_json(OUT/'testing'/'coverage-map.json',coverage)
    write_json(OUT/'manifest.json',manifest)
    index={'schema_version':SCHEMA_VERSION,'snapshot':snapshot,'manifest':'manifest.json','sections':['product/features.json','product/workflows.json','architecture/modules.json','architecture/relationships.json','architecture/data-flows.json','interfaces/frontend.json','interfaces/apis.json','interfaces/integrations.json','testing/coverage-map.json','evidence/source-index.json'],'counts':{'modules':len(modules),'nodes':len(nodes),'edges':len(edges),'records':len(records),'stale_features':stale_features,'stale_workflows':stale_workflows,'stale_modules':stale_modules,'stale_data_flows':stale_flows,'stale_interfaces':stale_interfaces,'stale_tests':stale_tests,'stale_manual_edges':stale_manual_edges},'description':'Descriptive repository map. Not a specialist assessment.'}
    write_json(OUT/'atlas.json',index)
    if changed_only:
        print(f"Atlas refreshed: parsed={parsed}, reused={reused}, deleted={len(deleted)}; graph rebuilt from current file records.")
    else: print(f"Atlas built: files={len(source_index)}, parsed={parsed}, reused={reused}, modules={len(modules)}, records={len(records)}, edges={len(edges)}.")
    write_digests()

def all_records():
    return read_json(OUT/'evidence'/'source-index.json',{}).get('records',[])
def ensure():
    if not (OUT/'atlas.json').exists(): sys.exit('Atlas missing. Run: python3 .claude/skills/codebase-atlas/scripts/atlas.py build')
def status():
    ensure(); idx=read_json(OUT/'atlas.json',{}); m=read_json(OUT/'manifest.json',{})
    dirty=[]
    src={x['path']:x['digest'] for x in read_json(OUT/'evidence'/'source-index.json',{}).get('sources',[])}
    for p in walk_files():
        try:
            if src.get(rel(p))!=sha(p.read_text(encoding='utf-8',errors='replace')): dirty.append(rel(p))
        except Exception: pass
    deleted=sorted(set(src)-{rel(p) for p in walk_files()})
    print(f"Atlas schema: {idx.get('schema_version')}\nGit HEAD: {m.get('snapshot',{}).get('git_head')}\nTree digest: {m.get('snapshot',{}).get('tree_digest')}\nFiles: {m.get('files_scanned')} · Modules: {idx.get('counts',{}).get('modules')} · Nodes: {idx.get('counts',{}).get('nodes')} · Edges: {idx.get('counts',{}).get('edges')}\nChanged: {len(dirty)} · Deleted: {len(deleted)}")
    if dirty or deleted: print('Source freshness: STALE — run atlas.py refresh --changed')
    else: print('Source freshness: CURRENT')
    cov=m.get('coverage',{}); stale_counts={k:v for k,v in cov.items() if k.startswith('stale_') and v}
    if stale_counts: print('Atlas content: PARTIAL · '+', '.join(f'{k.removeprefix("stale_")}={v}' for k,v in stale_counts.items())+'; re-trace affected records and update last_verified_snapshot after verification')
    ex=m.get('coverage',{}).get('extraction')
    if ex: print(f"Extraction: {len(ex['warnings'])} coverage warning(s); run atlas.py coverage")
    if dirty: print('Changed paths: '+', '.join(dirty[:30]))
    if deleted: print('Deleted paths: '+', '.join(deleted[:30]))
def coverage():
    ensure(); m=read_json(OUT/'manifest.json',{}); ex=m.get('coverage',{}).get('extraction')
    if not ex: sys.exit('No extraction coverage recorded. Run: atlas.py build --force')
    print('Extraction coverage (how much of this map is parsed vs guessed)')
    print(f"{'Language':<18}{'Files':>6}{'Lines':>9}  Tiers")
    for lang,row in sorted(ex['by_language'].items(), key=lambda kv: -kv[1]['files']):
        print(f"{lang:<18}{row['files']:>6}{row['lines']:>9}  "+', '.join(f'{t}={n}' for t,n in sorted(row['tiers'].items())))
    print('Records by tier: '+', '.join(f'{t}={n}' for t,n in sorted(ex['records_by_tier'].items())))
    i=ex['imports']; print(f"Imports: {i['total']} total, {i['resolved_to_repo_module']} resolved to repo modules, {i['not_resolved']} not resolved ({i['note']})")
    t=ex.get('tooling',{}); langs=', '.join(f"{k}={'yes' if v else 'no'}" for k,v in t.get('languages',{}).items())
    print(f"Tooling: tree-sitter={t.get('tree_sitter') or 'not installed'} ({langs or 'no grammars'}); adapters: {', '.join(t.get('adapters',[])) or 'none'}")
    if ex.get('frameworks_detected'): print('Frameworks detected: '+', '.join(ex['frameworks_detected']))
    sem=m.get('coverage',{}).get('semantic',{})
    print(f"Semantic analyzers: {', '.join(sem.get('tools',[])) or 'none ingested'}"+(f" ({sem.get('records',0)} records, {sem.get('edges',0)} edges, {sem.get('stale_skipped',0)} stale skipped)" if sem.get('tools') else ''))
    uo=ex.get('unresolved_observed',{})
    print('Unresolved in this repository (counted, never guessed): '+(', '.join(f'{k}={v}' for k,v in sorted(uo.items())) or 'none observed'))
    print('Unresolved by design: '+'; '.join(ex['unresolved_by_design']))
    if ex['warnings']: print('Warnings:'); [print('  - '+w) for w in ex['warnings']]
    else: print('Warnings: none')

def search(q):
    ensure(); q=q.lower(); hits=[]
    for r in all_records():
        hay=' '.join(str(r.get(k,'')) for k in ('id','kind','name','path','symbol','description')).lower()
        if q in hay: hits.append(r)
    for r in hits[:80]: print(f"{r['id']} | {r['kind']} | {r['name']} | {r['path']}:{r['line']} | {r['confidence']}")
    print(f'-- {len(hits)} match(es)'+(' (showing first 80)' if len(hits)>80 else ''))
def lookup(kind, query):
    ensure(); q=query.lower(); rows=[]
    for r in all_records():
        if kind=='module' and (r['kind']=='module' or r['path']==query or r['id'].lower()==q) and (q in r['id'].lower() or q in r['name'].lower() or r['path']==query): rows.append(r)
        elif kind!='module' and r['kind']==kind and (q in r['id'].lower() or q in r['name'].lower()): rows.append(r)
    extra=[]
    if kind in {'feature','workflow'}:
        file=OUT/'product'/('features.json' if kind=='feature' else 'workflows.json')
        key='features' if kind=='feature' else 'workflows'
        for x in read_json(file,{key:[]}).get(key,[]):
            if q in json.dumps(x).lower(): extra.append(x)
    if not rows and not extra: print(f'No {kind} match for: {query}'); return
    for r in rows+extra: print(json.dumps(r,indent=2,ensure_ascii=False))
def dependencies(query):
    ensure(); graph=read_json(OUT/'architecture'/'relationships.json',{'nodes':[],'edges':[]}); nodes=graph['nodes']; edges=graph['edges']
    matches=[n for n in nodes if query.lower() in n['id'].lower() or query.lower() in n.get('path','').lower() or query.lower() in n.get('label','').lower()]
    if not matches: print('No node match'); return
    ids={n['id'] for n in matches}
    for n in matches[:20]: print(f"NODE {n['id']} | {n.get('label')} | {n.get('path')}")
    for e in edges:
        if e['source'] in ids or e['target'] in ids: print(f"{e['source']} -[{e['type']}]-> {e['target']} ({e['confidence']})")
def verify():
    ensure(); errors=[]; warnings=[]; records=all_records(); ids={r['id'] for r in records}
    manifest=read_json(OUT/'manifest.json',{}); coverage=manifest.get('coverage',{})
    for key,value in coverage.items():
        if key.startswith('stale_') and value: warnings.append(f"{key}: {value} curated record(s) require re-tracing")
    seen=set()
    for r in records:
        if r.get('id') in seen: errors.append(f"duplicate record id: {r.get('id')}")
        seen.add(r.get('id'))
        if r.get('confidence') not in {'VERIFIED','INFERRED','PARTIAL','UNVERIFIED'}: errors.append(f"invalid confidence: {r.get('id')}")
        if r.get('extraction') in PATTERN_TIERS and r.get('confidence')=='VERIFIED': errors.append(f"overclaimed confidence (VERIFIED from {r.get('extraction')} tier): {r.get('id')}")
        p=ROOT/r.get('path','')
        if not p.is_file(): errors.append(f"missing source: {r['id']} -> {r.get('path')}"); continue
        try: lines=p.read_text(encoding='utf-8',errors='replace').splitlines()
        except Exception: errors.append(f"unreadable source: {r['path']}"); continue
        if r.get('line',1)<1 or (lines and r.get('line',1)>len(lines)+1): errors.append(f"line out of range: {r['id']} -> {r['path']}:{r.get('line')}")
    def check_ref(path, line_start=1, line_end=None, label='record'):
        p=(ROOT/path).resolve() if path else None
        if p is not None and not p.is_relative_to(ROOT.resolve()):
            errors.append(f"evidence path escapes repository for {label}: {path}"); return
        if p is None or not p.is_file():
            errors.append(f"missing evidence source for {label}: {path}"); return
        try: count=len(p.read_text(encoding='utf-8',errors='replace').splitlines())
        except Exception:
            errors.append(f"unreadable evidence source for {label}: {path}"); return
        if line_start < 1 or line_start > count+1 or (line_end is not None and (line_end < line_start or line_end > count)):
            errors.append(f"evidence line range invalid for {label}: {path}:{line_start}-{line_end}")
    graph=read_json(OUT/'architecture'/'relationships.json',{'nodes':[],'edges':[]}); node_list=graph['nodes']; nodeids={n['id'] for n in node_list}
    if len(nodeids)!=len(node_list): errors.append('duplicate graph node IDs')
    for e in graph['edges']:
        if e.get('confidence') not in {'VERIFIED','INFERRED','PARTIAL','UNVERIFIED'}: errors.append(f"invalid edge confidence: {e}")
        if e['source'] not in nodeids or e['target'] not in nodeids: errors.append(f"dangling edge: {e}")
        ev=e.get('evidence',{}); before=len(errors); check_ref(ev.get('path'),ev.get('line',1),label=f"edge {e.get('source')}->{e.get('target')}")
        if e.get('freshness')=='STALE':
            warnings.append(f"stale relationship: {e.get('source')} -[{e.get('type')}]-> {e.get('target')}")
            if len(errors)>before: warnings.extend(errors[before:]); del errors[before:]
    features=read_json(OUT/'product'/'features.json',{'features':[]}).get('features',[])
    workflows=read_json(OUT/'product'/'workflows.json',{'workflows':[]}).get('workflows',[])
    feature_ids=[x.get('id') for x in features]
    workflow_ids=[x.get('id') for x in workflows]
    if len(feature_ids)!=len(set(feature_ids)): errors.append('duplicate feature IDs')
    if len(workflow_ids)!=len(set(workflow_ids)): errors.append('duplicate workflow IDs')
    for feature in features:
        for group in ('intended','observed'):
            for src in feature.get(group,{}).get('sources',[]):
                before=len(errors); check_ref(src.get('path'),src.get('line_start',1),src.get('line_end'),label=f"feature {feature.get('id')} {group}")
                if feature.get('freshness')=='STALE':
                    warnings.append(f"stale feature evidence: {feature.get('id')} ({group})")
                    if len(errors)>before: warnings.extend(errors[before:]); del errors[before:]
    for workflow in workflows:
        for step in workflow.get('steps',[]):
            src=step.get('source',{}); before=len(errors); check_ref(src.get('path'),src.get('line_start',1),src.get('line_end'),label=f"workflow {workflow.get('id')} step {step.get('order')}")
            if workflow.get('freshness')=='STALE':
                warnings.append(f"stale workflow evidence: {workflow.get('id')} step {step.get('order')}")
                if len(errors)>before: warnings.extend(errors[before:]); del errors[before:]
    if warnings: print('WARNINGS (stale curated evidence):\n'+'\n'.join(warnings))
    if errors:
        print('\n'.join(errors)); print(f'FAILED: {len(errors)} issue(s)'); return 1
    print(f'PASS: {len(records)} evidence records and {len(graph["edges"])} edges; all current source paths and line references valid.'); return 0

# Per-role digest: a short, factual slice of the Atlas so specialists need not read the Atlas SKILL or browse JSON.
_AI_KW = ('llm','prompt','openai','anthropic','claude','gpt','embed','agent','completion','model')
_MEDIA_KW = ('render','video','audio','image','ffmpeg','export','encode','media','pipeline','subtitle','font')
DIGEST_ROLES = {
    'PMV': {'kinds':('route',),'files':('features','workflows')},
    'PMS': {'kinds':('module','route'),'files':('features','workflows')},
    'CMP': {'kinds':('route',),'files':('features',)},
    'ARC': {'kinds':('module','integration','api')},
    'FE':  {'kinds':('route','frontend_component','api')},
    'BE':  {'kinds':('api','module','integration')},
    'AI':  {'kinds':('integration','module','test'),'kw':_AI_KW},
    'MED': {'kinds':('module','integration','test'),'kw':_MEDIA_KW},
    'VIS': {'kinds':('route','frontend_component')},
    'UX':  {'kinds':('route','frontend_component','api'),'files':('workflows',)},
    'XAI': {'kinds':('route','frontend_component'),'files':('workflows',),'kw':_AI_KW},
    'DOC': {'kinds':('route','frontend_component')},
    'QA':  {'kinds':('api','integration','test')},
    'CPE': {'kinds':('integration','api'),'kw':_AI_KW+_MEDIA_KW},
    'RED': {'kinds':('integration','api'),'files':('features','workflows')},
    'VER': {'kinds':()},
    'SCR': {'kinds':()},
}
def write_digests(cap=40):
    ensure(); m=read_json(OUT/'manifest.json',{}); ex=m.get('coverage',{}).get('extraction') or {}
    snap=m.get('snapshot',{}); recs=all_records(); d=OUT/'digest'; d.mkdir(parents=True,exist_ok=True)
    head=[f"# Atlas digest (facts and leads only, not findings; open source directly and record your own evidence)",
          f"Snapshot: {snap.get('git_head')} / {snap.get('tree_digest')} · refresh: {m.get('refresh_state')} · files: {m.get('files_scanned')}",
          'Records by tier: '+', '.join(f'{k}={v}' for k,v in sorted((ex.get('records_by_tier') or {}).items())),
          'Coverage warnings: '+('; '.join(ex.get('warnings',[])) or 'none'),
          'More detail: `python3 .claude/skills/codebase-atlas/scripts/atlas.py search|module|dependencies <q>`; a missing item is not proof of absence.','']
    for role,spec in DIGEST_ROLES.items():
        out=list(head); kw=spec.get('kw')
        for kind in spec.get('kinds',()):
            rows=[r for r in recs if r['kind']==kind]
            if kw: rows=[r for r in rows if any(k in (r['name']+' '+r['path']).lower() for k in kw)] if kind in ('module','test','integration') else rows
            out.append(f"## {kind} ({len(rows)})")
            out+= [f"- {r['name']} | {r['path']}:{r['line']} | {r['confidence']}/{r.get('extraction')}" for r in rows[:cap]]
            if len(rows)>cap: out.append(f"- … {len(rows)-cap} more (use atlas.py search)")
        for f in spec.get('files',()):
            items=read_json(OUT/'product'/f'{f}.json',{f:[]}).get(f,[])
            out.append(f"## {f} ({len(items)})")
            out+= [f"- {x.get('id')} {x.get('name')}" for x in items[:cap]]
        (d/f'{role}.md').write_text(chr(10).join(out)+chr(10),encoding='utf-8')
    print(f"Digests written: {d} ({len(DIGEST_ROLES)} roles)")

def repo_map():
    """Generate .review/brief/repo-map.md from the Atlas (no agent tokens)."""
    ensure(); si=read_json(OUT/'evidence'/'source-index.json',{}); srcs=si.get('sources',[]); recs=si.get('records',[])
    top=defaultdict(lambda:{'files':0,'lines':0,'langs':Counter()})
    for s in srcs:
        k=s['path'].split('/')[0] if '/' in s['path'] else '(root)'
        top[k]['files']+=1; top[k]['lines']+=s.get('line_count',0); top[k]['langs'][s.get('language','?')]+=1
    L=['# Repo map (generated from the Codebase Atlas; navigational facts only)','',
       '## Top-level areas','| Area | Files | Lines | Languages |','|---|---|---|---|']
    for k,v in sorted(top.items(),key=lambda kv:-kv[1]['lines']):
        L.append(f"| {k} | {v['files']} | {v['lines']} | "+', '.join(f'{a} {b}' for a,b in v['langs'].most_common(3))+' |')
    mods=[r for r in recs if r['kind']=='module']; by=defaultdict(list)
    for m in mods: by[m['path'].split('/')[0] if '/' in m['path'] else '(root)'].append(m)
    L+=['','## Modules']
    for k,ms in sorted(by.items()):
        L.append(f"- **{k}** ({len(ms)}): "+', '.join(m['path'] for m in ms[:12])+(f' … +{len(ms)-12}' if len(ms)>12 else ''))
    for kind,title in (('route','Routes / UI entry points'),('api','API endpoints and call sites'),('integration','Integrations')):
        rows=[r for r in recs if r['kind']==kind]
        if rows:
            L+=['',f'## {title} ({len(rows)})']+[f"- {r['name']} — {r['path']}:{r['line']} ({r['confidence']})" for r in rows[:30]]
            if len(rows)>30: L.append(f'- … +{len(rows)-30} more (atlas.py search)')
    L+=['','## Ignored (generated/vendored)',', '.join(sorted(IGNORE_DIRS)),'',
        '## Data flow','See `.review/codebase-atlas/architecture/data-flows.json`. The Architect may append up to 10 verified lines here; do not guess.']
    d=ROOT/'.review'/'brief'; d.mkdir(parents=True,exist_ok=True)
    (d/'repo-map.md').write_text(chr(10).join(L)+chr(10),encoding='utf-8'); print(f'Wrote {d/"repo-map.md"}')

def main():
    ap=argparse.ArgumentParser(description=__doc__); sub=ap.add_subparsers(dest='cmd')
    b=sub.add_parser('build'); b.add_argument('--force',action='store_true')
    sub.add_parser('status'); r=sub.add_parser('refresh'); r.add_argument('--changed',action='store_true',required=True)
    s=sub.add_parser('search'); s.add_argument('query')
    for name in ('module','feature','workflow'): x=sub.add_parser(name); x.add_argument('query')
    d=sub.add_parser('dependencies'); d.add_argument('query'); sub.add_parser('verify'); sub.add_parser('coverage'); sub.add_parser('digest'); sub.add_parser('repo-map'); ig=sub.add_parser('ingest'); ig.add_argument('file')
    a=ap.parse_args()
    if a.cmd=='build': build(a.force)
    elif a.cmd=='refresh': build(False,True)
    elif a.cmd=='status': status()
    elif a.cmd=='search': search(a.query)
    elif a.cmd in ('module','feature','workflow'): lookup(a.cmd,a.query)
    elif a.cmd=='dependencies': dependencies(a.query)
    elif a.cmd=='verify': sys.exit(verify())
    elif a.cmd=='coverage': coverage()
    elif a.cmd=='digest': write_digests()
    elif a.cmd=='repo-map': repo_map()
    elif a.cmd=='ingest': ingest(a.file)
    else: ap.print_help()
if __name__=='__main__': main()
