"""Shared helpers for committee guard hooks.

Guards are ACTIVE only while a review is running: .review/state.json exists and
status is "active". When the review is paused or complete, every guard allows
everything, so normal development in the repo is never affected.
Emergency off-switch: set environment variable REVIEW_GUARDS=off.
"""
import json, os, sys

def project_dir():
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()

def review_dir():
    return os.path.join(project_dir(), ".review")

def guards_active():
    if os.environ.get("REVIEW_GUARDS", "").lower() == "off":
        return False
    p = os.path.join(review_dir(), "state.json")
    try:
        return json.load(open(p, encoding="utf-8")).get("status") == "active"
    except Exception:
        return False

def read_event():
    try:
        return json.load(sys.stdin)
    except Exception:
        return {}

def deny(reason):
    # Exit code 2 blocks the tool call; stderr is shown to Claude.
    sys.stderr.write("[review-committee guard] BLOCKED: " + reason + "\n")
    sys.exit(2)

def allow():
    sys.exit(0)

def load_stack_profile():
    p = os.path.join(review_dir(), "brief", "stack-profile.json")
    try:
        return json.load(open(p, encoding="utf-8"))
    except Exception:
        return {}
