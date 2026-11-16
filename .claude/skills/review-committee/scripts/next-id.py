#!/usr/bin/env python3
"""Print the next free ID. Run from repo root.
  next-id.py FND-BE   -> FND-BE-004      next-id.py DBT -> DBT-002
  next-id.py DEC | WS | TASK [count] (TASK IDs are implementation tickets)
"""
import glob, os, re, sys
prefix = sys.argv[1]; count = int(sys.argv[2]) if len(sys.argv) > 2 else 1
width = 2 if prefix == "WS" else 3
pat = re.compile(re.escape(prefix) + r"-(\d+)")
mx = 0
for p in glob.glob(".review/**/*", recursive=True):
    if os.path.isfile(p):
        try:
            for m in pat.finditer(open(p, encoding="utf-8", errors="ignore").read()):
                mx = max(mx, int(m.group(1)))
        except Exception:
            pass
        m = pat.search(os.path.basename(p))
        if m:
            mx = max(mx, int(m.group(1)))
for i in range(1, count + 1):
    print(f"{prefix}-{mx + i:0{width}d}")
