# Phase 6 — Feature 4: Conduct Health Check

**Goal:** Implement the standalone health check process — the simplest use case after assign zookeeper. A veterinarian examines an animal and the result is recorded.

**Depends on:** Phase 1–2 (domain + adapter).
**Unlocks:** Independent (but health check is also embedded in admission flow).

**Architecture references:**
- Process sequence: architecture.md C4.4 Process 4
- Use case DTOs: architecture.md C4.3 `ConductHealthCheckUseCase`
- Endpoint: `POST /animals/{animal_id}/health-checks` → 201 Created
- BDD scenarios: bdd-scenarios.md Process 3

---

## ✓ Step 6.1 — BDD Feature File

**File:** `features/health_check.feature`

```gherkin
Feature: Conduct Health Check
  As a veterinarian
  I want to conduct a health check on an animal and record the result
  So that the zoo can track health and schedule follow-up

  Scenario: Health check result is Healthy
    Given an animal "animal-lion-1" exists in the system
    And a veterinarian "emp-vet-1" exists in the system
    When veterinarian "emp-vet-1" conducts a health check on "animal-lion-1" with result "healthy"
    Then a health check record is created with result "healthy"

  Scenario: Health check result is Need Follow-Up
    Given an animal "animal-penguin-1" exists in the system
    And a veterinarian "emp-vet-1" exists in the system
    When veterinarian "emp-vet-1" conducts a health check on "animal-penguin-1" with result "need_follow_up"
    Then a health check record is created with result "need_follow_up"

  Scenario: Health check result is Critical
    Given an animal "animal-lion-1" exists in the system
    And a veterinarian "emp-vet-1" exists in the system
    When veterinarian "emp-vet-1" conducts a health check on "animal-lion-1" with result "critical"
    Then a health check record is created with result "critical"

  Scenario: Health check fails — employee is not a veterinarian
    Given an animal "animal-lion-1" exists in the system
    And a zookeeper "emp-zk-1" exists in the system
    When zookeeper "emp-zk-1" attempts to conduct a health check on "animal-lion-1"
    Then the health check fails with InvalidEmployeeRoleError
```

**Done.**

---

## ✓ Step 6.2 — Unit Tests for ConductHealthCheckUseCase

**File:** `tests/unit/test_conduct_health_check.py`

**Tests first:**

```
- test_health_check_healthy_creates_record
    Setup: Lion in repo. Veterinarian in repo.
    Execute: HealthCheckRequest(animal_id, vet_id, result=HEALTHY, notes=None)
    Assert: response has health_check_record_id and result == HEALTHY.
            HealthCheckRecord saved in repo with correct fields.

- test_health_check_need_follow_up_creates_record
    Assert: result == NEED_FOLLOW_UP.

- test_health_check_critical_creates_record
    Assert: result == CRITICAL.

- test_health_check_with_notes
    Execute with notes="Slight limp observed".
    Assert: HealthCheckRecord.notes == "Slight limp observed".

- test_health_check_notes_default_none
    Execute without notes.
    Assert: HealthCheckRecord.notes is None.

- test_health_check_raises_entity_not_found_for_missing_animal
    Assert: raises EntityNotFoundError.

- test_health_check_raises_entity_not_found_for_missing_employee
    Assert: raises EntityNotFoundError.

- test_health_check_raises_invalid_employee_role_for_non_vet
    Setup: Pass a Zookeeper id.
    Assert: raises InvalidEmployeeRoleError.

- test_health_check_record_date_is_today
    Assert: HealthCheckRecord.date == date.today().
```

**Done.**

---

## ✓ Step 6.3 — Implement ConductHealthCheckUseCase

**File:** `zoo_management/usecases/conduct_health_check.py`

**Implementation (from architecture.md C4.4 Process 4):**

```python
class ConductHealthCheckUseCase:
    def __init__(self, animal_repo, employee_repo, health_repo):
        ...

    def execute(self, req: HealthCheckRequest) -> HealthCheckResponse:
        # 1. animal_repo.get_by_id(animal_id) — raises EntityNotFoundError
        # 2. employee_repo.get_by_id(vet_id) — raises EntityNotFoundError
        # 3. isinstance(employee, Veterinarian) — raises InvalidEmployeeRoleError
        # 4. Create HealthCheckRecord(id=uuid, date=today, animal_id, vet_id, result, notes)
        # 5. health_repo.save(record)
        # 6. Log with extra={animal_id, vet_id, result}
        # 7. Return HealthCheckResponse(health_check_record_id, result)
```

**Verification:** `pytest tests/unit/test_conduct_health_check.py` — all pass.

**Done.**

---

## ✓ Step 6.4 — Integration Tests for Health Check Router

**File:** `tests/integration/test_health_check_router.py`

**Tests first:**

```
- test_health_check_returns_201_with_record_id
    POST /animals/{id}/health-checks with {vet_id, result: "healthy"}.
    Assert: 201 Created, body has health_check_record_id and result.

- test_health_check_with_notes_returns_201
    POST with notes="observation".
    Assert: 201.

- test_health_check_returns_404_for_missing_animal
    Assert: 404.

- test_health_check_returns_422_for_non_vet_role
    Assert: 422.

- test_health_check_critical_returns_201
    POST with result: "critical".
    Assert: 201 (all results are valid — no error for critical).
```

**Done.**

---

## ✓ Step 6.5 — Implement Router Endpoint

**File:** `zoo_management/adapters/web/routers.py`

```python
@router.post("/animals/{animal_id}/health-checks", status_code=201)
def conduct_health_check(
    animal_id: str,
    body: HealthCheckRequestSchema,
    use_case: ConductHealthCheckUseCase = Depends(get_conduct_health_check_use_case),
) -> HealthCheckResponseSchema:
    ...
```

**Pydantic schemas:**
```python
class HealthCheckRequestSchema(BaseModel):
    vet_id: str
    result: str   # maps to HealthResult enum
    notes: str | None = None

class HealthCheckResponseSchema(BaseModel):
    health_check_record_id: str
    result: str
```

**Done.**

---

## ✓ Step 6.6 — BDD Step Definitions

**File:** `tests/step_defs/test_health_check_steps.py`

**Done.**

---

## ✓ Step 6.7 — Lint, Type Check, and Commit

```bash
git add . && git commit -m "feat: conduct health check — use case, router, tests, BDD"
```

**Done.**

---

## Phase 6 Completion Checklist

- [x] `HealthCheckRequest` and `HealthCheckResponse` DTOs
- [x] `ConductHealthCheckUseCase.execute()` with role validation
- [x] HealthCheckRecord created with date, animal_id, vet_id, result, notes
- [x] Router `POST /animals/{id}/health-checks` → 201
- [x] Pydantic request/response schemas
- [x] ~9 unit tests pass
- [x] ~5 integration tests pass
- [x] 4 BDD scenarios pass
- [x] ruff and mypy clean (Phase 6 files)

---

**Previous phase:** [Phase 5 — Feeding Round](phase-5-feature-feeding-round.md)
**Next phase:** [Phase 7 — Feature 5: Conduct Guided Tour](phase-7-feature-guided-tour.md)
