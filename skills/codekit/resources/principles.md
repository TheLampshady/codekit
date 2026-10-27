# PROJECT_NAME Constitution

<!--
codekit baseline. `/codekit init` fills this in per project:
- PROJECT_NAME, the Quality Gates table, Project Patterns, and the Governance dates
- principles for stacks the project doesn't use are removed
- "No Backwards Compatibility Before First Release" removed once the project has shipped
The finished file stays under 300 lines. The WRONG/CORRECT examples live in docs/PRINCIPLES-EXAMPLES.md
(from principles-examples.md), not here. Remove this comment when filled.
-->

## Core Principles

### Modular Code

Every function, class, and module MUST have a single clear purpose. If you can't describe it in one or two sentences, split it.

- A function does one thing. If describing it requires "and", split it.
- A module groups related functions around one concept (e.g. "auth validation", "storage operations").
- A file you have to scroll to understand becomes a module directory whose index or `__init__` re-exports the public interface.
- **Reuse before you write.** Before adding a helper, check, or filter, search for one that already does the job, by behavior and not just by name. A check written twice gets one shared helper next to the data it's about, and every call site uses it.

**Rationale**: Single-purpose modules are faster to read and easier to test, and they give an AI assistant enough context in one file to change it correctly. A second copy of a check drifts from the first as soon as only one is fixed.

### Consistency

Every recurring problem MUST have exactly one solution in the codebase. When two call sites solve it differently, one of them is wrong.

- Refreshing data after a write: one invalidation or refetch helper.
- Errors: one handling pattern and one shared error display.
- Dates and times: one formatter.
- User-facing copy: one home for the strings.
- Names: one name per concept across code, copy, and docs. If a concept needs two (an internal field and its public label), write down which belongs where.

**Rationale**: Divergent solutions are themselves a source of bugs. Fixing one path leaves the others broken, and a newcomer, human or AI, can't tell which pattern is the real one.

### Testing Discipline

All code MUST be written so it can be tested. Keep business logic pure (input in, output out). Isolate side effects in boundary functions, tested by mocking the shared clients they import.

**Network isolation:** all tests MUST run with the network blocked by default. An external call fails the test unless the test explicitly allows it (`pytest-socket` for Python; MSW with `onUnhandledRequest: "error"` or `nock.disableNetConnect()` for JavaScript).

**Rationale**: Pure logic is trivial to test. Blocking the network keeps tests deterministic, fast, and independent of outside services.

### Required Test Coverage

All new code MUST include tests, in the same PR or commit. These categories set the minimum:

| Category | What to test |
|----------|-------------|
| **Pure logic** | Input → output, edge cases, boundaries, error cases. No mocks. |
| **Components** | Renders with typical props and with missing, null, or empty data. Key interactions produce the expected UI change. |
| **Pages / Views** | Smoke render, loading states, data display with a mocked API or service layer, key user flows. |
| **API endpoints / Services** | Request/response shape matches the contract, validation rejects bad input, error codes are correct, side effects happen. |
| **App entry (smoke)** | Imports and initializes without runtime errors, which proves the dependency tree loads. |

1. **Smoke tests are mandatory.** Every app entry point MUST have a test that imports and initializes it, to catch missing packages, circular imports, and bad re-exports before production.
2. **Test pure logic first.** Don't skip a test because the function is simple.
3. **Mock at boundaries, not everywhere.** Mock external I/O (database, APIs, file system), not internal code. If you have to mock internal code, refactor it.
4. **Missing tests block review.** Code without tests for the applicable categories MUST NOT be approved.

**Rationale**: Untested code is unverified code, and "we'll add tests later" means they won't be added.

### Test Economy

Tests MUST cover each behavior in exactly one place, at the cheapest layer that can observe it. A bloated suite slows every change and buries the failures that matter.

1. **One place per behavior.** Test pure logic in a unit test for that function, not from every caller. An endpoint test checks wiring only (status code, service call, response shape). Hooks get hook tests, components get component tests, and page tests check that the right components get the right props.
2. **Test rules, not literals.** Don't restate a constant, count, list, or copy string. Assert the invariant behind it: "every domain in `VALID_DOMAINS` passes `validate_email_domain`", not "`VALID_DOMAINS` has these 3 entries".
3. **Repeat a case across variants only when the behavior differs.** Two configurations on the same code path get one test.
4. **Recorded output is data, not a contract.** A test over a saved fixture (recorded LLM transcript, cached API response, golden payload) MUST derive its expectations from the fixture itself. When the fixture is stale, re-record it; don't hand-edit the assertion. A model's own judgment (quality, tone, reasoning) belongs in an eval scored by a rubric, not pinned to one recorded output.
5. **The test double holds no business rules.** A mock stores, replies, and fails on request, and nothing more. It exposes only the methods its tests exercise, and an unexercised operation raises (`NotImplementedError`) instead of returning a default. Validation, authorization, and business logic are tested against the service that owns them.
6. **Decision logic lives in pure functions.** Anything with a branch belongs in a pure function a test can call directly, not in a route handler or component body.
7. **Trimming tests must not lose covered lines.** Run coverage before and after. The diff MUST NOT drop any line that was covered before.
8. **Find the owner before writing.** Search for the test that already owns the behavior and extend it. A moved behavior takes its test with it. A task that adds tests MUST name the existing test file it extends, or state that the behavior has no owner yet. "Add tests for X" is not a task.
9. **A test must be able to fail on its own.** It MUST NOT recompute the code under test to build its expected value, and MUST NOT assert only that a removed field or key is absent. A test earns its place by failing for a reason the code under test doesn't already guarantee.

**Rationale**: The same assertion repeated at every layer, tests that retype constants, fixtures that drift from their recordings, permissive mocks, tautological tests, and trims that quietly drop the one case that caught a regression all have the same fix: test the behavior once, at the layer that owns it, and keep coverage honest.

### Change-Tolerant Tests

A test MUST fail only when behavior a caller depends on breaks. A test that fails on a change a user or caller would accept (new records in a data file, edited copy, reordered keys, an internal refactor) is brittle and MUST be rewritten.

1. **App data is not test data.** JSON, YAML, seed data, prompt files, and config the app loads at runtime are content. Tests MUST NOT pin their record count, order, or any single record. Each such file MUST have one validation test of per-record invariants across *all* records: required fields, types, unique IDs, resolving references, known enum values.
2. **Tests own their data.** A test that needs exact output builds its own input with a builder or factory, or a fixture under `tests/`. It MUST NOT read a file the app loads.
3. **Count only what you created.** Against data the test doesn't own, assert existence, a lower bound, or a per-item invariant.
4. **Assert the fields you care about.** Compare the keys under test, not whole dicts or response bodies. An extra field MUST NOT fail a test. Don't assert order unless order is the contract.
5. **Check outcomes, not call sequences.** Assert returned values and resulting state. Assert a mock call only when that call is the side effect under test, and then assert its payload, not the call count or order.
6. **No large snapshots.** Full-render, full-page, and full-response snapshots are forbidden. Inline snapshots are fine for small, deliberate output (about 20 lines or fewer) with timestamps and generated IDs masked.
7. **Invariants for wide-input functions.** Parsers, validators, formatters, and normalizers SHOULD get property-based tests (Hypothesis, fast-check), plus a few named examples.
8. **The review question.** For every test, ask: *"Would this fail on a change a user or caller would accept?"* If yes, fix it before merge.

**Rationale**: A brittle test fails without a bug, so every failure costs a diagnosis and teaches the team to distrust red builds.

### Copy-Resilient Tests

Tests MUST NOT match on copy: any human-readable string owned by product, design, or content rather than code (labels, headings, placeholders, button text, error messages, log lines, prompt text).

**Frontend: locate elements in this order:**
1. `getByRole` by role alone, scoped with `within()` when needed. Add `name` only when it comes from mock data or a code constant.
2. `data-testid`, when a role alone isn't unique and the only distinguishing name is static copy.
3. DOM structure, as a last resort.

**Backend: assert on** status codes, exception types, error codes, enum values, and structured fields, not message strings. A message match (`pytest.raises(..., match=)`) is allowed only for a value taken from the test's own input.

1. New components and page sections MUST use semantic elements and ARIA roles, and add a `data-testid` where a role alone can't identify an element.
2. Tests MUST NOT use `getByText`, `getByLabelText`, `getByPlaceholderText`, or `getByRole(..., { name })` with a hardcoded display string.
3. Enum values and typed constants are safe to assert against. They change through code, not content edits.
4. To check that data appears, assert the rendered text matches the mock input, not a hardcoded string.

**Rationale**: Product and content editors change copy on their own schedule. Tests coupled to it fail for no real reason and erode trust in the suite.

### Import-Time Safety

Module-level code (settings files, client initialization, secret loading) MUST be safe to run with no network access. Network work MUST be deferred to first use or an explicit init call, never triggered by `import`.

- Module-level code MUST NOT open connections, resolve DNS, or call remote services.
- Client singletons, secret loaders, and config fetchers that need the network MUST initialize lazily.
- A module that needs a network-dependent "ready" state exposes an explicit `init()` or `setup()` for callers to invoke.

**Rationale**: Under network-blocking test tools, gRPC and HTTP clients created at import can hang silently instead of raising, and `except Exception` can't catch a call that never returns.

### Boundary Logging

Logging MUST happen at system boundaries, where data enters or leaves the system, not where it's transformed: API endpoint entry, external service calls, errors and exceptions, startup and shutdown. Pure functions don't log.

**Rationale**: Boundary logging gives observability without noise, and makes it easy to trace a request through the system.

### Quality Gates

All commits MUST pass the pre-commit hooks. Never use `--no-verify` to bypass them.

| Hook | Purpose | Fix command |
|------|---------|-------------|
| QUALITY_GATES | | |

**Hook configuration:** HOOK_CONFIG_PATH

**Rationale**: Gates catch issues before they enter the codebase and prevent CI failures.

### No Backwards Compatibility Before First Release

Until the first production release, breaking changes MUST be made outright. Replace code, schemas, and data shapes directly. Don't add shims, aliases, dual-write paths, or migrations for data that doesn't matter yet.

**Rationale**: Before a first release there are no production callers and no data worth preserving, so a shim only adds a second code path. Once the project ships, remove this principle and apply standard migration discipline.

### Existing Conventions Are the Baseline

The project's established setup is a working system, not a starting point to improve. Features build on it.

- **Don't change what works.** Configuration loading, data-store wiring, local dev and emulator setup, and the build and task-runner shape MUST stay as they are unless a feature's spec says otherwise in so many words.
- **Fewest moving parts wins.** Prefer a documented command over a script, a script over a task-runner target, and a target over a CI workflow. Don't add pipelines, generated config, service identities, or per-environment plumbing unless the owner asks for them by name.
- **Platform defaults over explicit flags.** Don't add flags, labels, env vars, or settings that restate a default.
- **One knob per fact.** Each environment fact is set in exactly one place. If a value can be derived, derive it.
- **No new settings without a consumer.** Every new config key MUST be read by code that ships in the same feature, and that code MUST be tested.
- **Ask before inventing infrastructure.** If a plan needs a resource, role, secret, or environment the project doesn't have, list it as an open question for the owner. Assumed infrastructure is a defect.
- **Confirm the reading before editing.** When an instruction can be read two ways, confirm which before touching a file the owner wrote.

**Rationale**: The existing setup encodes decisions already paid for. Rebuilding them inside a feature costs review time and hides accidental changes among the intentional ones.

## Project Patterns

PROJECT_PATTERNS

## Governance

This constitution documents patterns that MUST be followed to keep the codebase consistent.

**Precedence**: Spec before plan, plan before code. If a spec conflicts with this constitution, fix the spec, not the code. The constitution changes only through the amendment process below.

**Spec Freshness**: Every spec records the commit it was checked against. If the code has moved since, re-check the spec before building from it.

**Living Docs vs. Specs**: Guides and architecture docs describe the current code and change in the same commit. A spec is a record of a decision: once it ships, only its status and checkboxes change.

**Amendment Process**: Propose the change in a PR that modifies this file, document the rationale, and increment the version (MAJOR: a pattern removed or changed incompatibly; MINOR: a new pattern or utility; PATCH: clarifications or examples).

**Version**: 1.0.0 | **Ratified**: RATIFIED_DATE | **Last Amended**: RATIFIED_DATE
