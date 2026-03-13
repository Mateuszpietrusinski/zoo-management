# Phase 4 — Feature 2: Animal Admission to Enclosure

**Goal:** Implement the most complex business process — animal admission with conditional health check, enclosure type matching, and admission record creation. This is the feature with the most branching logic.

**Depends on:** Phase 1 (domain), Phase 2 (in-memory adapter), Phase 3 (patterns established).
**Unlocks:** Phase 5 (feeding round needs animals in enclosures).

**Architecture references:**
- Process sequence: architecture.md C4.4 Process 2
- Use case DTOs: architecture.md C4.3 `AdmitAnimalUseCase`
- Endpoint: `POST /animals/{animal_id}/admit` → 201 Created
- BDD scenarios: bdd-scenarios.md Process 1
- ADR-002 (health check fields), ADR-012 (first match), ADR-013 (already placed guard), ADR-020 (taxonomic_type matching)

---

## Step 4.1 — BDD Feature File ✅

**File:** `features/animal_admission.feature`

**Write Gherkin scenarios first:**

```gherkin
Feature: Animal Admission to Enclosure
  As a zoo manager
  I want to admit a new animal to a suitable enclosure
  So that it is correctly housed and has an assigned caretaker

  Scenario: Admit internal animal without health check
    Given an internal lion "animal-lion-1" exists but is not placed
    And a mammal enclosure "enc-mammal-1" exists in zoo "zoo-1"
    When the zoo admits animal "animal-lion-1" to zoo "zoo-1"
    Then the animal is placed in enclosure "enc-mammal-1"
    And an admission record is created

  Scenario: Admit external animal with health check — cleared
    Given an external penguin "animal-penguin-ext" exists but is not placed
    And a bird enclosure "enc-bird-1" exists in zoo "zoo-1"
    And a veterinarian "emp-vet-1" exists in zoo "zoo-1"
    When the zoo admits animal "animal-penguin-ext" to zoo "zoo-1" with vet "emp-vet-1" result "healthy"
    Then the animal is placed in enclosure "enc-bird-1"
    And a health check record is created
    And an admission record is created with health_check_record_id

  Scenario: Admit external animal fails — not cleared
    Given an external lion "animal-lion-ext" exists but is not placed
    And a mammal enclosure "enc-mammal-1" exists in zoo "zoo-1"
    And a veterinarian "emp-vet-1" exists in zoo "zoo-1"
    When the zoo attempts to admit "animal-lion-ext" with vet "emp-vet-1" result "critical"
    Then the admission fails with HealthCheckNotClearedError
    And the animal remains unplaced

  Scenario: Admission fails — no suitable enclosure
    Given an internal crocodile "animal-croc-1" exists but is not placed
    And no reptile enclosure exists in zoo "zoo-1"
    When the zoo attempts to admit "animal-croc-1" to zoo "zoo-1"
    Then the admission fails with NoSuitableEnclosureError

  Scenario: Admission fails — animal already placed (ADR-013)
    Given a lion "animal-lion-placed" already placed in enclosure "enc-mammal-1"
    When the zoo attempts to admit "animal-lion-placed" to zoo "zoo-1"
    Then the admission fails with AnimalAlreadyPlacedError
```

---

## Step 4.2 — Unit Tests for AdmitAnimalUseCase ✅

**File:** `tests/unit/test_admit_animal.py`

**Tests first (fresh InMemoryRepositories per test):**

```
- test_admit_internal_animal_happy_path
    Setup: Lion(origin=INTERNAL, enclosure_id=None), Enclosure(type=MAMMAL).
    Execute: AdmitAnimalRequest(animal_id=..., zoo_id=..., vet_id=None, ...)
    Assert: response has animal_id, enclosure_id, admission_record_id.
            Animal.enclosure_id is set. Animal is in enclosure.animals list.
            AdmissionRecord saved. No HealthCheckRecord created.

- test_admit_internal_animal_ignores_health_fields (ADR-002)
    Setup: Internal animal. Pass vet_id and health_check_result in request.
    Assert: No error raised. No HealthCheckRecord created. Fields silently ignored.

- test_admit_external_animal_with_healthy_result
    Setup: Penguin(origin=EXTERNAL). Veterinarian. Bird enclosure.
    Execute: vet_id=..., health_check_result=HEALTHY.
    Assert: Animal placed. HealthCheckRecord created. AdmissionRecord has health_check_record_id.

- test_admit_external_animal_raises_health_check_not_cleared_for_non_healthy
    Setup: External lion. Vet. health_check_result=CRITICAL.
    Assert: raises HealthCheckNotClearedError. Animal not placed.

- test_admit_external_animal_raises_invalid_request_when_vet_id_missing
    Setup: External animal. vet_id=None.
    Assert: raises InvalidRequestError.

- test_admit_external_animal_raises_invalid_request_when_result_missing
    Setup: External animal. health_check_result=None.
    Assert: raises InvalidRequestError.

- test_admit_external_animal_raises_invalid_employee_role_for_non_vet
    Setup: External animal. Pass a Zookeeper id as vet_id.
    Assert: raises InvalidEmployeeRoleError.

- test_admit_raises_entity_not_found_for_missing_animal
    Execute with non-existent animal_id.
    Assert: raises EntityNotFoundError.

- test_admit_raises_animal_already_placed_when_enclosure_set (ADR-013)
    Setup: Lion with enclosure_id already set.
    Assert: raises AnimalAlreadyPlacedError.

- test_admit_raises_no_suitable_enclosure_when_type_mismatch (ADR-020)
    Setup: Crocodile (Reptile), only MAMMAL enclosures available.
    Assert: raises NoSuitableEnclosureError.

- test_admit_selects_first_matching_enclosure (ADR-012)
    Setup: Two mammal enclosures. Verify first one is selected.
    Assert: Animal placed in first matching enclosure.

- test_admission_record_has_zookeeper_id_from_enclosure (ADR-004)
    Setup: Enclosure with assigned_zookeeper_id = "emp-zk-1".
    Assert: AdmissionRecord.zookeeper_id == "emp-zk-1".

- test_admission_record_has_none_zookeeper_when_enclosure_unassigned (ADR-004)
    Setup: Enclosure with assigned_zookeeper_id = None.
    Assert: AdmissionRecord.zookeeper_id is None.
```

---

## Step 4.3 — Implement AdmitAnimalUseCase ✅

**File:** `zoo_management/usecases/admit_animal.py`

**Implementation flow (from architecture.md C4.4 Process 2):**

```python
class AdmitAnimalUseCase:
    def __init__(self, animal_repo, enclosure_repo, employee_repo, admission_repo, health_repo):
        ...

    def execute(self, req: AdmitAnimalRequest) -> AdmitAnimalResponse:
        # 1. Fetch animal by id (raises EntityNotFoundError)
        # 2. Check animal.is_placed — raise AnimalAlreadyPlacedError if True (ADR-013)
        # 3. If origin == EXTERNAL:
        #    a. Validate vet_id and health_check_result not None — raise InvalidRequestError
        #    b. Fetch employee by vet_id
        #    c. isinstance check for Veterinarian — raise InvalidEmployeeRoleError
        #    d. Check health_check_result == HEALTHY — raise HealthCheckNotClearedError
        #    e. Create HealthCheckRecord, save it
        # 4. If origin == INTERNAL: silently ignore health fields
        # 5. get_by_zoo(zoo_id) — get all enclosures
        # 6. Filter: enclosure_type.value == animal.taxonomic_type (ADR-020)
        # 7. If no match — raise NoSuitableEnclosureError
        # 8. Select first match (ADR-012)
        # 9. animal.enclosure_id = enclosure.id
        # 10. enclosure.animals.append(animal) (ADR-001)
        # 11. zookeeper_id = enclosure.assigned_zookeeper_id (may be None, ADR-004)
        # 12. Save animal, save enclosure
        # 13. Create AdmissionRecord with health_check_record_id (ADR-027)
        # 14. Save AdmissionRecord
        # 15. Return AdmitAnimalResponse
```

**Verification:** `pytest tests/unit/test_admit_animal.py` — all pass.

---

## Step 4.4 — Integration Tests for Animal Admission Router ✅

**File:** `tests/integration/test_admit_animal_router.py`

**Tests first:**

```
- test_admit_internal_animal_returns_201
    POST /animals/{id}/admit with {zoo_id: "zoo-1"}.
    Assert: 201 Created, body has animal_id, enclosure_id, admission_record_id.

- test_admit_external_animal_returns_201_with_health_check
    POST with {zoo_id, vet_id, health_check_result: "healthy"}.
    Assert: 201 Created.

- test_admit_returns_404_for_missing_animal
    POST /animals/nonexistent/admit.
    Assert: 404, {"detail": "..."}.

- test_admit_returns_422_for_already_placed_animal
    Assert: 422.

- test_admit_returns_422_for_health_check_not_cleared
    External animal with result "critical".
    Assert: 422.

- test_admit_returns_422_for_no_suitable_enclosure
    Assert: 422.
```

---

## Step 4.5 — Implement Router Endpoint ✅

**File:** `zoo_management/adapters/web/routers.py` (add endpoint)

```python
@router.post("/animals/{animal_id}/admit", status_code=201)
def admit_animal(
    animal_id: str,
    body: AdmitAnimalRequestSchema,
    use_case: AdmitAnimalUseCase = Depends(get_admit_animal_use_case),
) -> AdmitAnimalResponseSchema:
    ...
```

**Pydantic schemas:**
```python
class AdmitAnimalRequestSchema(BaseModel):
    zoo_id: str
    vet_id: str | None = None
    health_check_result: str | None = None  # maps to HealthResult enum
    health_check_notes: str | None = None

class AdmitAnimalResponseSchema(BaseModel):
    animal_id: str
    enclosure_id: str
    admission_record_id: str
```

**Add new exception handlers:**
- `NoSuitableEnclosureError → 422`
- `HealthCheckNotClearedError → 422`
- `AnimalAlreadyPlacedError → 422`
- `InvalidRequestError → 422`

---

## Step 4.6 — GET Endpoints for State Verification (ADR-021) ✅

**Important:** Implement the two GET endpoints needed by graders to verify state after admission:

**File:** `zoo_management/adapters/web/routers.py`

```python
@router.get("/animals/{animal_id}", status_code=200)
def get_animal(animal_id: str, ...) -> AnimalResponse:
    ...

@router.get("/enclosures/{enclosure_id}", status_code=200)
def get_enclosure(enclosure_id: str, ...) -> EnclosureResponse:
    ...
```

**Response schemas (exact field names from architecture.md M-3):**

```python
class AnimalResponse(BaseModel):
    id: str
    name: str
    origin: str
    enclosure_id: str | None
    type_name: str          # concrete class name, e.g. "Lion"
    taxonomic_type: str     # mid-tier ABC name, e.g. "Mammal"
    diet_type: str          # result of get_diet_type()

class EnclosureResponse(BaseModel):
    id: str
    name: str
    enclosure_type: str
    zoo_id: str
    assigned_zookeeper_id: str | None
    animal_count: int
    animal_ids: list[str]
```

**Integration tests for GET endpoints:**
```
- test_get_animal_returns_200_with_correct_fields
- test_get_animal_returns_404_for_missing
- test_get_enclosure_returns_200_with_correct_fields
- test_get_enclosure_returns_404_for_missing
```

---

## Step 4.7 — BDD Step Definitions ✅

**File:** `tests/step_defs/test_animal_admission_steps.py`

Implement Given/When/Then steps for all 5 BDD scenarios.

---

## Step 4.8 — Lint, Type Check, and Commit ✅

**Action:**
1. Run full test suite.
2. `ruff check` + `mypy` on changed files.
3. `git add . && git commit -m "feat: animal admission — use case, router, GET endpoints, tests, BDD"`

---

## Phase 4 Completion Checklist

- [x] `AdmitAnimalRequest` and `AdmitAnimalResponse` DTOs
- [x] `AdmitAnimalUseCase.execute()` with all branching logic
- [x] External animal health check flow (ADR-002)
- [x] `AnimalAlreadyPlacedError` guard (ADR-013)
- [x] `taxonomic_type` matching for enclosure selection (ADR-020)
- [x] First-match enclosure selection (ADR-012)
- [x] `AdmissionRecord.health_check_record_id` linkage (ADR-027)
- [x] Router `POST /animals/{id}/admit` → 201
- [x] `GET /animals/{id}` and `GET /enclosures/{id}` with exact field names (ADR-021)
- [x] New exception handlers added
- [x] ~13 unit tests pass
- [x] ~10 integration tests pass (including GET endpoints)
- [x] 5 BDD scenarios pass
- [x] ruff and mypy clean

---

**Previous phase:** [Phase 3 — Assign Zookeeper](phase-3-feature-assign-zookeeper.md)
**Next phase:** [Phase 5 — Feature 3: Execute Feeding Round](phase-5-feature-feeding-round.md)
