# Phase 5 — Feature 3: Execute Feeding Round

**Goal:** Implement the feeding round process with schedule matching, zookeeper assignment validation, polymorphic `get_diet_type()` dispatch, and the note response pattern.

**Depends on:** Phase 1–2 (domain + adapter), Phase 3 (zookeeper assignment patterns).
**Unlocks:** Independent of other features.

**Architecture references:**
- Process sequence: architecture.md C4.4 Process 3
- Use case DTOs: architecture.md C4.3 `ExecuteFeedingRoundUseCase`
- Endpoint: `POST /enclosures/{enclosure_id}/feeding-rounds` → 200 OK
- BDD scenarios: bdd-scenarios.md Process 2
- ADR-019 (client-supplied current_time), ADR-024 (check ordering), ADR-028 (note format), ADR-029 (non-existent enclosure yields FeedingNotDueError)

---

## Step 5.1 — BDD Feature File ✅

**File:** `features/feeding_round.feature`

```gherkin
Feature: Execute Feeding Round
  As a zookeeper
  I want to execute a feeding round for my assigned enclosure
  So that animals are fed on time

  Scenario: Successfully execute feeding round with animals
    Given enclosure "enc-mammal-1" in zoo "zoo-1" has lion "animal-lion-1"
    And zookeeper "emp-zk-1" is assigned to enclosure "enc-mammal-1"
    And a feeding schedule exists for "enc-mammal-1" at "09:00:00" with diet "meat"
    When zookeeper "emp-zk-1" executes feeding round for "enc-mammal-1" at "09:00:00"
    Then the feeding round succeeds with fed_count 1
    And the note contains "Fed 1 animals (diets: carnivore)"

  Scenario: Feeding round for empty enclosure
    Given enclosure "enc-bird-1" in zoo "zoo-1" has no animals
    And zookeeper "emp-zk-1" is assigned to enclosure "enc-bird-1"
    And a feeding schedule exists for "enc-bird-1" at "10:00:00" with diet "fish"
    When zookeeper "emp-zk-1" executes feeding round for "enc-bird-1" at "10:00:00"
    Then the feeding round succeeds with fed_count 0
    And the note is "no animals to feed"

  Scenario: Feeding fails — not due (time mismatch)
    Given a feeding schedule exists for "enc-mammal-1" at "09:00:00"
    When zookeeper "emp-zk-1" attempts feeding for "enc-mammal-1" at "10:00:00"
    Then the feeding fails with FeedingNotDueError

  Scenario: Feeding fails — zookeeper not assigned
    Given enclosure "enc-mammal-1" has zookeeper "emp-zk-other" assigned
    And a feeding schedule exists for "enc-mammal-1" at "09:00:00"
    When zookeeper "emp-zk-1" attempts feeding for "enc-mammal-1" at "09:00:00"
    Then the feeding fails with ZookeeperNotAssignedError
```

---

## Step 5.2 — Unit Tests for ExecuteFeedingRoundUseCase ✅

**File:** `tests/unit/test_execute_feeding_round.py`

**Tests first:**

```
- test_feeding_round_happy_path_with_animals
    Setup: Enclosure with Lion and Elephant. FeedingSchedule at 09:00. Zookeeper assigned.
    Execute: FeedingRoundRequest(enclosure_id, zookeeper_id, current_time=time(9,0))
    Assert: fed_count == 2, note == "Fed 2 animals (diets: carnivore, herbivore)"

- test_feeding_round_empty_enclosure
    Setup: Empty enclosure. Schedule exists. Zookeeper assigned.
    Assert: fed_count == 0, note == "no animals to feed"

- test_feeding_round_polymorphic_diet_types
    Setup: Enclosure with Lion (carnivore) + Penguin (piscivore).
    Assert: note contains both diet types in enclosure animals list order.

- test_feeding_round_raises_feeding_not_due_when_time_mismatch
    Setup: Schedule at 09:00. Request with current_time=10:00.
    Assert: raises FeedingNotDueError.

- test_feeding_round_raises_feeding_not_due_for_nonexistent_enclosure (ADR-029)
    Setup: No schedule for "enc-nonexistent".
    Assert: raises FeedingNotDueError (not EntityNotFoundError).

- test_feeding_round_raises_zookeeper_not_assigned
    Setup: Enclosure with zookeeper "A" assigned. Request from zookeeper "B".
    Assert: raises ZookeeperNotAssignedError.

- test_feeding_round_raises_invalid_employee_role_for_non_zookeeper
    Setup: Pass a Veterinarian id as zookeeper_id.
    Assert: raises InvalidEmployeeRoleError.

- test_feeding_round_raises_entity_not_found_for_missing_employee
    Assert: raises EntityNotFoundError.

- test_feeding_round_uses_client_supplied_time_not_system_time (ADR-019)
    Assert: use case uses req.current_time directly (test with deterministic time).
```

---

## Step 5.3 — Implement ExecuteFeedingRoundUseCase ✅

**File:** `zoo_management/usecases/execute_feeding_round.py`

**Implementation flow (from architecture.md C4.4 Process 3 — check ordering per ADR-024):**

```python
class ExecuteFeedingRoundUseCase:
    def __init__(self, enclosure_repo, employee_repo, schedule_repo):
        ...

    def execute(self, req: FeedingRoundRequest) -> FeedingRoundResponse:
        # 1. schedule_repo.get_by_enclosure_and_time(enclosure_id, current_time)
        #    → None means FeedingNotDueError (also covers non-existent enclosure — ADR-029)
        # 2. enclosure_repo.get_by_id(enclosure_id)
        # 3. Validate: enclosure.assigned_zookeeper_id == zookeeper_id
        #    → ZookeeperNotAssignedError if mismatch
        # 4. employee_repo.get_by_id(zookeeper_id)
        # 5. isinstance(employee, Zookeeper) → InvalidEmployeeRoleError
        # 6. Loop each animal in enclosure.animals:
        #    - Call animal.get_diet_type() polymorphically
        #    - Collect diet_types list
        # 7. Build note:
        #    - Empty: "no animals to feed" (fed_count=0)
        #    - Non-empty: "Fed {n} animals (diets: {', '.join(diet_types)})" (ADR-028)
        # 8. Return FeedingRoundResponse(enclosure_id, fed_count, note)
```

**Critical constraints:**
- Check ordering: schedule → enclosure → assignment → employee role (ADR-024).
- `current_time` comes from the request, never from `datetime.now()` (ADR-019).
- `note` is always a `str`, never `None` (ADR-028).
- Diet types order matches `enclosure.animals` list order.

**Verification:** `pytest tests/unit/test_execute_feeding_round.py` — all pass. ✅

---

## Step 5.4 — Integration Tests for Feeding Round Router ✅

**File:** `tests/integration/test_feeding_round_router.py`

**Tests first:**

```
- test_feeding_round_returns_200_with_fed_count_and_note
    POST /enclosures/{id}/feeding-rounds with {zookeeper_id, current_time: "09:00:00"}.
    Assert: 200, body has enclosure_id, fed_count, note.

- test_feeding_round_returns_422_for_time_mismatch
    Assert: 422, {"detail": "..."}.

- test_feeding_round_returns_422_for_unassigned_zookeeper
    Assert: 422.

- test_feeding_round_returns_422_for_nonexistent_enclosure (ADR-029)
    Assert: 422 (FeedingNotDueError, not 404).

- test_feeding_round_returns_422_for_non_zookeeper_role
    Assert: 422.
```

---

## Step 5.5 — Implement Router Endpoint ✅

**File:** `zoo_management/adapters/web/routers.py`

```python
@router.post("/enclosures/{enclosure_id}/feeding-rounds", status_code=200)
def execute_feeding_round(
    enclosure_id: str,
    body: FeedingRoundRequestSchema,
    use_case: ExecuteFeedingRoundUseCase = Depends(get_execute_feeding_round_use_case),
) -> FeedingRoundResponseSchema:
    ...
```

**Pydantic schemas:**
```python
class FeedingRoundRequestSchema(BaseModel):
    zookeeper_id: str
    current_time: time

    model_config = ConfigDict(
        json_schema_extra={"example": {
            "enclosure_id": "enc-mammal-1",
            "zookeeper_id": "emp-zk-1",
            "current_time": "09:00:00"
        }}
    )

class FeedingRoundResponseSchema(BaseModel):
    enclosure_id: str
    fed_count: int
    note: str
```

**Add exception handlers:**
- `FeedingNotDueError → 422`
- `ZookeeperNotAssignedError → 422`

---

## Step 5.6 — BDD Step Definitions ✅

**File:** `tests/step_defs/test_feeding_round_steps.py`

---

## Step 5.7 — Lint, Type Check, and Commit ✅

```bash
git add . && git commit -m "feat: execute feeding round — polymorphic diet dispatch, schedule matching, tests, BDD"
```

---

## Phase 5 Completion Checklist

- [x] `FeedingRoundRequest` and `FeedingRoundResponse` DTOs
- [x] `ExecuteFeedingRoundUseCase.execute()` with correct check ordering (ADR-024)
- [x] Client-supplied `current_time` (ADR-019)
- [x] Polymorphic `get_diet_type()` dispatch in diet collection
- [x] Note format: `"Fed N animals (diets: ...)"` or `"no animals to feed"` (ADR-028)
- [x] Non-existent enclosure yields `FeedingNotDueError` not 404 (ADR-029)
- [x] Router `POST /enclosures/{id}/feeding-rounds` → 200
- [x] `json_schema_extra` on request schema (M-5, ADR-023)
- [x] ~9 unit tests pass
- [x] ~5 integration tests pass
- [x] 4 BDD scenarios pass
- [x] ruff and mypy clean (Phase 5 files)

---

**Previous phase:** [Phase 4 — Animal Admission](phase-4-feature-animal-admission.md)
**Next phase:** [Phase 6 — Feature 4: Conduct Health Check](phase-6-feature-health-check.md)
