# PROJECT_NAME Constitution

<!--
codekit baseline. `/codekit init` fills this in per project:
- PROJECT_NAME, the Quality Gates table, Project Patterns, and the Governance dates
- examples translated to the project's primary language; examples for stacks
  the project doesn't use are removed
- "No Backwards Compatibility Before First Release" removed once the project has shipped
Remove this comment when filled.
-->

## Core Principles

### Modular Code

Every function, class, and module MUST have a single clear purpose. If you can't describe what it does in one or two sentences, it MUST be split.

**The Split Rule:**
- A function does one thing. If describing it requires "and", split it.
- A module groups related functions around one concept (e.g. "auth validation", "storage operations", "user queries").
- A file you have to scroll to understand should become a module directory whose index or `__init__` re-exports the public interface.

**Structure Pattern:**
```
# Simple module: a single file is fine
secrets.py              # One concept: loading secrets

# Complex module: split into a directory
services/
├── __init__.py         # Re-exports the public interface
├── clients/            # Grouped by sub-concept
│   ├── storage.py      # Client singletons
│   ├── auth.py         # Auth guard + helpers
│   └── _config.py      # Internal config (not re-exported)
├── logging.py          # Logging setup
└── secrets.py          # Secret management
```

**Reuse Before You Write:**
- Before adding a helper, check, or filter, search for one that already does the job. Search by behavior, not just by name.
- A check or filter written twice gets one shared helper, placed next to the data it's about. Every call site is updated to use it instead of its own copy.
- This is the inverse of the Split Rule. The Split Rule keeps one function from doing two things; this rule keeps two functions from doing the same thing. Consistency (below) applies the same idea to patterns.

**Rationale**: Single-purpose modules are faster to read and easier to test. They give an AI assistant enough context in one file to make a correct change without the whole codebase. Duplication is the same defect from the other direction: a second copy of a check drifts from the first as soon as one of them is fixed and the other isn't.

### Consistency

Every recurring problem MUST have exactly one solution in the codebase. When two call sites solve the same problem differently, one of them is wrong.

**Apply this to:**
- Refreshing data after a write: one invalidation or refetch helper, not ad hoc refetches invented per feature.
- Errors: one error-handling pattern and one shared error-display component. Don't let each feature grow its own.
- Dates and times: one formatter, reused everywhere a date is shown.
- User-facing copy: one home for the strings, so a wording change touches one file.
- Names: one name per concept across code, copy, and docs. If a concept legitimately needs two names (an internal field and its public label, say), write down which name belongs to which. Don't leave the mapping implicit.

**Rationale**: Divergent solutions to one problem are themselves a source of bugs. Fixing one path leaves the others broken, and a newcomer, human or AI, can't tell which pattern is the real one. Solving each recurring problem once, and naming each concept once, keeps the codebase clear enough that an agent can extend it correctly without re-deriving the convention every time.

### Testing Discipline

All code MUST be written so it can be tested. Keep business logic pure (input in, output out). Isolate side effects in boundary functions, which are tested by mocking the shared clients they import.

```python
# CORRECT - pure logic, easy to test without mocks
def validate_email_domain(email: str, valid_domains: list[str]) -> bool:
    domain = email.split("@")[1]
    return domain in valid_domains


# CORRECT - boundary function with side effects, tested by mocking db
async def create_user(email: str, name: str) -> str:
    if not validate_email_domain(email, VALID_DOMAINS):
        raise ValueError("Invalid domain")
    return await db.users.insert({"email": email, "name": name})
```

**Network Isolation:**
All tests MUST run with network access blocked by default. An external call fails the test unless the test explicitly allows it. Typical tools: `pytest-socket` for Python, MSW with `onUnhandledRequest: "error"` or `nock.disableNetConnect()` for JavaScript.

```python
# Default: network blocked, no annotation needed
def test_unit_logic():
    assert process_data({"key": "value"}) is not None


# CORRECT - network explicitly allowed for an integration test
@pytest.mark.enable_socket
def test_external_api_integration(): ...


# CORRECT - specific hosts only
@pytest.mark.allow_hosts(["127.0.0.1", "localhost"])
def test_local_service(): ...
```

**Rationale**: Pure logic is trivial to test, and boundary functions can be tested by mocking their shared clients. Blocking the network keeps tests deterministic and fast, and independent of whether outside services are up.

### Required Test Coverage

All new code MUST include tests. Tests are not optional and MUST NOT be deferred to a later phase. These categories set the minimum coverage:

| Category | What to test | Examples |
|----------|-------------|---------|
| **Pure logic** | Input → output, edge cases, boundary conditions, error cases. No mocks needed: these are the easiest and most valuable tests. | Utility functions, formatters, validators, parsers, algorithms, state machines |
| **Components** | Renders correctly with typical props. Renders gracefully with missing, null or empty data. Key interactions (click, toggle) produce the expected UI change. | UI components, widgets, reusable building blocks |
| **Pages / Views** | A smoke render (catches crashes in the import chain). Loading states. Data display with a mocked API or service layer. Key user flows (navigation, form submit). | Route-level components, screens, full page views |
| **API endpoints / Services** | The request/response shape matches the contract. Validation rejects bad input. Error codes are correct. Side effects happen (DB writes, queue dispatch). | REST endpoints, GraphQL resolvers, service functions that do I/O |
| **App entry (smoke)** | Imports and renders or initializes without runtime errors, which proves the whole dependency tree loads. | App root component, server entry point, CLI entry point |

**Rules:**

1. **Smoke tests are mandatory.** Every app entry point MUST have a test that imports and initializes it. This catches dependency crashes (missing packages, circular imports, bad re-exports) before they reach production.
2. **Test pure logic first.** If a function has no side effects, test it directly. Don't skip a test because the function is simple: untested edge cases in simple functions cause production bugs.
3. **Mock at boundaries, not everywhere.** Mock external I/O (database, APIs, file system). Don't mock internal code. If you have to mock internal code to test something, refactor it so it's testable.
4. **Tests ship with the code.** Tests for new code go in the same PR or commit. "I'll add tests later" means the tests won't be added.
5. **Missing tests block review.** Code without tests for the applicable categories above MUST NOT be approved.

**Rationale**: Untested code is unverified code. Mandatory categories prevent the usual failure, where "we'll add tests later" turns into "tests were never added". Smoke tests alone catch a whole class of production incidents caused by broken import chains and missing dependencies.

### Test Economy

Tests MUST cover each behavior in exactly one place, at the cheapest layer that can observe it. More tests are not more coverage. A bloated suite slows every change and buries the failures that matter.

**Rules:**

1. **One place per behavior.** Test pure logic where it lives, in a unit test for that function, and don't re-verify it from every caller. Test a service or client wrapper at the service layer. An API endpoint test checks wiring only: the right status code, the right service call, the right response shape. It doesn't re-check business rules the service's unit tests already cover. The same split applies on the frontend: hooks get hook tests, components get component tests, and page or route tests check that the right components receive the right props, not what's already proven inside those components.
2. **Test rules, not literals.** Don't write a test whose only job is to restate a constant, a count, a list, or a copy string (see Change-Tolerant Tests and Copy-Resilient Tests). Assert the invariant behind the data. For example, assert "every domain in `VALID_DOMAINS` passes `validate_email_domain`", not "`VALID_DOMAINS` has these 3 entries".
3. **Repeat a case across variants only when the behavior differs.** If two configurations (two models, two environments, two component sizes) run the same code path, one test covers both. Write one test per variant only where the variant changes the outcome.
4. **Recorded output is data, not a contract.** A test over a saved fixture (a recorded LLM or eval transcript, a cached API response, a golden payload) MUST derive its expected values from the fixture itself, not from a second, hand-maintained copy of what the fixture "should" contain. An assertion may only claim what the recording actually supports. When the fixture is wrong or stale, re-record it; don't hand-edit the assertion to match. The exception is a test of a model's own judgment (quality, tone, correctness of reasoning). That belongs in an eval scored by a rubric or an LLM judge, not pinned to one exact recorded output.
5. **The test double holds no business rules.** A mock for a database, storage, auth, or model client stores, replies, and fails on request, and nothing more. It MUST expose only the methods the tests that use it exercise. An operation nothing exercises MUST fail loudly (raise `NotImplementedError` or similar) rather than silently return a default. The rules that decide what a real service does (validation, authorization, business logic) are tested against the service that owns them, never reimplemented inside the double. Tests script what the server does, then verify the caller handles it.
6. **Decision logic lives in pure functions.** Anything with a branch (an `if`, a `match`, a threshold) belongs in a pure function that a test can call directly. It shouldn't be buried in a route handler or a component body, where testing it means standing up the server or rendering the tree. This is Testing Discipline's pure-logic split, applied to branching as well as I/O.
7. **Trimming a test must not lose covered lines.** When removing or consolidating tests, run coverage before and after. The diff MUST NOT drop any line that was covered before, in any file. A test earns its keep by covering a line nothing else covers, and losing that line without a replacement is a regression even if every remaining test passes.
8. **Find the owner before writing.** Before adding a test, search for the test that already owns the behavior and extend or change that one instead of adding another beside it. A new test file or case is only for a behavior that has no owner yet. When a change moves a behavior, its test moves with it: the old test is deleted, not kept alongside the new one. This applies at planning time, not just in review. A task that adds tests MUST name the existing test file it extends, or state plainly that the behavior has no owner yet. "Add tests for X" is not a task.
9. **A test must be able to fail on its own.** A test MUST NOT recompute the code under test to build its expected value (for example, rebuilding an expected column order with the same steps the implementation uses). That only proves the function agrees with itself. A test MUST NOT assert only that a removed field, key, or ID is absent: deleting it is the proof, and a type checker plus the generic unknown-field test (rule 2) already guard it. A test earns its place by being able to fail for a reason the code under test doesn't already guarantee.

**Rationale**: Each rule answers a failure seen in practice:
- the same assertion repeated at every layer
- tests that re-type a constant instead of a rule
- fixture tests that drift from their own recordings
- mocks permissive enough to hide a missing code path
- decision logic that can only be exercised by rendering a page
- test trims that quietly remove the one case that caught a regression
- duplicate tests added because no one looked for an owner first
- tautological or absence-only tests that can't fail for a real reason

The fix is the same each time: test the behavior once, at the layer that owns it, make sure the test can actually fail, and keep the suite's coverage honest as it changes.

### Change-Tolerant Tests

A test MUST fail only when behavior a caller depends on breaks. A test that fails on a change a user or caller would accept (new records in a data file, edited copy, reordered keys, an internal refactor) is brittle and MUST be rewritten. Once written, a test changes only when the requirement it covers changes.

**Rules:**

1. **App data is not test data.** JSON, YAML, seed data, prompt files, and config that the app loads at runtime change as content, not code. Tests MUST NOT pin their record count, their record order, or any single record's content. Every such file MUST have one validation test that checks per-record invariants across *all* records: required fields present, types valid, IDs unique, cross-references resolve, enum values known. That test grows with the data instead of breaking on it.
2. **Tests own their data.** A test that needs exact output builds its own input. Use a builder or factory with valid defaults, where the test overrides only the fields it's about, or a small fixture under `tests/` that exists only for tests. An exact-output test MUST NOT read a file the app loads.
3. **Count only what you created.** A count assertion is allowed only when the test created the inputs (`len(result) == len(items)`, "added 3, got 3 rows"). Against data the test doesn't own, assert existence, a lower bound (`>= 1`), or an invariant per item.
4. **Assert the fields you care about.** Compare the keys under test, not entire dicts, JSON payloads, or response bodies. An extra field or a new optional key MUST NOT fail a test. Don't assert order unless order is the contract (sorted output, pagination); otherwise compare as sets or sort first.
5. **Check outcomes, not call sequences.** Assert returned values and the resulting state. Assert a mock call only when that call is itself the side effect under test (the DB write, the message sent), and then assert the payload that matters, not the call count or order. A test that only checks the mocks were called in the order the code calls them is a change detector and MUST be rewritten or deleted.
6. **No large snapshots.** Full-render, full-page, and full-response snapshots are forbidden: they break on any change to a child, and their diffs get approved without review. Inline snapshots are allowed for small, deliberate output (roughly 20 lines or fewer), with dynamic values such as timestamps and generated IDs masked.
7. **Invariants for wide-input functions.** Parsers, validators, formatters, and normalizers SHOULD get property-based tests (Hypothesis for Python, fast-check for TypeScript) that state the rule: round-trips, idempotence, never raising on valid input. Add a few named example cases alongside them to document intent.
8. **The review question.** For every test, ask: *"Would this fail on a change a user or caller would accept?"* If yes, it's brittle. Fix it before merge.

```python
# WRONG - breaks the day someone adds a plan to the catalog
def test_plan_catalog():
    plans = load_plan_catalog()
    assert len(plans) == 4
    assert plans[0]["id"] == "starter"


# CORRECT - per-record invariants over the whole file the app loads
def test_plan_catalog_records_are_valid():
    plans = load_plan_catalog()
    assert plans
    ids = [p["id"] for p in plans]
    assert len(ids) == len(set(ids))
    for p in plans:
        assert p["tier"] in Tier
        assert p["seats"] > 0


# CORRECT - exact output from data the test owns
def test_filter_enabled_plans():
    plans = [make_plan(enabled=True), make_plan(enabled=False)]
    assert [p["id"] for p in filter_enabled(plans)] == [plans[0]["id"]]


# WRONG - whole-body equality fails when a field is added
assert response.json() == {"id": "u1", "name": "Ada", "role": "admin"}

# CORRECT - assert only the fields under test
assert response.json()["role"] == Role.ADMIN
```

**Rationale**: A brittle test fails without a bug, so every failure costs a diagnosis and teaches the team to distrust red builds. The usual causes are tests pinned to content the app treats as data, counts of things the test didn't create, whole-object equality, assumed ordering, mock call-sequence checks, and large snapshots. Each rule above replaces the incidental detail with the invariant the caller actually relies on. The suite then stays green through content growth and refactors, and goes red only for real regressions.

### Copy-Resilient Tests

Tests MUST NOT match on copy: any human-readable string owned by product, design, or content rather than by code. That covers UI labels, headings, placeholders, button text, error and exception messages, log lines, and prompt text. Copy changes independently of logic, and a test that matches on it fails for no real reason.

**Frontend: locate elements, in this order:**
1. `getByRole` by role alone (scoped with `within()` when needed). Add `name` only when the name comes from mock data or a code constant. This keeps queries close to how users and assistive technology find elements.
2. `data-testid`, when a role alone isn't unique and the only distinguishing name is static copy.
3. DOM structure (tag type, nesting), as a last resort.

**Backend: assert on:**
- HTTP status codes, exception types, and error codes or enum values.
- Structured fields in the response or log record, not the message string. A message-matching assertion (e.g. `pytest.raises(..., match=)`) is allowed only for an identifier or value taken from the test's own input.

**Assert values by:**
- Comparing rendered text or response fields against the mock data the test passed in, not against hardcoded display strings.
- Matching enum or constant values. These are code-level identifiers, not copy.

**Rules:**
1. New components and page sections MUST use semantic elements and ARIA roles, and MUST add a `data-testid` where a role alone can't identify an element.
2. Tests MUST NOT use `getByText`, `getByLabelText`, `getByPlaceholderText`, or `getByRole(..., { name })` with a hardcoded display string.
3. Enum values and typed constants (status codes, category keys) are safe to assert against. They change through code, not through content edits.
4. To check that specific data appears, assert that the rendered text matches the mock input, not a hardcoded expected string.

```tsx
// WRONG - breaks when the copy changes
expect(screen.getByText("Welcome back, friend!")).toBeInTheDocument();
expect(screen.getByRole("button", { name: /submit/i })).toBeEnabled();

// CORRECT - role alone, scoped to the form
expect(within(screen.getByRole("form")).getByRole("button")).toBeEnabled();

// CORRECT - accessible name taken from mock data
expect(screen.getByRole("link", { name: mockProject.title })).toHaveAttribute(
  "href",
  `/projects/${mockProject.id}`,
);

// CORRECT - an enum value is a code constant, not copy
expect(screen.getByTestId("status-badge").textContent).toBe(Status.ACTIVE);
```

```python
# WRONG - breaks when the message is reworded
with pytest.raises(ValueError, match="Email domain is not allowed"):
    validate_user(email="a@other.com")

# CORRECT - exception type, plus a value from the test's own input
with pytest.raises(InvalidDomainError, match="other.com"):
    validate_user(email="a@other.com")

# CORRECT - status and error code, not the detail string
assert response.status_code == 403
assert response.json()["code"] == ErrorCode.INVALID_DOMAIN
```

**Rationale**: Designers, product, and content editors own the copy and change it on their own schedule. Tests coupled to it produce false failures that erode trust in the suite. Role queries keep frontend tests aligned with how users and assistive technology find elements. Test IDs, error codes, and assertions against mock data cover the rest, so tests verify behavior without depending on wording.

### Import-Time Safety

Code that runs at module level (top-level calls in settings files, client initialization, secret loading) MUST be safe to execute with no network access. Network-dependent work MUST be deferred to first use or to an explicit initialization call, and never triggered by `import`.

**Why this matters:** network-blocking test tools and sandboxed environments disable sockets before any test code runs. gRPC and HTTP clients initialized at import time can hang silently under these conditions instead of raising a catchable exception. `except Exception` won't help, because the call never returns.

**Rules:**
- Module-level code MUST NOT open network connections, resolve DNS, or call remote services.
- Client singletons, secret loaders, and configuration fetchers that need the network MUST initialize lazily (on first access, not on import).
- If a module needs a "ready" state that depends on the network, expose an explicit `init()` or `setup()` that callers invoke once the environment is known to be available.

```python
# WRONG - hangs silently when the network is blocked
secrets = SecretClient().get("my-secret")  # runs at import

# CORRECT - lazy initialization on first use
_client = None


def get_client():
    global _client
    if _client is None:
        _client = SomeGrpcClient()
    return _client


# CORRECT - explicit init, called by application startup
def init():
    global secrets
    secrets = SecretClient().get("my-secret")
```

**Rationale**: Network calls at import time tie module loading to network availability. That breaks test isolation, slows startup, and produces failures that standard exception handling can't catch or debug.

### Boundary Logging

Logging MUST happen at system boundaries, not inside every function. Log where data enters or leaves the system, not where it's transformed.

**Boundary points:**
- API endpoint entry (request received)
- External service calls (cloud services, third-party APIs)
- Errors and exceptions
- Startup and shutdown

```python
# CORRECT - log at the boundary
async def get_user(user_id: str) -> dict:
    logger.info("Fetching user: %s", user_id)
    user = await db.users.get(user_id)
    if user is None:
        logger.warning("User not found: %s", user_id)
        raise NotFoundError(user_id)
    return user


# WRONG - logging inside pure logic
def calculate_score(items: list[int]) -> int:
    logger.info("Starting calculation")  # Noise
    return sum(items) * 2
```

**Rationale**: Boundary logging gives observability without noise. Pure functions don't need logging, because tests verify their behavior. Logging at the edges makes it easy to trace a request through the system.

### Quality Gates

All commits MUST pass the pre-commit hooks. Never use `--no-verify` to bypass them.

| Hook | Purpose | Fix command |
|------|---------|-------------|
| QUALITY_GATES | | |

**Hook configuration:** HOOK_CONFIG_PATH

**Rationale**: Pre-commit gates catch issues before they enter the codebase. They keep quality consistent and prevent CI failures.

### No Backwards Compatibility Before First Release

Until the project's first production release, breaking changes MUST be made outright. Replace code, schemas, and data shapes directly. Don't add shims, aliases, dual-write paths, or migrations for data that doesn't matter yet.

```python
# WRONG - a compatibility shim for a pre-release schema
def get_user_email(user: dict) -> str:
    return user.get("email") or user.get("email_address")  # old field kept "just in case"


# CORRECT - rename outright and fix the (few) callers
def get_user_email(user: dict) -> str:
    return user["email"]
```

**Rationale**: Shims exist to protect data or callers that must keep working. Before a first release there are no production callers and no data worth preserving, so a shim only adds a second code path to maintain and a leftover nobody will read. Once the project ships, remove this principle and apply standard migration discipline.

### Existing Conventions Are the Baseline

The project's established setup is a working system, not a starting point to improve. Its conventions are decided, and features build on them.

- **Don't change what works.** Configuration loading, data-store wiring, the local dev and emulator setup, and the build and task-runner shape (see Project Patterns) MUST stay as they are, unless a feature's spec says otherwise in so many words.
- **Fewest moving parts wins.** Prefer a documented command over a script, a script over a task-runner target, and a target over a CI workflow. Don't add pipelines, generated config files, service identities, or per-environment plumbing unless the owner asks for them by name.
- **Platform defaults over explicit flags.** Deploy and run commands MUST pass only what the app needs. Don't add flags, labels, env vars, or settings that restate a default.
- **One knob per fact.** Each environment fact is set in exactly one place. If a value can be derived (from the platform, from metadata, from another setting), derive it; don't add a variable for it.
- **No new settings without a consumer.** Every new configuration key MUST be read by code that ships in the same feature, and that code MUST be tested.
- **Ask before inventing infrastructure.** If a plan needs a resource, role, secret, or environment the project doesn't already have, the plan MUST list it as an open question for the owner. Assumed infrastructure is a defect.
- **Confirm the reading before editing.** When an instruction can be read two ways, confirm which one is meant before touching a file the owner wrote.

**Rationale**: The existing setup encodes decisions that were already paid for. Rebuilding them inside a feature costs review time and hides accidental changes among the intentional ones.

## Project Patterns

PROJECT_PATTERNS

## Governance

This constitution documents patterns that MUST be followed to keep the codebase consistent.

**Precedence**: Spec before plan, plan before code. If a spec conflicts with this constitution, the spec is wrong: fix the spec, not the code. The constitution itself changes only through the amendment process below.

**Spec Freshness**: Every spec records the commit it was checked against. If the code has moved since, re-check the spec against the current state before building from it.

**Living Docs vs. Specs**: Guides and architecture docs describe the current code, and they change in the same commit as the code they describe. A spec is a record of a decision. Once it ships, only its status and checkboxes change: its body is history, not a living doc.

**Amendment Process:**
1. Propose the change in a PR that modifies this file.
2. Document the rationale for the pattern change.
3. Increment the version using semantic versioning.

**Versioning:**
- MAJOR: a pattern removed or changed incompatibly
- MINOR: a new pattern or utility added
- PATCH: clarifications or examples

**Version**: 1.0.0 | **Ratified**: RATIFIED_DATE | **Last Amended**: RATIFIED_DATE
