# Phase 7 — Feature 5: Conduct Guided Tour

**Goal:** Implement the guided tour process — guide availability check, zoo route traversal, tour creation with synchronous timestamps, and guide availability toggle.

**Depends on:** Phase 1–2 (domain + adapter).
**Unlocks:** Independent.

**Architecture references:**
- Process sequence: architecture.md C4.4 Process 5
- Use case DTOs: architecture.md C4.3 `ConductGuidedTourUseCase`
- Endpoint: `POST /tours` → 201 Created
- BDD scenarios: bdd-scenarios.md Process 5
- ADR-003 (Guide.is_available), ADR-011 (start_time == end_time == now()), ADR-026 (GuideNotInZooError), ADR-030 (end_time in response)

---

## Step 7.1 — BDD Feature File ✅

**File:** `features/guided_tour.feature`

```gherkin
Feature: Conduct Guided Tour
  As a guide
  I want to conduct a guided tour through the zoo's enclosures
  So that visitors see all animals

  Scenario: Guide successfully conducts tour through all enclosures
    Given a guide "emp-guide-1" is available in zoo "zoo-1"
    And zoo "zoo-1" has tour route ["enc-mammal-1", "enc-bird-1", "enc-reptile-1"]
    And all enclosures in the route exist
    When guide "emp-guide-1" conducts a tour of zoo "zoo-1"
    Then a tour record is created with the full route
    And the guide "emp-guide-1" is no longer available

  Scenario: Tour fails — guide not available
    Given a guide "emp-guide-busy" exists in zoo "zoo-1" but is not available
    When guide "emp-guide-busy" attempts to conduct a tour of zoo "zoo-1"
    Then the tour fails with NoGuideAvailableError

  Scenario: Tour fails — guide not in zoo (ADR-026)
    Given a guide "emp-guide-other" exists in zoo "zoo-other"
    When guide "emp-guide-other" attempts to conduct a tour of zoo "zoo-1"
    Then the tour fails with GuideNotInZooError

  Scenario: Tour fails — employee is not a guide
    Given a zookeeper "emp-zk-1" exists in zoo "zoo-1"
    When zookeeper "emp-zk-1" attempts to conduct a tour of zoo "zoo-1"
    Then the tour fails with InvalidEmployeeRoleError
```

---

## Step 7.2 — Unit Tests for ConductGuidedTourUseCase ✅

**File:** `tests/unit/test_conduct_guided_tour.py`

**Tests first (fresh InMemoryRepositories per test — ADR-003 test isolation):**

```
- test_guided_tour_happy_path
    Setup: Guide(is_available=True), Zoo(tour_route=["enc-1","enc-2"]),
           two Enclosures in repo.
    Execute: GuidedTourRequest(guide_id, zoo_id)
    Assert: response has tour_id, route == ["enc-1","enc-2"], start_time, end_time.
            Tour saved. Guide.is_available now False in repo.

- test_guided_tour_start_time_equals_end_time (ADR-011)
    Assert: response.start_time == response.end_time.

- test_guided_tour_guide_becomes_unavailable_after_tour (ADR-003)
    Assert: After execute, employee_repo.get_by_id(guide_id).is_available is False.

- test_guided_tour_raises_no_guide_available_when_not_available (ADR-003)
    Setup: Guide(is_available=False).
    Assert: raises NoGuideAvailableError.

- test_guided_tour_raises_guide_not_in_zoo_when_zoo_mismatch (ADR-026)
    Setup: Guide(zoo_id="zoo-other"). Request zoo_id="zoo-1".
    Assert: raises GuideNotInZooError.

- test_guided_tour_raises_invalid_employee_role_for_non_guide
    Setup: Pass a Zookeeper id as guide_id.
    Assert: raises InvalidEmployeeRoleError.

- test_guided_tour_raises_entity_not_found_for_missing_guide
    Assert: raises EntityNotFoundError.

- test_guided_tour_raises_entity_not_found_for_missing_zoo
    Assert: raises EntityNotFoundError.

- test_guided_tour_raises_entity_not_found_for_missing_enclosure_in_route
    Setup: Zoo tour_route contains "enc-nonexistent".
    Assert: raises EntityNotFoundError.

- test_guided_tour_bdd_isolation_no_guide_available_uses_fresh_state
    Verify that a test constructing Guide(is_available=False) is independent of
    any other test that may toggle Guide state.
```

---

## Step 7.3 — Implement ConductGuidedTourUseCase ✅

**File:** `zoo_management/usecases/conduct_guided_tour.py`

**Implementation flow (from architecture.md C4.4 Process 5):**

```python
class ConductGuidedTourUseCase:
    def __init__(self, zoo_repo, enclosure_repo, employee_repo, tour_repo):
        ...

    def execute(self, req: GuidedTourRequest) -> GuidedTourResponse:
        # 1. employee_repo.get_by_id(guide_id) — raises EntityNotFoundError
        # 2. isinstance(employee, Guide) — raises InvalidEmployeeRoleError
        # 3. Validate guide.zoo_id == request.zoo_id — raises GuideNotInZooError (ADR-026)
        # 4. Validate guide.is_available == True — raises NoGuideAvailableError (ADR-003)
        # 5. zoo_repo.get_by_id(zoo_id) — raises EntityNotFoundError
        # 6. route = zoo.tour_route
        # 7. For each enclosure_id in route:
        #    enclosure_repo.get_by_id(enclosure_id) — raises EntityNotFoundError
        # 8. now = datetime.now()
        # 9. Create Tour(id=uuid, guide_id, route, start_time=now, end_time=now)
        #    (ADR-011: start_time == end_time == now())
        # 10. guide.is_available = False (ADR-003)
        # 11. employee_repo.save(guide)
        # 12. tour_repo.save(tour)
        # 13. Return GuidedTourResponse(tour_id, route, start_time, end_time)
```

**Key constraints:**
- Check order: guide existence → role check → zoo match → availability → zoo fetch → route traversal.
- `start_time == end_time == datetime.now()` (ADR-011, ADR-030).
- `guide.is_available = False` after tour (ADR-003).
- No reset mechanism — guide stays unavailable until server restart.
- `end_time` included in response (ADR-030).

**Verification:** `pytest tests/unit/test_conduct_guided_tour.py` — all pass.

---

## Step 7.4 — Integration Tests for Guided Tour Router ✅

**File:** `tests/integration/test_guided_tour_router.py`

**Tests first:**

```
- test_guided_tour_returns_201_with_tour_details
    POST /tours with {guide_id, zoo_id}.
    Assert: 201 Created, body has tour_id, route, start_time, end_time.

- test_guided_tour_returns_422_for_unavailable_guide
    Setup: Guide(is_available=False).
    Assert: 422.

- test_guided_tour_returns_422_for_guide_not_in_zoo
    Assert: 422.

- test_guided_tour_returns_422_for_non_guide_role
    Assert: 422.

- test_guided_tour_returns_404_for_missing_guide
    Assert: 404.

- test_consecutive_tours_second_fails_with_same_guide
    First POST succeeds (201). Second POST with same guide fails (422 — NoGuideAvailableError).
```

---

## Step 7.5 — Implement Router Endpoint ✅

**File:** `zoo_management/adapters/web/routers.py`

```python
@router.post("/tours", status_code=201)
def conduct_guided_tour(
    body: GuidedTourRequestSchema,
    use_case: ConductGuidedTourUseCase = Depends(get_conduct_guided_tour_use_case),
) -> GuidedTourResponseSchema:
    ...
```

**Pydantic schemas:**
```python
class GuidedTourRequestSchema(BaseModel):
    guide_id: str
    zoo_id: str

class GuidedTourResponseSchema(BaseModel):
    tour_id: str
    route: list[str]
    start_time: datetime
    end_time: datetime  # ADR-030
```

**Add exception handlers:**
- `NoGuideAvailableError → 422`
- `GuideNotInZooError → 422`

---

## Step 7.6 — BDD Step Definitions ✅

**File:** `tests/step_defs/test_guided_tour_steps.py`

**Critical test isolation (ADR-003):**
- The "no guide available" scenario must construct `Guide(is_available=False)` directly in its `Given` step using a **fresh** `InMemoryRepositories`.
- Must NOT reuse any shared guide instance that another scenario may have toggled.

---

## Step 7.7 — Lint, Type Check, and Commit ✅

```bash
git add . && git commit -m "feat: conduct guided tour — guide availability, route traversal, tests, BDD"
```

---

## Phase 7 Completion Checklist

- [x] `GuidedTourRequest` and `GuidedTourResponse` DTOs
- [x] `ConductGuidedTourUseCase.execute()` with guide availability and zoo checks
- [x] `start_time == end_time == now()` (ADR-011)
- [x] `guide.is_available = False` after tour (ADR-003)
- [x] Guide zoo match check (ADR-026)
- [x] `end_time` in response (ADR-030)
- [x] Router `POST /tours` → 201
- [x] Pydantic request/response schemas
- [x] ~10 unit tests pass
- [x] ~6 integration tests pass
- [x] 4 BDD scenarios pass
- [x] BDD test isolation: fresh state per scenario
- [x] ruff and mypy clean

---

**Previous phase:** [Phase 6 — Health Check](phase-6-feature-health-check.md)
**Next phase:** [Phase 8 — Infrastructure, Seed Data & App Assembly](phase-8-infrastructure-seed-app.md)
