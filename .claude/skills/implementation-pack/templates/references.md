# Reference and plan document templates

One section per document. Copy the section you need into the target file under `.review/implementation/`, fill every `<!-- fill -->` marker, and omit documents that do not apply.

---

## Template: adr

# ADR-NNN — <Decision title>
*Owner: ARC. Every item must reference the finding (FND-), debate (DBT-) and decision (DEC-) IDs it is based on. Plain language; no padding; no new information beyond the review record.*

## Status (Accepted)
<!-- fill -->

## Context
<!-- fill -->

## Decision
<!-- fill -->

## Alternatives considered
<!-- fill -->

## Consequences
<!-- fill -->

## Linked: DEC-, FND-
<!-- fill -->

---

## Template: ai-system

# AI System Specification
*Owner: AI. Every item must reference the finding (FND-), debate (DBT-) and decision (DEC-) IDs it is based on. Plain language; no padding; no new information beyond the review record.*

## Prompt architecture (layers, ownership, versioning)
<!-- fill -->

## Context construction
<!-- fill -->

## Structured outputs and validation
<!-- fill -->

## Decision rationale data for explainability
<!-- fill -->

## Failure handling (timeouts, malformed output, rate limits, model changes)
<!-- fill -->

## Evaluation set and regression tests
<!-- fill -->

## Observability
<!-- fill -->

---

## Template: architecture

# Target Architecture
*Owner: ARC. Every item must reference the finding (FND-), debate (DBT-) and decision (DEC-) IDs it is based on. Plain language; no padding; no new information beyond the review record.*

## Current architecture (brief, with diagram)
<!-- fill -->

## Target architecture (diagram)
<!-- fill -->

## Module responsibilities and boundaries
<!-- fill -->

## Interfaces and contracts
<!-- fill -->

## Data flow: request → AI → timeline → render → export
<!-- fill -->

## What changes and why (linked decisions)
<!-- fill -->

## What deliberately stays the same
<!-- fill -->

---

## Template: cost-performance

# Cost & Performance Model
*Owner: CPE. Every item must reference the finding (FND-), debate (DBT-) and decision (DEC-) IDs it is based on. Plain language; no padding; no new information beyond the review record.*

## Cost per unit of work today (breakdown, assumptions, sources)
<!-- fill -->

## Cost per unit of work target
<!-- fill -->

## Performance budgets (generation, render, UI)
<!-- fill -->

## Bottlenecks and planned optimisations
<!-- fill -->

## Quality / speed / cost trade-offs
<!-- fill -->

---

## Template: design-system

# Design System
*Owner: VIS. Every item must reference the finding (FND-), debate (DBT-) and decision (DEC-) IDs it is based on. Plain language; no padding; no new information beyond the review record.*

## Visual direction (principles, references)
<!-- fill -->

## Tokens: colour, typography, spacing, radius, elevation, motion
<!-- fill -->

## Components (each: purpose, variants, states)
<!-- fill -->

## Patterns to remove (the generic look)
<!-- fill -->

## Contrast and accessibility
<!-- fill -->

---

## Template: media-pipeline

# Media Pipeline Specification
*Owner: MED. Every item must reference the finding (FND-), debate (DBT-) and decision (DEC-) IDs it is based on. Plain language; no padding; no new information beyond the review record.*

## Pipeline stages and contracts
<!-- fill -->

## Determinism and preview/export parity
<!-- fill -->

## Text and font rendering (incl. multi-script)
<!-- fill -->

## Encoding and export profiles
<!-- fill -->

## Performance targets
<!-- fill -->

## Visual regression and golden fixtures
<!-- fill -->

---

## Template: migration-strategy

# Migration Strategy
*Optional ARC reference. Include only when the architectural migration strategy adds cross-ticket context not already expressed in the roadmap and ticket dependencies. This is not a second backlog.*

## Migration principles
<!-- fill -->

## Architectural transition stages
Describe system-level transition stages, compatibility constraints, and reversible boundaries. Link relevant TASK IDs rather than restating their steps.
<!-- fill -->

## Data and compatibility considerations
<!-- fill -->

## Cross-stage risks and mitigations
<!-- fill -->

---


## Template: risk-register

# Risk Register
*Owner: RED · CHR. Every item must reference the finding (FND-), debate (DBT-) and decision (DEC-) IDs it is based on. Plain language; no padding; no new information beyond the review record.*

## Pre-mortem summary
<!-- fill -->

## Risks table: risk · likelihood · impact · affected workstreams · mitigation · owner · early warning sign
<!-- fill -->

---

## Template: terminology-and-copy

# Terminology & Copy
*Owner: DOC. Every item must reference the finding (FND-), debate (DBT-) and decision (DEC-) IDs it is based on. Plain language; no padding; no new information beyond the review record.*

## Glossary (term · meaning · use instead of)
<!-- fill -->

## Voice and tone
<!-- fill -->

## Microcopy standards (buttons, errors, empty states, progress)
<!-- fill -->

## Message rewrites (current → new, location)
<!-- fill -->

## Documentation fixes
<!-- fill -->

---

## Template: test-strategy

# Test Plan
*Owner: QA. Every item must reference the finding (FND-), debate (DBT-) and decision (DEC-) IDs it is based on. Plain language; no padding; no new information beyond the review record.*

## Test strategy (what kind of test for what)
<!-- fill -->

## Making the suite fast (diagnosis, plan, target duration)
<!-- fill -->

## Regression scenarios per workstream
<!-- fill -->

## Security tests
<!-- fill -->

## Acceptance tests mapped to decisions
<!-- fill -->

---

## Template: ux-flows

# UX Flows
*Owner: UX · XAI. Every item must reference the finding (FND-), debate (DBT-) and decision (DEC-) IDs it is based on. Plain language; no padding; no new information beyond the review record.*

## Primary journeys (target flow per journey)
<!-- fill -->

## States: loading, empty, error, success, background work
<!-- fill -->

## Onboarding
<!-- fill -->

## AI control and explainability patterns (XAI): see why, edit, lock, regenerate one part, compare, recover
<!-- fill -->

## Accessibility requirements
<!-- fill -->

---

## Template: workstream

# WS-NN — <Workstream title>
*Owner: Workstream owner. Every item must reference the finding (FND-), debate (DBT-) and decision (DEC-) IDs it is based on. Plain language; no padding; no new information beyond the review record.*

## Problem (plain language)
<!-- fill -->

## Findings and decisions addressed
<!-- fill -->

## Requirements
<!-- fill -->

## Design / approach (and alternatives rejected)
<!-- fill -->

## Acceptance criteria (observable)
<!-- fill -->

## Dependencies
<!-- fill -->

## Out of scope
<!-- fill -->

## Risks
<!-- fill -->
