# PROJECT_NAME Principles: Examples

<!--
codekit baseline. `/codekit init` writes this to docs/PRINCIPLES-EXAMPLES.md next to the constitution.
The constitution holds the rules; this file holds the WRONG/CORRECT examples for them.
Translate the examples to the project's primary language and drop stacks it doesn't use.
Remove this comment when filled.
-->

Examples for the principles in the constitution. Each heading matches one there.

## Modular Code

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

## Testing Discipline

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

## Change-Tolerant Tests

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

## Copy-Resilient Tests

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

## Import-Time Safety

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

## Boundary Logging

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

## No Backwards Compatibility Before First Release

```python
# WRONG - a compatibility shim for a pre-release schema
def get_user_email(user: dict) -> str:
    return user.get("email") or user.get("email_address")  # old field kept "just in case"


# CORRECT - rename outright and fix the (few) callers
def get_user_email(user: dict) -> str:
    return user["email"]
```
