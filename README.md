# Product Roundtable

**A review committee for your software, inside Claude Code.**
17 specialist AI reviewers (architect, UX, security, cost, red team and more) examine your product, argue over the disagreements, and hand you:

- 📄 **A readable report** (one offline HTML file): what your product does, what's wrong, what to change, and why.
- 🎫 **A ready-to-use plan**: prioritised, traceable tickets you or any coding agent can pick up later.

It **only reviews and plans.** It never edits your code.

## Install (one command)

Run this in the project you want reviewed:

**macOS / Linux / Git Bash**
```bash
curl -fsSL https://raw.githubusercontent.com/KayasthaSahil/product-roundtable/main/install.py | python3 -
```

**Windows PowerShell**
```powershell
irm https://raw.githubusercontent.com/KayasthaSahil/product-roundtable/main/install.py | python -
```

Needs Python 3.9+ and Node (for the optional browser). Your existing `.claude/settings.json` and `.mcp.json` are merged, never overwritten. Run it again any time to update.

## Use it

Open Claude Code in that project and run these **three commands**, one per session (`/clear` before each `next`):

```
/review-committee start     # 1. Understand: learns your product
/review-committee next      # 2. Review: specialists review, then every finding is verified
/review-committee next      # 3. Plan: decisions, roadmap and tickets
```

Three commands, three stages, that's all. You get a one-line update after each step and a short summary at the end of each stage. If you hit your usage limit, run `next` again later: it resumes where it stopped instead of starting over.

> 💡 Run one stage per session (`/clear` between stages) to stay under your usage limit.

## The 3 stages

| Stage | What happens |
|---|---|
| **1. Understand** | Reads your repo and docs, maps the code, tries the product like a first-time user |
| **2. Review** | 13 specialists review independently, then every finding is checked against the real code (nobody verifies their own) |
| **3. Plan** | Each finding is accepted, rejected or deferred; you get a roadmap, tickets and a Go / Hold verdict per piece of work. **Review complete** |

### Optional add-ons (only when you want them)

| Command | Adds | When it's worth it |
|---|---|---|
| `/review-committee debate` | A structured debate, with evidence, on disagreements between specialists, before decisions are made. Without it, the Chair decides and records the dissent | Strategic or high-impact disagreements (Stage 2 tells you how many there are) |
| `/review-committee benchmark` | A competitor comparison | You care about positioning |
| `/review-committee rereview` | After you've made changes, checks they really fixed the problems | After implementing the plan |

Other commands: `status` · `report` · `ticket TASK-001` · `approve-plan TASK-001`

## Where to find results

Everything lands in `.review/` in your project:

| Open this | To see |
|---|---|
| `.review/report/index.html` | The full report |
| `.review/implementation/START-HERE.md` | The plan and tickets, with the order to read them |
| `.review/implementation/tickets/INDEX.md` | The backlog |

## Good to know

- **Works on any stack.** Python and React get extra-deep checks; other stacks work too.
- **Safe by design.** It writes only inside `.review/`, never runs your full test suite, and never prints secrets (enforced by hooks while a review runs).
- **It decides on its own.** It won't ask you questions mid-review. You approve the plan afterwards.
- **Uninstall:** delete the `review-*` files in `.claude/agents`, the 8 committee folders in `.claude/skills` (`review-committee`, `review-standards`, `stack-detection`, `codebase-atlas`, `debate-protocol`, `verification-protocol`, `implementation-pack`, `report-builder`), `.claude/hooks/guard-*.py` and `_common.py`, and the three `guard-*` hook entries in `.claude/settings.json`.

## Learn more

How roles, phases, the Codebase Atlas, schemas and safety guards work: [docs/REFERENCE.md](docs/REFERENCE.md).
Run the tests: `python3 -m unittest discover -s tests`.

MIT licensed.
