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

Open Claude Code in that project, then:

```
/review-committee start     # learns your product (takes one session)
/review-committee next      # runs the next phase, repeat until done
```

That's it. You'll get a short progress note after each phase. Want it hands-off? Say:
`/review-committee next — run P1 through P6 without stopping`

> 💡 Each phase is token-heavy. Run one phase per session (`/clear` between phases) so you don't hit your usage limit mid-phase.

Handy extras: `/review-committee status` · `report` · `ticket TASK-001` · `approve-plan TASK-001`

## What happens

| Phase | In plain words |
|---|---|
| P0 Intake | Reads your repo and docs, maps the code, writes the product brief |
| P1 Discovery | Tries the product like a first-time user, checks competitors |
| P2 Review | Each specialist reviews on their own, without seeing the others' notes |
| P3 Verification | Every claim is checked against the real code. Nobody verifies their own |
| P4 Debate | Disagreements are argued with evidence, then decided |
| P5 Decision | Every verified finding gets accepted, rejected or deferred. Plan and tickets are drafted |
| P6 Readiness | Go / Go-with-conditions / Hold for each piece of work. **Review complete** |
| P7 Re-review *(optional)* | After you've made changes, checks they actually fixed the problems |

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
