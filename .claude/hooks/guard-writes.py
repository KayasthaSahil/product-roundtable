#!/usr/bin/env python3
"""PreToolUse guard for Write / Edit / MultiEdit / NotebookEdit: during a review, only .review/ may be written."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import guards_active, read_event, deny, allow, review_dir, project_dir

ev = read_event()
if not guards_active():
    allow()
ti = ev.get("tool_input", {}) or {}
path = ti.get("file_path") or ti.get("notebook_path") or ti.get("path") or ""
if not path:
    allow()
full = os.path.realpath(path if os.path.isabs(path) else os.path.join(ev.get("cwd") or project_dir(), path))
rd = os.path.realpath(review_dir())
if full == rd or full.startswith(rd + os.sep):
    allow()
deny(f"During the review, files may only be written inside .review/ (attempted: {path}). "
     "The committee reviews and plans; it never modifies production code, config, assets or design files.")
