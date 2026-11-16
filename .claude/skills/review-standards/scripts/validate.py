#!/usr/bin/env python3
"""Validate committee JSON records against the schemas (stdlib only).

Usage: python3 validate.py <kind> <file> [--check-refs]
Kinds: findings, verification, dispute, position, decisions, roadmap, gate, rereview, product-context, ticket
--check-refs : also confirm that code evidence paths (path or path:line) exist in the repo
               and that referenced finding IDs exist in .review/findings/.
Exit 0 = valid, 1 = invalid (errors printed).
"""
import json, os, re, sys, glob

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMAS = os.path.join(HERE, "..", "schemas")
KINDS = {"findings": "findings-file", "verification": "verification", "dispute": "dispute",
         "position": "position", "decisions": "decisions", "roadmap": "roadmap", "gate": "gate",
         "rereview": "rereview", "ticket": "ticket", "product-context": "product-context"}
TYPES = {"object": dict, "array": list, "string": str, "boolean": bool, "integer": int,
         "number": (int, float), "null": type(None)}


def load_schema(name):
    with open(os.path.join(SCHEMAS, f"{name}.schema.json"), encoding="utf-8") as f:
        return json.load(f)


def check(value, schema, path, errs):
    if "$ref" in schema:
        return check(value, load_schema(schema["$ref"]), path, errs)
    t = schema.get("type")
    if t:
        ts = t if isinstance(t, list) else [t]
        ok = False
        for x in ts:
            py = TYPES[x]
            if isinstance(value, bool) and x in ("integer", "number"):
                continue
            if isinstance(value, py):
                ok = True
        if not ok:
            errs.append(f"{path}: expected {t}, got {type(value).__name__}")
            return
    if "enum" in schema and value not in schema["enum"]:
        errs.append(f"{path}: {value!r} not one of {schema['enum']}")
    if isinstance(value, str):
        if len(value.strip()) < schema.get("minLength", 0):
            errs.append(f"{path}: must not be empty")
        if "pattern" in schema and not re.match(schema["pattern"], value):
            errs.append(f"{path}: {value!r} does not match {schema['pattern']}")
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            errs.append(f"{path}: needs at least {schema['minItems']} item(s)")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            errs.append(f"{path}: at most {schema['maxItems']} item(s)")
        if schema.get("uniqueItems"):
            seen = set()
            for i, item in enumerate(value):
                try:
                    marker = json.dumps(item, sort_keys=True, ensure_ascii=False)
                except TypeError:
                    marker = repr(item)
                if marker in seen:
                    errs.append(f"{path}[{i}]: duplicate item is not allowed")
                seen.add(marker)
        if "items" in schema:
            for i, v in enumerate(value):
                check(v, schema["items"], f"{path}[{i}]", errs)
    if isinstance(value, dict):
        if len(value) < schema.get("minProperties", 0):
            errs.append(f"{path}: needs at least {schema['minProperties']} properties")
        if "maxProperties" in schema and len(value) > schema["maxProperties"]:
            errs.append(f"{path}: at most {schema['maxProperties']} properties")
        for r in schema.get("required", []):
            if r not in value:
                errs.append(f"{path}: missing required field '{r}'")
        properties = schema.get("properties", {})
        for k, sub in properties.items():
            if k in value and (value[k] is not None or "null" in str(sub.get("type"))):
                check(value[k], sub, f"{path}.{k}", errs)
        additional = schema.get("additionalProperties", True)
        for k in value:
            if k not in properties:
                if additional is False:
                    errs.append(f"{path}: unexpected property '{k}'")
                elif isinstance(additional, dict):
                    check(value[k], additional, f"{path}.{k}", errs)


def repo_root():
    d = os.getcwd()
    while d != os.path.dirname(d):
        if os.path.isdir(os.path.join(d, ".review")) or os.path.isdir(os.path.join(d, ".git")):
            return d
        d = os.path.dirname(d)
    return os.getcwd()


def all_finding_ids(root):
    ids = set()
    for p in glob.glob(os.path.join(root, ".review", "findings", "*.json")):
        try:
            for f in json.load(open(p, encoding="utf-8")).get("findings", []):
                ids.add(f.get("id"))
        except Exception:
            pass
    return ids


def semantic_findings(doc, errs, check_refs):
    seen = set()
    strengths = {}
    root = repo_root()
    role = doc.get("role")
    for i, f in enumerate(doc.get("findings", [])):
        p = f"findings[{i}]({f.get('id', '?')})"
        fid = f.get("id", "")
        if fid in seen:
            errs.append(f"{p}: duplicate id")
        seen.add(fid)
        if role and not fid.startswith(f"FND-{role}-"):
            errs.append(f"{p}: id prefix must be FND-{role}-")
        if f.get("role") and role and f["role"] != role:
            errs.append(f"{p}: role '{f['role']}' differs from file role '{role}'")
        if f.get("kind") == "finding":
            for r in ("category", "severity", "recommendation", "impact"):
                if not f.get(r):
                    errs.append(f"{p}: '{r}' is required for kind=finding")
            rec = f.get("recommendation") or {}
            need = {"Critical": ("why", "expected_outcome", "verification"), "High": ("why", "expected_outcome", "verification"),
                    "Medium": ("verification",)}.get(f.get("severity"), ())
            for r in need:
                if not str(rec.get(r, "")).strip():
                    errs.append(f"{p}: {f.get('severity')} needs recommendation.{r} (tiered detail, see review-standards)")
            if f.get("severity") in ("Critical", "High"):
                has_code = any(e.get("type") in ("code", "command", "repro") for e in f.get("evidence", []))
                if not f.get("repro_steps") and not has_code:
                    errs.append(f"{p}: Critical/High needs repro_steps or code/command evidence")
        elif f.get("kind") == "strength":
            if f.get("severity"):
                errs.append(f"{p}: strengths carry no severity")
            strengths[f.get("phase")] = strengths.get(f.get("phase"), 0) + 1
            if strengths[f.get("phase")] == 4:
                errs.append(f"{p}: at most 3 strengths per role per phase")
        if check_refs:
            for e in f.get("evidence", []):
                if e.get("type") == "code":
                    ref = e.get("ref", "")
                    m = re.match(r"^(.+?)(?::(\d+)(?:-(\d+))?)?$", ref)
                    fp = m.group(1) if m else ref
                    full = os.path.join(root, fp)
                    if not os.path.exists(full):
                        errs.append(f"{p}: evidence path not found: {fp}")
                    elif m and m.group(2) and os.path.isfile(full):
                        try:
                            n = sum(1 for _ in open(full, encoding="utf-8", errors="ignore"))
                            last = int(m.group(3) or m.group(2))
                            if last > n:
                                errs.append(f"{p}: {fp} has {n} lines, cited line {last}")
                        except Exception:
                            pass


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    check_refs = "--check-refs" in sys.argv
    if len(args) != 2 or args[0] not in KINDS:
        print(__doc__)
        sys.exit(2)
    kind, path = args
    try:
        doc = json.load(open(path, encoding="utf-8"))
    except Exception as e:
        print(f"INVALID: cannot parse {path}: {e}")
        sys.exit(1)
    errs = []
    check(doc, load_schema(KINDS[kind]), kind, errs)
    if kind == "findings":
        semantic_findings(doc, errs, check_refs)
    if check_refs and kind in ("verification", "decisions", "rereview", "dispute"):
        ids = all_finding_ids(repo_root())
        key = {"verification": "verdicts", "decisions": "decisions", "rereview": "results"}.get(kind)
        items = doc.get(key, []) if key else [doc]
        for it in items:
            refs = [it.get("finding_id")] if "finding_id" in it else it.get("findings", [])
            for r in refs:
                if r and r.startswith("FND-") and r not in ids:
                    errs.append(f"unknown finding id referenced: {r}")
    if errs:
        print(f"INVALID: {path} ({len(errs)} error(s))")
        for e in errs[:60]:
            print("  -", e)
        sys.exit(1)
    print(f"VALID: {path}")


if __name__ == "__main__":
    main()
