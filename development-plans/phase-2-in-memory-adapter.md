# Phase 2 — In-Memory Adapter & Repository Implementation

**Goal:** Implement `InMemoryRepositories` — the single class that satisfies all 8 repository port contracts using `dict[str, Entity]` storage. This is the production adapter for MVP and the fake used in all test layers.

**Depends on:** Phase 1 (domain entities + interfaces).
**Unlocks:** Phase 3–7 (all features need repositories), Phase 8 (seed data).

---

## ✓ Step 2.1 — Tests for InMemoryRepositories: Zoo Repository

**File:** `tests/unit/test_in_memory_repositories.py`

**Tests first:**
```
- test_seed_zoo_stores_zoo
- test_get_zoo_by_id_returns_stored_zoo
- test_get_zoo_by_id_raises_entity_not_found_for_missing_id
```

**Implementation notes:**
- `InMemoryRepositories` has `_zoos: dict[str, Zoo]` (private).
- `seed_zoo(zoo: Zoo) -> None` is a **non-port** public method (ADR-025) — only called by `seed_data()`.
- `get_by_id(id)` raises `EntityNotFoundError` on miss (ADR-015).

**Done.**

---

## ✓ Step 2.2 — Tests for InMemoryRepositories: Enclosure Repository

**Tests first:**
```
- test_save_enclosure_stores_enclosure
- test_get_enclosure_by_id_returns_stored
- test_get_enclosure_by_id_raises_entity_not_found
- test_get_enclosures_by_zoo_returns_matching
- test_get_enclosures_by_zoo_returns_empty_for_no_match
- test_save_enclosure_overwrites_existing
```

**Implementation notes:**
- `_enclosures: dict[str, Enclosure]`
- `get_by_zoo(zoo_id)` filters by `enclosure.zoo_id == zoo_id`.

**Done.**

---

## ✓ Step 2.3 — Tests for InMemoryRepositories: Animal Repository

**Tests first:**
```
- test_save_animal_stores_animal
- test_get_animal_by_id_returns_stored
- test_get_animal_by_id_raises_entity_not_found
- test_save_animal_overwrites_existing
```

**Implementation notes:**
- `_animals: dict[str, Animal]`

**Done.**

---

## ✓ Step 2.4 — Tests for InMemoryRepositories: Employee Repository

**Tests first:**
```
- test_save_employee_stores_employee
- test_get_employee_by_id_returns_stored
- test_get_employee_by_id_raises_entity_not_found
- test_get_by_zoo_and_type_returns_matching_employees
- test_get_by_zoo_and_type_returns_empty_for_no_match
- test_save_employee_overwrites_existing (important for Guide.is_available updates)
```

**Implementation notes:**
- `_employees: dict[str, Employee]`
- `get_by_zoo_and_type(zoo_id, role)` filters by `emp.zoo_id == zoo_id and emp.role == role`.

**Done.**

---

## ✓ Step 2.5 — Tests for InMemoryRepositories: FeedingSchedule Repository

**Tests first:**
```
- test_save_schedule_stores_schedule
- test_get_by_enclosure_and_time_returns_matching
- test_get_by_enclosure_and_time_returns_none_for_no_match
- test_save_schedule_uses_composite_key (enclosure_id, scheduled_time) — ADR-014
- test_save_schedule_overwrites_on_same_composite_key
```

**Implementation notes:**
- `_schedules: dict[tuple[str, time], FeedingSchedule]` — composite key is `(enclosure_id, scheduled_time)` (ADR-014).
- `get_by_enclosure_and_time` returns `FeedingSchedule | None` — does **not** raise on miss.

**Done.**

---

## ✓ Step 2.6 — Tests for InMemoryRepositories: Record Repositories

**Tests first:**
```
- test_save_admission_record_stores_record
- test_save_health_check_record_stores_record
- test_save_tour_stores_tour
```

**Implementation notes:**
- `_admission_records: dict[str, AdmissionRecord]`
- `_health_records: dict[str, HealthCheckRecord]`
- `_tours: dict[str, Tour]`
- These only need `save()` — no `get_by_id()` on the port contract.

**Done.**

---

## ✓ Step 2.7 — Implement InMemoryRepositories Class

**File:** `zoo_management/adapters/in_memory.py`

**Implementation (from architecture.md C4.2):**

```python
class InMemoryRepositories(
    ZooRepository,
    EnclosureRepository,
    AnimalRepository,
    EmployeeRepository,
    FeedingScheduleRepository,
    AdmissionRecordRepository,
    HealthCheckRecordRepository,
    TourRepository,
):
    def __init__(self) -> None:
        self._zoos: dict[str, Zoo] = {}
        self._enclosures: dict[str, Enclosure] = {}
        self._animals: dict[str, Animal] = {}
        self._employees: dict[str, Employee] = {}
        self._schedules: dict[tuple[str, time], FeedingSchedule] = {}
        self._admission_records: dict[str, AdmissionRecord] = {}
        self._health_records: dict[str, HealthCheckRecord] = {}
        self._tours: dict[str, Tour] = {}

    # Non-port method (ADR-025)
    def seed_zoo(self, zoo: Zoo) -> None: ...

    # ZooRepository
    def get_by_id(self, id: str) -> Zoo: ...  # Note: method name conflict — see below

    # ... all other port methods
```

**Critical design note — method name conflicts:**
Since `InMemoryRepositories` implements all 8 ports and several have `get_by_id`, you need to handle this carefully. The approach is:
- **Each port's `get_by_id` has a different return type.** Since Python doesn't support method overloading by return type, you'll need a single dispatch approach or separate internal methods.
- **Recommended approach:** Implement port-specific methods by internally routing based on the call site. In practice, use cases inject the adapter typed as the port interface, so each call goes to the same `get_by_id` but the use case expects the correct type.
- **Practical solution:** Since each `get_by_id` needs to search a different dict, implement a **type-aware** `get_by_id` that checks all dicts, **OR** use separate named dicts and check each one. The simplest approach: `get_by_id` checks all dicts in a defined order and returns the first match. Alternatively, separate the repos into individual implementations.

**Alternative (simpler, recommended):** Make `InMemoryRepositories` a container that provides each port as an attribute:
```python
# Actually, the architecture says one class implements all ports.
# The method name collision on get_by_id is resolved by:
# - use cases receive the typed port interface
# - the InMemoryRepositories stores items in typed dicts
# - a single get_by_id scans the correct dict based on stored type
```

**Simplest practical approach:** Since the architecture explicitly says one class implements all ports, implement `get_by_id` to search across all entity dicts and return the matching entity. The use case already knows the expected type.

**Verification:** `pytest tests/unit/test_in_memory_repositories.py` — all pass (~20 tests).

**Done.**

---

## ✓ Step 2.8 — Verify Port Contract Compliance

**Tests first** — `tests/unit/test_port_compliance.py`:
```
- test_in_memory_repositories_is_instance_of_zoo_repository
- test_in_memory_repositories_is_instance_of_enclosure_repository
- test_in_memory_repositories_is_instance_of_animal_repository
- test_in_memory_repositories_is_instance_of_employee_repository
- test_in_memory_repositories_is_instance_of_feeding_schedule_repository
- test_in_memory_repositories_is_instance_of_admission_record_repository
- test_in_memory_repositories_is_instance_of_health_check_record_repository
- test_in_memory_repositories_is_instance_of_tour_repository
```

**Verification:** All `isinstance` checks pass — proves the adapter satisfies all ports.

**Done.**

---

## ✓ Step 2.9 — Lint, Type Check, and Commit

**Action:**
1. `ruff check zoo_management/adapters/`
2. `mypy zoo_management/adapters/`
3. Fix any issues.
4. `git add . && git commit -m "feat: in-memory repository adapter implementing all 8 ports"`

**Verification:** Clean lint/mypy. All tests pass.

**Done.**

---

## Phase 2 Completion Checklist

- [x] `InMemoryRepositories` class implemented in `adapters/in_memory.py`
- [x] Implements all 8 port interfaces (`ZooRepository`, `EnclosureRepository`, etc.)
- [x] `seed_zoo()` non-port method for seed data (ADR-025)
- [x] `EntityNotFoundError` raised on all `get_by_id` misses (ADR-015)
- [x] FeedingSchedule uses composite key `(enclosure_id, scheduled_time)` (ADR-014)
- [x] Port compliance tests verify `isinstance` for all 8 ports
- [x] ~28 unit tests pass (35 total: 27 in-memory + 8 port compliance)
- [x] ruff and mypy clean

---

**Previous phase:** [Phase 1 — Domain Layer](phase-1-domain-layer.md)
**Next phase:** [Phase 3 — Feature 1: Assign Zookeeper](phase-3-feature-assign-zookeeper.md)
