#!/usr/bin/env python3
"""PreToolUse guard for Read / Grep: block reading secret files during a review."""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import guards_active, read_event, deny, allow

ev = read_event()
if not guards_active():
    allow()
ti = ev.get("tool_input", {}) or {}
cands = [ti.get("file_path", ""), ti.get("path", ""), ti.get("glob", "")]
SECRET = re.compile(r"(^|[\\/])(\.env(?!\.(example|sample|template|dist)$)[^\\/]*|.*\.pem|.*\.key|id_rsa[^\\/]*|id_ed25519[^\\/]*|credentials(\.json)?|secrets?\.(json|ya?ml|toml))$", re.I)
for c in cands:
    if c and SECRET.search(c.strip()):
        deny(f"Secret files must not be read during the review ({c}). Cite the location of a secrets issue, never its value. "
             "Use .env.example or config schemas to learn variable names.")
allow()
