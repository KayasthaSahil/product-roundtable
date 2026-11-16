"""Optional Tree-sitter tier and framework-adapter registry for the Codebase Atlas.

Importing this module never requires third-party packages. If `tree_sitter` and a language grammar are
installed (see requirements-optional.txt) the Atlas parses JavaScript/TypeScript/TSX/Go into real syntax
trees; otherwise `extract()` returns None and atlas.py falls back to its regex tier, clearly labelled.

Tiers produced here
  tree-sitter : syntactic facts read from a real syntax tree (imports, declarations). Exact as syntax.
  adapter     : facts derived from a framework *convention* (Express-style routes, React Router, NestJS
                decorators, Next.js file routes, Go HTTP routers, client fetch/axios calls). Never VERIFIED.

Behaviour that cannot be resolved statically (non-literal route paths, dynamic import/require, non-literal
API URLs) is counted in `unresolved`, never guessed.

Extend with a plugin: drop `adapters/<name>.py` next to SKILL.md defining a function decorated with
`@adapter('javascript', 'typescript', 'tsx')` (example in SKILL.md). Plugins load from the skill
folder only, never from the repository under review.
"""
import importlib.util
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

GRAMMARS = {
    'javascript': ('tree_sitter_javascript', 'language'),
    'typescript': ('tree_sitter_typescript', 'language_typescript'),
    'tsx': ('tree_sitter_typescript', 'language_tsx'),
    'go': ('tree_sitter_go', 'language'),
}
EXT_LANG = {'.js': 'javascript', '.jsx': 'javascript', '.mjs': 'javascript', '.cjs': 'javascript',
            '.ts': 'typescript', '.tsx': 'tsx', '.go': 'go'}
JS_LANGS = {'javascript', 'typescript', 'tsx'}
REQUIREMENTS = 'pip install -r .claude/skills/codebase-atlas/requirements-optional.txt'

_parsers = {}
_state = {'loaded': False, 'version': None, 'missing': []}
ADAPTERS = []  # (languages, fn)


def adapter(*languages):
    """Register a framework adapter: fn(lang, idx, src, path, ctx, out). idx maps node type -> [nodes]."""
    def deco(fn):
        ADAPTERS.append((set(languages), fn))
        return fn
    return deco


def _load():
    if _state['loaded']:
        return
    _state['loaded'] = True
    if os.environ.get('ATLAS_DISABLE_TREE_SITTER'):  # force the stdlib-only baseline (reproducible runs, tests)
        _state['missing'] = sorted(GRAMMARS)
        return
    try:
        import tree_sitter
        from tree_sitter import Language, Parser
    except Exception:
        _state['missing'] = sorted(GRAMMARS)
        return
    try:
        from importlib.metadata import version
        _state['version'] = version('tree-sitter')
    except Exception:
        _state['version'] = 'unknown'
    for key, (mod, fn) in GRAMMARS.items():
        try:
            m = __import__(mod)
            _parsers[key] = Parser(Language(getattr(m, fn)()))
        except Exception:
            _state['missing'].append(key)


def status():
    _load()
    return {'tree_sitter': _state['version'], 'languages': {k: (k in _parsers) for k in sorted(GRAMMARS)},
            'adapters': sorted({fn.__name__ for _, fn in ADAPTERS}), 'install': REQUIREMENTS}


def signature():
    """Changes whenever the available extraction tooling changes, so cached records are re-extracted."""
    _load()
    return 'ts:' + ','.join(sorted(_parsers)) + ':' + str(_state['version']) + ':' + ','.join(sorted({fn.__name__ for _, fn in ADAPTERS}))


def supported(ext):
    _load()
    return EXT_LANG.get(ext) in _parsers


# ---------- helpers ----------
def _txt(n):
    return n.text.decode('utf-8', 'replace') if n is not None and n.text is not None else ''


def _line(n):
    return n.start_point[0] + 1


def _lit(n):
    """Literal string value, or None when the value is not statically known."""
    if n is None:
        return None
    if n.type in ('string', 'interpreted_string_literal', 'raw_string_literal'):
        s = _txt(n)
        return s[1:-1] if len(s) >= 2 else ''
    if n.type == 'template_string':
        if any(c.type == 'template_substitution' for c in n.children):
            return None
        s = _txt(n)
        return s[1:-1] if len(s) >= 2 else ''
    return None


def _tmpl(n):
    """Template/string URL with interpolations normalised to {}; None if not string-like."""
    v = _lit(n)
    if v is not None:
        return v
    if n is not None and n.type == 'template_string':
        parts = []
        for c in n.children:
            if c.type == 'template_substitution':
                parts.append('{}')
            elif c.type in ('string_fragment', 'escape_sequence'):
                parts.append(_txt(c))
        return ''.join(parts)
    return None


def _args(call):
    a = call.child_by_field_name('arguments')
    return [c for c in a.named_children if c.type != 'comment'] if a is not None else []


def _name(n):
    return _txt(n.child_by_field_name('name'))


def _has_jsx(n):
    stack = [n]
    while stack:
        x = stack.pop()
        if x.type in ('jsx_element', 'jsx_self_closing_element', 'jsx_fragment'):
            return True
        stack.extend(x.children)
    return False


# ---------- core syntactic extraction (tier: tree-sitter) ----------
def _core_js(lang, idx, ctx, out, imports, ext):
    for n in idx['import_statement'] + idx['export_statement']:
        s = n.child_by_field_name('source')
        v = _lit(s)
        if v:
            imports.append(v)
    for n in idx['call_expression']:
        f = n.child_by_field_name('function')
        if f is None:
            continue
        a = _args(n)
        if f.type == 'identifier' and _txt(f) == 'require':
            v = _lit(a[0]) if a else None
            if v:
                imports.append(v)
            else:
                ctx['unresolved']['dynamic-require'] += 1
        elif f.type == 'import':
            v = _lit(a[0]) if a else None
            if v:
                imports.append(v)
            else:
                ctx['unresolved']['dynamic-import'] += 1
    for t, label in (('function_declaration', 'function'), ('generator_function_declaration', 'generator function'),
                     ('class_declaration', 'class'), ('abstract_class_declaration', 'abstract class'),
                     ('interface_declaration', 'interface'), ('type_alias_declaration', 'type alias'),
                     ('enum_declaration', 'enum')):
        for n in idx[t]:
            nm = _name(n)
            if not nm:
                continue
            out.append(('symbol', nm, _line(n), f'{label} declaration', nm, 'VERIFIED', 'tree-sitter'))
            if t in ('function_declaration', 'class_declaration') and nm[:1].isupper() and ext in ('.jsx', '.tsx') and _has_jsx(n):
                out.append(('frontend_component', nm, _line(n), 'Component: capitalised declaration containing JSX', nm, 'INFERRED', 'adapter'))
    for n in idx['variable_declarator']:
        v = n.child_by_field_name('value')
        if v is not None and v.type in ('arrow_function', 'function_expression', 'function', 'generator_function'):
            nm = _txt(n.child_by_field_name('name'))
            if nm and re.match(r'^[\w$]+$', nm):
                out.append(('symbol', nm, _line(n), 'function value declaration', nm, 'VERIFIED', 'tree-sitter'))
                if nm[:1].isupper() and ext in ('.jsx', '.tsx') and _has_jsx(v):
                    out.append(('frontend_component', nm, _line(n), 'Component: capitalised function containing JSX', nm, 'INFERRED', 'adapter'))


def _core_go(idx, ctx, out, imports, path):
    for n in idx['import_spec']:
        v = _lit(n.child_by_field_name('path'))
        if v:
            imports.append(v)
    for n in idx['function_declaration']:
        nm = _name(n)
        if nm:
            out.append(('symbol', nm, _line(n), 'Go function', nm, 'VERIFIED', 'tree-sitter'))
            if path.endswith('_test.go') and nm.startswith(('Test', 'Benchmark', 'Fuzz')):
                out.append(('test', nm, _line(n), 'Go test function', nm, 'VERIFIED', 'tree-sitter'))
    for n in idx['method_declaration']:
        nm = _name(n)
        if nm:
            out.append(('symbol', nm, _line(n), 'Go method', nm, 'VERIFIED', 'tree-sitter'))
    for n in idx['type_spec']:
        nm = _name(n)
        if nm:
            out.append(('symbol', nm, _line(n), 'Go type', nm, 'VERIFIED', 'tree-sitter'))


# ---------- built-in framework adapters (tier: adapter) ----------
_VERBS = {'get', 'post', 'put', 'patch', 'delete', 'all', 'options', 'head'}
_RECV = re.compile(r'^(app|server|api|router|routes?|fastify|\w*Router|\w*App)$')


@adapter('javascript', 'typescript', 'tsx')
def express_like_routes(lang, idx, src, path, ctx, out):
    for n in idx['call_expression']:
        f = n.child_by_field_name('function')
        if f is None or f.type != 'member_expression':
            continue
        prop = _txt(f.child_by_field_name('property'))
        obj = _txt(f.child_by_field_name('object'))
        if prop.lower() not in _VERBS or not _RECV.match(obj):
            continue
        a = _args(n)
        if not a:
            continue
        v = _lit(a[0])
        if v is None:
            ctx['unresolved']['non-literal-route-path'] += 1
        elif v.startswith(('/', '*')):
            out.append(('api', v, _line(n), f'{prop.upper()} route (Express/Fastify-style receiver "{obj}")', v, 'INFERRED', 'adapter'))


@adapter('javascript', 'typescript', 'tsx')
def nestjs_decorators(lang, idx, src, path, ctx, out):
    for d in idx['decorator']:
        call = next((c for c in d.children if c.type == 'call_expression'), None)
        if call is None:
            continue
        f = call.child_by_field_name('function')
        if f is None or _txt(f) not in ('Get', 'Post', 'Put', 'Patch', 'Delete', 'All'):
            continue
        a = _args(call)
        v = '/' if not a else _lit(a[0])
        if v is None:
            ctx['unresolved']['non-literal-route-path'] += 1
        else:
            out.append(('api', v or '/', _line(d), f'NestJS @{_txt(f)} decorator (controller prefix not combined)', v, 'INFERRED', 'adapter'))


@adapter('javascript', 'typescript', 'tsx')
def client_api_calls(lang, idx, src, path, ctx, out):
    for n in idx['call_expression']:
        f = n.child_by_field_name('function')
        if f is None:
            continue
        hit = False
        if f.type == 'identifier' and _txt(f) in ('fetch', '$fetch'):
            hit = True
        elif f.type == 'member_expression' and _txt(f.child_by_field_name('object')) == 'axios' \
                and _txt(f.child_by_field_name('property')).lower() in _VERBS | {'request'}:
            hit = True
        if not hit:
            continue
        a = _args(n)
        if not a:
            continue
        v = _tmpl(a[0])
        if v is None:
            ctx['unresolved']['non-literal-api-url'] += 1
        elif v:
            out.append(('api', v, _line(n), 'Client-side API call site (fetch/axios)', v, 'INFERRED', 'adapter'))


@adapter('javascript', 'typescript', 'tsx')
def client_routes(lang, idx, src, path, ctx, out):
    for t in ('jsx_self_closing_element', 'jsx_opening_element'):
        for n in idx[t]:
            if _txt(n.child_by_field_name('name')) != 'Route':
                continue
            for at in n.children:
                if at.type == 'jsx_attribute' and at.children and _txt(at.children[0]) == 'path':
                    v = _lit(at.named_children[-1]) if len(at.named_children) > 1 else None
                    if v is not None:
                        out.append(('route', v, _line(n), 'React Router <Route path>', v, 'INFERRED', 'adapter'))
    for n in idx['pair']:
        key = _txt(n.child_by_field_name('key')).strip('\'"')
        v = _lit(n.child_by_field_name('value'))
        if key != 'path' or v is None or n.parent is None:
            continue
        siblings = {_txt(c.child_by_field_name('key')).strip('\'"') for c in n.parent.children if c.type == 'pair'}
        if siblings & {'element', 'component', 'children', 'lazy', 'loader', 'Component'}:
            out.append(('route', v, _line(n), 'Route-config object (path with element/component)', v, 'INFERRED', 'adapter'))


_GO_METHODS = {'HandleFunc', 'Handle', 'GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'Get', 'Post', 'Put', 'Patch', 'Delete', 'Any'}


@adapter('go')
def go_http_routes(lang, idx, src, path, ctx, out):
    for n in idx['call_expression']:
        f = n.child_by_field_name('function')
        if f is None or f.type != 'selector_expression':
            continue
        m = _txt(f.child_by_field_name('field'))
        if m not in _GO_METHODS:
            continue
        a = _args(n)
        if not a:
            continue
        v = _lit(a[0])
        if v is None:
            if m in ('HandleFunc', 'Handle'):
                ctx['unresolved']['non-literal-route-path'] += 1
        elif v.startswith('/') or re.match(r'^[A-Z]+ /', v):
            out.append(('api', v, _line(n), f'Go HTTP route via .{m}() (net/http, chi, gin, echo style)', v, 'INFERRED', 'adapter'))


# ---------- path-based adapters (no parser needed) ----------
def detect_frameworks(root):
    """Names of frameworks evidenced by manifests in the repository root."""
    found = set()
    try:
        pkg = json.loads((Path(root) / 'package.json').read_text(encoding='utf-8'))
        deps = {**pkg.get('dependencies', {}), **pkg.get('devDependencies', {})}
        for name in ('next', 'express', 'fastify', 'react', 'react-router', 'react-router-dom', '@nestjs/core', 'vue', 'svelte'):
            if name in deps:
                found.add(name)
    except Exception:
        pass
    try:
        gomod = (Path(root) / 'go.mod').read_text(encoding='utf-8')
        for name in ('gin-gonic/gin', 'labstack/echo', 'go-chi/chi', 'gofiber/fiber', 'gorilla/mux'):
            if name in gomod:
                found.add(name)
    except Exception:
        pass
    return found


def file_routes(path, frameworks):
    """Next.js file-system routes. Requires `next` in package.json to avoid false positives."""
    if 'next' not in frameworks:
        return []
    p = path.replace('\\', '/')
    m = re.search(r'(?:^|/)pages/(.+)\.(?:tsx|ts|jsx|js)$', p)
    if m:
        r = m.group(1)
        if r.rsplit('/', 1)[-1].startswith('_'):
            return []
        r = re.sub(r'(^|/)index$', '', r)
        if r.startswith('api/') or r == 'api':
            return [('api', '/' + r, 1, 'Next.js pages/api file route (file-system convention)', '/' + r, 'INFERRED', 'adapter')]
        return [('route', '/' + r, 1, 'Next.js pages file route (file-system convention)', '/' + r, 'INFERRED', 'adapter')]
    m = re.search(r'(?:^|/)app/(?:(.*)/)?(page|route)\.(?:tsx|ts|jsx|js)$', p)
    if m:
        r = '/' + (m.group(1) or '')
        r = re.sub(r'/\([^/]+\)', '', r) or '/'
        kind = 'route' if m.group(2) == 'page' else 'api'
        return [(kind, r, 1, f'Next.js app-router {m.group(2)} file (file-system convention)', r, 'INFERRED', 'adapter')]
    return []


# ---------- plugin loading (skill folder only) ----------
def _load_plugins():
    d = Path(__file__).resolve().parents[1] / 'adapters'
    if not d.is_dir():
        return
    for f in sorted(d.glob('*.py')):
        if f.name.startswith('_'):
            continue
        try:
            spec = importlib.util.spec_from_file_location('atlas_adapter_' + f.stem, f)
            mod = importlib.util.module_from_spec(spec)
            sys.modules.setdefault('ts_adapters', sys.modules[__name__])
            spec.loader.exec_module(mod)
        except Exception as exc:  # a broken plugin must never break the Atlas
            print(f'warning: adapter plugin {f.name} failed to load: {exc}', file=sys.stderr)


_load_plugins()


# ---------- entry point ----------
def extract(ext, text, path, frameworks=frozenset()):
    """Returns {'imports','rows','unresolved','parse_errors'} or None if no parser is available for ext."""
    _load()
    lang = EXT_LANG.get(ext)
    parser = _parsers.get(lang)
    if parser is None:
        return None
    src = text.encode('utf-8')
    tree = parser.parse(src)
    idx = defaultdict(list)
    stack = [tree.root_node]
    while stack:
        n = stack.pop()
        idx[n.type].append(n)
        stack.extend(n.children)
    ctx = {'unresolved': Counter(), 'frameworks': frameworks, 'ext': ext}
    out, imports = [], []
    if lang in JS_LANGS:
        _core_js(lang, idx, ctx, out, imports, ext)
    else:
        _core_go(idx, ctx, out, imports, path)
    for langs, fn in ADAPTERS:
        if lang in langs:
            try:
                fn(lang, idx, src, path, ctx, out)
            except Exception as exc:  # adapter bug: skip that adapter, keep the rest
                ctx['unresolved']['adapter-error:' + fn.__name__] += 1
    return {'imports': imports, 'rows': out, 'unresolved': dict(ctx['unresolved']),
            'parse_errors': 1 if tree.root_node.has_error else 0}
