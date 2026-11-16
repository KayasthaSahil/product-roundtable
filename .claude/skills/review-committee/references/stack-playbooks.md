# Stack Playbooks: Python and React

Investigation prompts for the two most common stacks. **They are prompts, not findings.** Use them to decide where to look; a finding exists only when this repository's code, config or runtime behaviour shows the problem, with evidence (path:line, excerpt, or observed behaviour). Skip sections that do not apply to the detected stack (`stack-profile.md`). Frameworks change quickly: when a point depends on a version, check the version in the lockfile and the framework's current official documentation.

## How roles use this

| Role | Start with |
|---|---|
| ARC | Layout, boundaries, packaging, FE/BE contract, config and secrets |
| BE | Python: framework, data, async, jobs, errors, observability |
| FE | React: components, state, data fetching, rendering, accessibility |
| QA | Test strategy, security checklist for both stacks |
| UX | React: loading, empty and error states, forms, keyboard flows |
| CPE | Python query/IO cost, React bundle and render cost, AI/API call cost |

## Python (FastAPI, Flask, Django and others)

**Structure and packaging**
- One clear app entry point; layering (routes → services → data access) without circular imports; business logic out of route handlers and templates.
- `pyproject.toml` as the single source of metadata; dependencies pinned through a lockfile (uv, poetry, pip-tools); dev and runtime dependencies separated; Python version declared and matched in CI/Docker.
- Settings from environment (pydantic-settings, django-environ or similar) with no secrets or `DEBUG=True` defaults committed.

**Web layer**
- Input validated at the boundary (pydantic models, DRF serializers, Django forms), with consistent error shapes and status codes.
- Authentication and authorisation enforced per route or per view, not assumed from the frontend; CORS and CSRF configured deliberately; rate limiting on auth and expensive endpoints.
- Pagination, filtering and sorting bounded; no unbounded list endpoints.
- FastAPI: dependency injection used for auth/db sessions; no blocking calls inside `async def`; response models declared; background tasks not used for work that must not be lost.
- Django: `ALLOWED_HOSTS`, `SECRET_KEY`, `DEBUG`, `SECURE_*` and session/cookie flags; `select_related`/`prefetch_related` where lists render related rows; migrations reviewed and reversible; admin exposure.
- Flask: application factory, blueprints, extension init order, request-context misuse in threads/jobs.

**Data**
- ORM N+1 patterns, missing indexes for filtered/sorted columns, transactions around multi-step writes, session lifecycle (one session per request/job), connection pool sizing.
- Raw SQL built by string formatting (injection), migrations that lock large tables, schema changes without backfill plans.

**Async, jobs and external calls**
- Celery/RQ/Dramatiq tasks idempotent, with retries, backoff, timeouts and dead-letter handling; task arguments small and serialisable; results not relied on for correctness.
- Every outbound HTTP/LLM call has a timeout, bounded retries and error mapping; no shared mutable global state across workers.
- Long-running work not executed inside request handlers.

**Errors, logging, observability**
- Exceptions not swallowed (`except Exception: pass`); structured logging with request/job IDs; no secrets or PII in logs; health and readiness endpoints; metrics on queue depth, latency, error rate.

**Typing and quality**
- Type hints at public boundaries; mypy/pyright configuration and how strict; ruff/flake8 rules; dead code and duplicated logic.

**Security (static review)**
- `pickle`/`yaml.load`/`eval`/`exec` on untrusted data, `subprocess(..., shell=True)` with interpolated input, path traversal in file handling, SSRF through user-supplied URLs, open redirects, weak password hashing, JWT handling (algorithm, expiry, storage), unsafe file upload (type, size, storage location), dependency vulnerabilities from the lockfile, secrets in the repo or Dockerfile.

**Tests**
- pytest layout, fixtures and factories, database isolation per test, markers for slow/integration tests, network and LLM calls mocked or recorded, flaky time/randomness, coverage of critical paths. Review statically; never run the full suite during the review.

## React (Vite, Next.js, Remix, CRA and others; JS or TS)

**Structure**
- Feature-oriented folders, small focused components, shared UI primitives, no god components; presentational vs stateful split where it helps; consistent naming.
- TypeScript: `strict` on, few `any`/non-null assertions, API types shared or generated (OpenAPI, tRPC, zod) rather than hand-duplicated.

**State and data**
- State lives at the lowest level that needs it; context used for stable, low-frequency values, not hot state; a server-state library (React Query, SWR, RTK Query) instead of ad hoc `useEffect` fetching; no duplicated server data in client stores; derived values computed, not stored.
- Forms: validation strategy, controlled vs uncontrolled consistency, error display, double-submit protection, optimistic updates and rollback.

**Hooks and rendering**
- `useEffect` used to synchronise with external systems, not to derive state; dependency arrays correct (the `react-hooks` lint rules enabled); cleanups for subscriptions, timers and fetches; stable `key` props; no state updates after unmount; memoisation used where it measurably helps, not everywhere.
- Re-render hot spots: large lists without virtualisation, inline object/function props into memoised children, context value identity changes.

**Loading, empty and error states**
- Every async view has loading, empty and error states; error boundaries around route-level and risky subtrees; failed requests give actionable messages and retry; offline/slow-network behaviour considered.

**Routing and SSR (Next/Remix)**
- Server vs client component boundaries, hydration mismatches, data fetching location, caching/revalidation settings, route guards that are enforced server-side, environment variables exposed to the browser (`NEXT_PUBLIC_*`, `VITE_*`) containing nothing secret.

**Performance**
- Bundle size and code splitting, heavy dependencies imported wholesale, images/fonts optimisation, request waterfalls, unnecessary client-side work; check build output or config rather than guessing.

**Accessibility (implementation)**
- Semantic elements before ARIA; labels for every input; visible focus; full keyboard operation; modal focus trap and return; accessible names for icon buttons; colour contrast tokens; reduced-motion handling; live regions for async status.

**Security (static review)**
- `dangerouslySetInnerHTML` and unsanitised Markdown/HTML, tokens in `localStorage` (XSS exposure), open redirects after login, trusting client-side authorisation, third-party scripts, source maps and secrets in the production bundle.

**Tests**
- Testing Library style (behaviour over implementation), network mocked at the boundary (MSW), router/provider test wrappers, a small number of end-to-end flows (Playwright/Cypress) for critical journeys, visual/Storybook coverage where present.

## Full-stack seams (Python API + React client)

- **Contract:** one source of truth for request/response shapes (OpenAPI → generated client/types, or shared schema); error format and status-code conventions agreed; versioning and breaking-change policy; pagination and filter conventions consistent.
- **Auth flow:** where tokens live, refresh handling, logout and revocation, CSRF if cookies are used, CORS origins per environment.
- **Long operations:** polling vs SSE vs WebSocket, job status endpoints, cancellation, resumability after refresh, progress that survives reload.
- **Environments:** config per environment, no hard-coded URLs, build-time vs runtime variables, Docker/compose parity with production, CI running lint, types and tests for both sides.
- **Observability across the seam:** request IDs propagated from browser to API to jobs; frontend error reporting; backend errors that the UI can explain to the user.
