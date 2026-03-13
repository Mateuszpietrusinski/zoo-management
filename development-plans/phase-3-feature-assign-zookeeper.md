# Phase 3 — Feature 1: Assign Zookeeper to Enclosure

**Goal:** Implement the first business process end-to-end: use case, router, exception handling, BDD feature, and all three test layers. This is the simplest feature and establishes the pattern for all subsequent features.

**Depends on:** Phase 1 (domain), Phase 2 (in-memory adapter).
**Unlocks:** Phase 4 (animal admission depends on zookeeper assignment).

**Architecture references:**
- Process sequence: architecture.md C4.4 Process 1
- Use case DTOs: architecture.md C4.3 `AssignZookeeperUseCase`
- Endpoint: `POST /enclosures/{enclosure_id}/zookeeper` → 200 OK
- BDD scenarios: bdd-scenarios.md Process 4

---

## Step 3.1 — BDD Feature File ✅

**File:** `features/assign_zookeeper.feature`

**Write the Gherkin scenarios first (from bdd-scenarios.md):**

```gherkin
Feature: Assign Zookeeper to Enclosure
  As a zoo manager
  I want to assign a zookeeper to an enclosure
  So that feeding and daily care are clearly owned

  Scenario: Successfully assign zookeeper to enclosure
    Given an enclosure "enc-mammal-1" exists in zoo "zoo-1"
    And a zookeeper "emp-zk-1" exists in zoo "zoo-1"
    When the zoo assigns zookeeper "emp-zk-1" to enclosure "enc-mammal-1" in zoo "zoo-1"
    Then enclosure "enc-mammal-1" has zookeeper "emp-zk-1" assigned

  Scenario: Reassign enclosure to different zookeeper (idempotent, ADR-031)
    Given an enclosure "enc-mammal-1" exists in zoo "zoo-1" with zookeeper "emp-zk-1" assigned
    And a zookeeper "emp-zk-2" exists in zoo "zoo-1"
    When the zoo assigns zookeeper "emp-zk-2" to enclosure "enc-mammal-1" in zoo "zoo-1"
    Then enclosure "enc-mammal-1" has zookeeper "emp-zk-2" assigned

  Scenario: Assignment fails — enclosure not in zoo
    Given an enclosure "enc-mammal-1" exists in zoo "zoo-1"
    And a zookeeper "emp-zk-1" exists in zoo "zoo-1"
    When the zoo attempts to assign zookeeper "emp-zk-1" to enclosure "enc-mammal-1" in zoo "zoo-other"
    Then the assignment fails with EnclosureNotInZooError

  Scenario: Assignment fails — employee is not a zookeeper
    Given an enclosure "enc-mammal-1" exists in zoo "zoo-1"
    And a guide "emp-guide-1" exists in zoo "zoo-1"
    When the zoo attempts to assign employee "emp-guide-1" as zookeeper to enclosure "enc-mammal-1" in zoo "zoo-1"
    Then the assignment fails with InvalidEmployeeRoleError
```

---

## Step 3.2 — Unit Tests for AssignZookeeperUseCase ✅

**File:** `tests/unit/test_assign_zookeeper.py`

**Tests first (constructor injection of fresh InMemoryRepositories):**

```
- test_assign_zookeeper_happy_path
    Setup: create Enclosure(zoo_id="zoo-1"), Zookeeper(zoo_id="zoo-1"), save both.
    Execute: use_case.execute(AssignZookeeperRequest(zoo_id="zoo-1", enclosure_id=..., zookeeper_id=...))
    Assert: response contains correct enclosure_id and zookeeper_id;
            enclosure in repo now has assigned_zookeeper_id set.

- test_assign_zookeeper_idempotent_same_zookeeper (ADR-031)
    Setup: enclosure already has zookeeper_id = "emp-zk-1".
    Execute: assign same zookeeper again.
    Assert: 200 OK equivalent (no exception), zookeeper_id unchanged.

- test_assign_zookeeper_replaces_previous
    Setup: enclosure has zookeeper "A".
    Execute: assign zookeeper "B".
    Assert: enclosure now has zookeeper "B".

- test_assign_zookeeper_raises_entity_not_found_for_missing_enclosure
    Execute with non-existent enclosure_id.
    Assert: raises EntityNotFoundError.

- test_assign_zookeeper_raises_entity_not_found_for_missing_employee
    Execute with non-existent zookeeper_id.
    Assert: raises EntityNotFoundError.

- test_assign_zookeeper_raises_invalid_employee_role_for_non_zookeeper
    Setup: save a Guide, not a Zookeeper.
    Execute: try to assign Guide as zookeeper.
    Assert: raises InvalidEmployeeRoleError.

- test_assign_zookeeper_raises_enclosure_not_in_zoo_when_zoo_ids_mismatch
    Setup: enclosure in zoo-1, zookeeper in zoo-2, request with zoo-1.
    Assert: raises EnclosureNotInZooError.

- test_assign_zookeeper_raises_enclosure_not_in_zoo_when_request_zoo_id_mismatches_enclosure
    Setup: enclosure in zoo-1, request with zoo-2.
    Assert: raises EnclosureNotInZooError (three-way check per ADR-016).
```

---

## Step 3.3 — Implement AssignZookeeperUseCase ✅

**File:** `zoo_management/usecases/assign_zookeeper.py`

**Implementation (from architecture.md C4.3 + C4.4 Process 1):**

```python
from dataclasses import dataclass
from zoo_management.domain.interfaces import EnclosureRepository, EmployeeRepository
from zoo_management.domain.entities import Zookeeper
from zoo_management.domain.exceptions import InvalidEmployeeRoleError, EnclosureNotInZooError

@dataclass(frozen=True)
class AssignZookeeperRequest:
    zoo_id: str
    enclosure_id: str
    zookeeper_id: str

@dataclass(frozen=True)
class AssignZookeeperResponse:
    enclosure_id: str
    zookeeper_id: str

class AssignZookeeperUseCase:
    def __init__(self, enclosure_repo: EnclosureRepository, employee_repo: EmployeeRepository) -> None:
        ...

    def execute(self, req: AssignZookeeperRequest) -> AssignZookeeperResponse:
        # 1. get_by_id(enclosure_id) — raises EntityNotFoundError if missing
        # 2. get_by_id(zookeeper_id) — raises EntityNotFoundError if missing
        # 3. isinstance(employee, Zookeeper) — raises InvalidEmployeeRoleError
        # 4. Three-way zoo_id check (ADR-016) — raises EnclosureNotInZooError
        # 5. enclosure.assigned_zookeeper_id = zookeeper.id
        # 6. save(enclosure)
        # 7. Return AssignZookeeperResponse
        ...
```

**Key rules:**
- Three-way equality: `enclosure.zoo_id == req.zoo_id == zookeeper.zoo_id` (ADR-016).
- Idempotent re-assignment: no error if same zookeeper already assigned (ADR-031).
- Log with `extra={"enclosure_id": ..., "zookeeper_id": ...}`.

**Verification:** `pytest tests/unit/test_assign_zookeeper.py` — all pass.

---

## Step 3.4 — Integration Tests for Assign Zookeeper Router ✅

**File:** `tests/integration/test_assign_zookeeper_router.py`

**Tests first (httpx.Client with ASGITransport, ADR-005):**

```
- test_assign_zookeeper_returns_200_with_correct_body
    Setup: dependency_overrides with fresh InMemoryRepositories, seed enclosure + zookeeper.
    POST /enclosures/{id}/zookeeper with body {zookeeper_id, zoo_id}.
    Assert: status 200, JSON body = {enclosure_id, zookeeper_id}.

- test_assign_zookeeper_returns_404_for_missing_enclosure
    POST with non-existent enclosure_id in path.
    Assert: status 404, {"detail": "..."}.

- test_assign_zookeeper_returns_422_for_invalid_role
    Setup: seed a Guide instead of Zookeeper.
    POST with guide's id.
    Assert: status 422, {"detail": "..."}.

- test_assign_zookeeper_returns_422_for_zoo_mismatch
    Setup: enclosure zoo-1, zookeeper zoo-2.
    POST with zoo_id = "zoo-1".
    Assert: status 422, {"detail": "..."}.
```

**Test pattern (sync, ADR-005):**
```python
from httpx import ASGITransport, Client

def test_...:
    repo = InMemoryRepositories()
    # seed data
    app.dependency_overrides[get_assign_zookeeper_use_case] = lambda: AssignZookeeperUseCase(repo, repo)
    try:
        transport = ASGITransport(app=app)
        with Client(transport=transport, base_url="http://test") as client:
            response = client.post(f"/enclosures/{enc_id}/zookeeper", json={...})
            assert response.status_code == 200
    finally:
        app.dependency_overrides.clear()
```

---

## Step 3.5 — Implement Router and Exception Handlers (Partial) ✅

**File:** `zoo_management/adapters/web/routers.py` (first endpoint)
**File:** `zoo_management/adapters/web/exception_handlers.py` (first handlers)

**Router implementation:**
```python
@router.post("/enclosures/{enclosure_id}/zookeeper", status_code=200)
def assign_zookeeper(
    enclosure_id: str,
    body: AssignZookeeperRequestSchema,
    use_case: AssignZookeeperUseCase = Depends(get_assign_zookeeper_use_case),
) -> AssignZookeeperResponseSchema:
    req = AssignZookeeperRequest(
        zoo_id=body.zoo_id,
        enclosure_id=enclosure_id,
        zookeeper_id=body.zookeeper_id,
    )
    result = use_case.execute(req)
    return AssignZookeeperResponseSchema(
        enclosure_id=result.enclosure_id,
        zookeeper_id=result.zookeeper_id,
    )
```

**Pydantic schemas (request body and response):**
```python
class AssignZookeeperRequestSchema(BaseModel):
    zookeeper_id: str
    zoo_id: str

class AssignZookeeperResponseSchema(BaseModel):
    enclosure_id: str
    zookeeper_id: str
```

**Exception handlers (first batch):**
```python
def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(EntityNotFoundError)
    def entity_not_found(...): return JSONResponse(status_code=404, ...)

    @app.exception_handler(EnclosureNotInZooError)
    def enclosure_not_in_zoo(...): return JSONResponse(status_code=422, ...)

    @app.exception_handler(InvalidEmployeeRoleError)
    def invalid_role(...): return JSONResponse(status_code=422, ...)
```

**Verification:** `pytest tests/integration/test_assign_zookeeper_router.py` — all pass.

---

## Step 3.6 — BDD Step Definitions ✅

**File:** `tests/step_defs/test_assign_zookeeper_steps.py`

**Implement Given/When/Then steps that map to use case calls using fresh InMemoryRepositories per scenario.**

Key patterns:
- `Given` steps create entities and save them to a fresh `InMemoryRepositories`.
- `When` steps call `use_case.execute()`.
- `Then` steps assert on the response DTO or on the repository state.
- Use `pytest-bdd` decorators: `@scenario`, `@given`, `@when`, `@then`.

**Verification:** `pytest tests/step_defs/test_assign_zookeeper_steps.py` — all scenarios pass.

---

## Step 3.7 — Lint, Type Check, and Commit ✅

**Action:**
1. `ruff check zoo_management/usecases/assign_zookeeper.py zoo_management/adapters/`
2. `mypy zoo_management/usecases/assign_zookeeper.py zoo_management/adapters/`
3. `pytest tests/` — full suite.
4. `git add . && git commit -m "feat: assign zookeeper to enclosure — use case, router, tests, BDD"`

---

## Phase 3 Completion Checklist

- [x] `AssignZookeeperRequest` and `AssignZookeeperResponse` DTOs (frozen dataclass)
- [x] `AssignZookeeperUseCase.execute()` with three-way zoo check (ADR-016)
- [x] Idempotent re-assignment (ADR-031)
- [x] Router `POST /enclosures/{id}/zookeeper` → 200
- [x] Exception handlers for `EntityNotFoundError`, `EnclosureNotInZooError`, `InvalidEmployeeRoleError`
- [x] Pydantic request/response schemas
- [x] ~8 unit tests pass
- [x] ~4 integration tests pass
- [x] 4 BDD scenarios pass
- [x] ruff and mypy clean

---

**Previous phase:** [Phase 2 — In-Memory Adapter](phase-2-in-memory-adapter.md)
**Next phase:** [Phase 4 — Feature 2: Animal Admission](phase-4-feature-animal-admission.md)
