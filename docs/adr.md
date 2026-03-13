# Zoo Management System — Architecture Decision Records (ADRs)

**Source:** Senior engineer reviews of `architecture.md` against `PRD.md`; fifth review addressed 2026-03-10  
**Applied skills:** `architect-python-fastapi` · `fastapi-clean-architecture`  
**Date:** 2026-03-10 (ADR-001–019); ADR-020–024 added 2026-03-10 (third review); ADR-025–028 added 2026-03-10 (fourth review); ADR-029–031 added 2026-03-10 (fifth review)

Each ADR below was raised as a gap, inconsistency, or open question during the senior engineer assessment. All decisions here are **binding for implementation** and supersede any conflicting wording in earlier documents.

---

## ADR-001 — Enclosure owns an `animals` list collection

**Status:** Accepted

### Context

The senior engineer identified that `Enclosure.__init__` only defined `id, name, enclosure_type, zoo_id, assigned_zookeeper_id`. Yet:

- `Enclosure.is_occupied` and `Enclosure.animal_count` are `@property` values that must be backed by something.
- Process 3 (*Execute Feeding Round*) loops over `for each animal in enclosure` (sequence diagram and `business-processes-detailed.md`: *"Enclosure holds list of animals"*).
- Process 1 (*Animal Admission*), step 5: *"Animal is added to the enclosure's list of animals (aggregation: Enclosure ◇── Animal)"*.

No `AnimalRepository.get_by_enclosure()` method was defined, leaving the feeding round use case with no way to retrieve animals.

### Decision

`Enclosure` owns `animals: list[Animal]` as a mutable instance field initialised to `[]` in `__init__`. All use cases that need to iterate, count, or test occupancy access `enclosure.animals` directly on the object returned from `EnclosureRepository.get_by_id()`.

- `is_occupied: bool` → `return bool(self.animals)`
- `animal_count: int` → `return len(self.animals)`
- `AdmitAnimalUseCase` appends the animal to `enclosure.animals` and calls `EnclosureRepository.save(enclosure)`.
- `ExecuteFeedingRoundUseCase` iterates `enclosure.animals` for the polymorphic `get_diet_type()` call.
- **No new repository method** (`get_by_enclosure`) is added. The collection is owned by the aggregate.

### Consequences

- `Enclosure.__init__` signature gains `animals: list[Animal] | None = None` (defaults to `[]`).
- `InMemoryRepositories` stores and returns full `Enclosure` objects with their `animals` list intact (standard in-memory dict; no serialisation).
- `AnimalRepository` port is unchanged.
- C4.1 entity diagram and entity table must show `animals: list` on `Enclosure`.

---

## ADR-002 — `AdmitAnimalRequest` carries the health-check result fields

**Status:** Accepted

### Context

The senior engineer found that `AdmitAnimalRequest` contained only `{animal_id, zoo_id, vet_id}`. The admission sequence diagram showed `alt origin == external → perform health check → save HealthCheckRecord → raises HealthCheckNotClearedError if not cleared`, but there was no mechanism to supply the health-check outcome to the use case:

- `HealthCheckRecordRepository` exposes only `save` (no `get_by_animal`), so the use case cannot look up a prior record.
- `ConductHealthCheckUseCase` is a separate standalone process; having `AdmitAnimalUseCase` call another use case is a code smell in Clean Architecture.

`business-processes-detailed.md` Process 1 step 3: *"Veterinarian examines the animal. Result: Cleared or Not cleared."* This result is produced at admission time by the vet.

### Decision

Add `health_check_result: HealthResult | None` and `health_check_notes: str | None` to `AdmitAnimalRequest`. Make `vet_id: str | None`.

`AdmitAnimalUseCase.execute()` logic:

```
if animal.origin == Origin.EXTERNAL:
    if vet_id is None or health_check_result is None:
        raise InvalidRequestError("vet_id and health_check_result required for external animals")
    vet = employee_repo.get_by_id(vet_id)          # raises EntityNotFoundError if not found
    if not isinstance(vet, Veterinarian):           # ADR-010: role narrowing is use-case responsibility
        raise InvalidEmployeeRoleError(f"Expected Veterinarian, got {vet.role}")
    record = HealthCheckRecord(animal_id, vet_id, result, notes)
    health_repo.save(record)
    if health_check_result != HealthResult.HEALTHY:
        raise HealthCheckNotClearedError(animal_id)
# proceed to select enclosure ...
```

- **`HealthResult.HEALTHY`** is the only result that allows admission to proceed.
- `HealthCheckRecord` is created inline (not via `ConductHealthCheckUseCase`); this is intentional — admission embeds an inline health check, while Process 4 (`ConductHealthCheckUseCase`) covers standalone health checks.

### Consequences

- `AdmitAnimalRequest` gains two new optional fields; breaking change from C4.3 DTO diagram — update required.
- `vet_id: str | None` (previously shown as `str`) — update C4.3 and sequence diagram.
- `HealthCheckRecordRepository` is **unchanged** (only `save` required).
- BDD scenarios for admission must pass `health_check_result` in the `When` step for external-origin animals.

---

## ADR-003 — Guide availability is a stored boolean field on `Guide`

**Status:** Accepted

### Context

`ConductGuidedTourUseCase` must raise `NoGuideAvailableError` if the guide is not available. The `Guide` entity had no field or property representing availability. `PRD §5`: *"'Guide available' is a binary check at tour start; no detailed roster or conflict checking."*

Two design options were considered:

- **Option A:** `is_available: bool` stored on `Guide` (set externally when creating test/seed data).
- **Option B:** Derive availability from open tours — check `TourRepository` for tours where `end_time is None` for the given `guide_id`. This requires a new `get_active_by_guide(guide_id)` method on `TourRepository`.

### Decision

**Option A:** Add `is_available: bool = True` to `Guide.__init__`. The use case checks `if not guide.is_available: raise NoGuideAvailableError(guide_id)`. No changes to `TourRepository`.

Rationale:
- PRD explicitly says "binary check" and "no detailed roster or conflict checking."
- Option B introduces cross-aggregate queries and a new repository method; inconsistent with the MVP simplicity principle.
- `is_available` is set when constructing `Guide` objects (test fakes, seed data). Toggling it post-tour is out of scope for MVP.

### Consequences

- `Guide.__init__` gains `is_available: bool = True`.
- C4.1 entity diagram must add `+is_available: bool` to `Guide`.
- `TourRepository` port is unchanged.
- There is **no** `PATCH /guides/{id}` endpoint to flip `is_available` back to `True`. The flag is one-way for the lifetime of the server process — set to `True` by seed/constructor, set to `False` by `ConductGuidedTourUseCase`. A server restart (which wipes all in-memory state and re-runs `seed_data`) is the only reset mechanism for the MVP. This is an accepted limitation.

**BDD / test isolation (engineer finding C-2 — binding):**

| Test layer | Isolation strategy for `is_available` |
|-----------|---------------------------------------|
| Unit (`tests/unit/`) | Construct a fresh `InMemoryRepositories` instance in each test function. Populate it with only the objects needed for that scenario. Never share a single repo instance across test functions. |
| Integration (`tests/integration/`) | Use `app.dependency_overrides` to inject a fresh `InMemoryRepositories` instance **per test function**. The override must be cleared (`app.dependency_overrides = {}`) in a teardown / `finally` block so it does not leak between tests. Do not rely on seed data being in a known state after another test has mutated it. |
| BDD (`tests/step_defs/`) | The "no guide available" scenario **must** construct a `Guide(is_available=False)` directly in its `Given` step using a fresh `InMemoryRepositories` — it must **not** reuse the shared seed guide `emp-guide-1` from the happy-path scenario. The shared seed data is only a starting point; BDD step definitions must create/override any state that the scenario explicitly calls for. |

These rules are **mandatory** — violating them causes inter-test order dependence and false failures.

---

## ADR-004 — `AdmissionRecord.zookeeper_id` is nullable and sourced from the chosen enclosure

**Status:** Accepted

### Context

`AdmissionRecord` required a `zookeeper_id` field (entity table and ER diagram both showed it as non-nullable). `AdmitAnimalRequest` carried no `zookeeper_id`, and the Process 2 sequence diagram never fetched or assigned one before saving `AdmissionRecord`.

`business-processes-detailed.md` Process 1 step 6: *"Assign zookeeper to enclosure (if not already assigned)"* — the zookeeper may or may not be present on the enclosure at admission time.

### Decision

- `AdmissionRecord.zookeeper_id` is **nullable** (`str | None`).
- `AdmitAnimalUseCase` reads `enclosure.assigned_zookeeper_id` after selecting the target enclosure and passes it to `AdmissionRecord(zookeeper_id=enclosure.assigned_zookeeper_id)`.
- If the enclosure has no assigned zookeeper at admission time, `zookeeper_id` is `None` in the record (valid state; the zookeeper can be assigned via Process 4 afterwards).
- The admission sequence diagram must show this explicit read step.

### Consequences

- `AdmissionRecord.__init__` signature: `zookeeper_id: str | None`.
- C4.1 entity table and ER diagram: `zookeeper_id` marked nullable (`FK, nullable`).
- C4.4 Process 2 sequence diagram updated to show the `zookeeper_id` sourcing step.
- BDD scenarios: an `AdmissionRecord` created before `AssignZookeeperUseCase` runs will have `zookeeper_id=None`.

---

## ADR-005 — Integration tests use `httpx.Client` (sync), not `httpx.AsyncClient`

**Status:** Accepted

### Context

`architecture.md` C4.5 specified `httpx.AsyncClient` with `ASGITransport`. However, `PRD §7.3` mandates *"Sync throughout: No async/await required — route handlers, use cases, and repositories are plain synchronous functions."*

Using `httpx.AsyncClient` requires `async def test_...` functions and `pytest-asyncio` (or `anyio`) as an additional dependency, directly contradicting the "no async" decision.

### Decision

Replace `httpx.AsyncClient` with **`httpx.Client`** (synchronous) combined with `ASGITransport(app)` for all integration tests. `TestClient` from `starlette.testclient` is an equally valid alternative (it wraps `requests` and handles ASGI). Both are sync and require no event loop.

```python
# integration test pattern
from httpx import Client
from httpx._transports.asgi import ASGITransport

def test_assign_zookeeper(app):
    with Client(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = client.post("/enclosures/enc-1/zookeeper", json={...})
    assert response.status_code == 200
```

`pytest-asyncio` / `anyio` are **not** added to `requirements-dev.txt`.

### Consequences

- All integration test modules use `def test_...` (not `async def`).
- `requirements-dev.txt`: `httpx` stays; `pytest-asyncio` is not added.
- C4.5 testing diagram and text updated to reflect sync client.

---

## ADR-006 — `Zoo` entity owns no `employee_count` / `enclosure_count` properties

**Status:** Accepted

### Context

`Zoo.__init__` stores only `id, name, tour_route: list[str]`. Yet C4.1 showed `Zoo` having `employee_count: int` and `enclosure_count: int` as `@property`. With no list of employees or enclosures stored on `Zoo`, these properties have no backing data source.

Two options:
- **Option A:** Add `_employees: list` and `_enclosures: list` to `Zoo` — creates dual state (both `Zoo` and the repositories hold the same objects).
- **Option B:** Remove these properties from `Zoo`; provide counts through repository queries when needed.

### Decision

**Option B:** Remove `employee_count` and `enclosure_count` from `Zoo`. The `Zoo` entity is a simple aggregate: `id, name, tour_route`.

The `@property` OOP grading requirement is met by the many properties remaining across the domain:

| Entity | Properties |
|--------|-----------|
| `Animal` | `type_name`, `is_placed` |
| `Enclosure` | `is_occupied`, `animal_count` (backed by `animals` list — ADR-001) |
| `Employee` | `role` |
| `FeedingSchedule` | `schedule_info` |
| `Tour` | `is_completed` |
| All concrete animals | `get_diet_type()` (polymorphic) |

Removing two properties from `Zoo` does not reduce OOP scoring; the domain retains 8+ explicit `@property` usages.

### Consequences

- `Zoo.__init__` is unchanged; two `@property` definitions removed.
- C4.1 entity diagram: `Zoo` class no longer shows `employee_count()` or `enclosure_count()`.
- PRD §8.4 entity table and §8.7 UML diagram note: these properties are superseded by this ADR.
- Any test or code that referenced `zoo.employee_count` must use `len(employee_repo.get_by_zoo_and_type(zoo_id, ...))` instead.

---

## ADR-007 — No `FeedingRecord` entity for MVP; feeding round result is response-only

**Status:** Accepted

### Context

`business-processes-detailed.md` Process 2 postconditions say *"Feeding for the selected enclosure at this time is **recorded** as executed."* This suggests a persistent audit trail. However:

- PRD §9.4 (Data and audit — resolved) explicitly names only three required audit entities: `AdmissionRecord`, `HealthCheckRecord`, `Tour`. `FeedingRecord` is not listed.
- The `FeedingRoundResponse` already returns `{enclosure_id, fed_count, note}`, capturing the outcome in the HTTP response.

### Decision

No `FeedingRecord` entity or `FeedingRecordRepository` port is created for MVP. The feeding round result is **response-only** (returned as `FeedingRoundResponse`; not persisted).

The word "recorded" in `business-processes-detailed.md` is interpreted as "the HTTP response records the result for the caller" rather than "persisted to storage."

**Deferred:** A `FeedingRecord` entity with a `save` repository can be added in a future iteration if audit of feeding rounds is required (e.g. regulatory compliance, feeding history per animal).

### Consequences

- No new domain entity, port, or adapter is needed for the feeding round.
- `ExecuteFeedingRoundUseCase` does not call any record-saving repository.
- BDD scenario postcondition: assert HTTP response body `{fed_count, note}`; not a DB/store state check.
- `business-processes-detailed.md` wording is acknowledged as aspirational; PRD §9.4 is the binding source.

---

## ADR-008 — `AssignZookeeperUseCase` does not validate zoo existence in the store

**Status:** Accepted

### Context

`AssignZookeeperUseCase` validates correctness by comparing `enclosure.zoo_id == request.zoo_id` and `zookeeper.zoo_id == request.zoo_id`. It never calls `ZooRepository.get_by_id(zoo_id)` to confirm the zoo itself exists. A caller could pass any string as `zoo_id`.

### Decision

**Accepted as-is for MVP.** The cross-field equality check (`enclosure.zoo_id == zookeeper.zoo_id == request.zoo_id`) is sufficient to detect the key failure mode (assigning staff across zoo boundaries). Loading the `Zoo` entity just for existence verification would add `ZooRepository` as a dependency to `AssignZookeeperUseCase` with no functional gain given in-memory state is always consistent.

If a future SQL adapter is introduced with foreign-key constraints, the DB itself will enforce referential integrity on `zoo_id`.

### Consequences

- `AssignZookeeperUseCase` depends on `EnclosureRepository` and `EmployeeRepository` only (unchanged).
- No `ZooRepository` injection into this use case.
- A `zoo_id` that doesn't correspond to a real `Zoo` object will not raise an explicit error in MVP — this is a known and accepted limitation.

---

## ADR-009 — Seed data via `infrastructure/seed.py` standalone function

**Status:** Accepted

### Context

The system has zero GET endpoints (see ADR-021 for the later decision to add minimal reads). At startup the in-memory store is empty. A grader calling any POST endpoint immediately after `uvicorn main:app` would receive `EntityNotFoundError` for every ID.

Seed data must be loaded once at startup. Two placement options existed:

- **Option A:** `InMemoryRepositories.seed()` — a method on the adapter class.
- **Option B:** A standalone `seed_data(repo)` function in `infrastructure/seed.py`, called from `main.py`.

### Decision

**Option B.** Seed logic lives exclusively in `infrastructure/seed.py` as a standalone function `seed_data(repo: InMemoryRepositories) -> None`. `main.py` calls it once before the ASGI app begins serving requests.

`InMemoryRepositories` has **no** `seed()` method. The repository adapter's responsibility is pure data access; seeding is an infrastructure concern.

All entity IDs in seed data are hard-coded stable strings (e.g. `"zoo-1"`, `"enc-mammal-1"`, `"emp-vet-1"`) and documented in `architecture.md` C3 so graders can construct valid request bodies without any prior GET call.

### Consequences

- `infrastructure/seed.py` is created with a single public function `seed_data(repo: InMemoryRepositories) -> None`.
- `main.py` imports `seed_data` and calls it at startup.
- `InMemoryRepositories` remains a pure data-access class (SRP preserved). No `seed()` method exists on it.
- Stable IDs are listed in the C3 seed table in `architecture.md`.

---

## ADR-010 — Employee role validated via `isinstance` in each use case; not delegated to the repository

**Status:** Accepted

### Context

Multiple use cases receive an employee ID (`vet_id`, `zookeeper_id`, `guide_id`) and must ensure the fetched employee is the correct subtype. Two designs were considered:

- **Option A:** Typed repository methods — `get_vet_by_id()`, `get_zookeeper_by_id()`, `get_guide_by_id()` — each raises `InvalidEmployeeRoleError` on type mismatch.
- **Option B:** `EmployeeRepository.get_by_id()` returns the broadest type (`Employee`); each use case narrows via `isinstance` immediately after the call.

PRD §4: *"Each use case enforces its own actor preconditions."* The rule that *"a health check requires a Veterinarian"* is a business rule, not a data-access concern.

### Decision

**Option B.** `EmployeeRepository` exposes a single `get_by_id(id: str) -> Employee`. Each use case asserts the correct subtype immediately after fetching:

```python
employee = employee_repo.get_by_id(employee_id)
if not isinstance(employee, ExpectedType):
    raise InvalidEmployeeRoleError(f"Expected ExpectedType, got {employee.role}")
```

The check is **not** delegated to the repository.

Rationale:

- **Port SRP:** `EmployeeRepository`'s job is data retrieval, not role enforcement.
- **Business logic in use cases:** The requirement *"only a Veterinarian may conduct a health check"* belongs in `ConductHealthCheckUseCase`, not in a shared repository method.
- **Simpler port interface:** One `get_by_id` method instead of three typed variants.
- **Consistency:** All five use cases that receive an employee ID apply the identical `isinstance` pattern.

### Consequences

- `EmployeeRepository` port: `get_by_id(id: str) -> Employee` (single method; unchanged).
- `AdmitAnimalUseCase`, `AssignZookeeperUseCase`, `ExecuteFeedingRoundUseCase`, `ConductHealthCheckUseCase`, `ConductGuidedTourUseCase` each assert `isinstance` immediately after `get_by_id` for every employee ID in their request DTO.
- `InvalidEmployeeRoleError` maps to HTTP 422 (already registered in `exception_handlers.py`).
- No new repository methods or domain exceptions are required.

---

## ADR-011 — `Tour` creation semantics: synchronous MVP, `start_time == end_time == now()`

**Status:** Accepted

### Context

Engineer finding C-3: The Process 5 sequence diagram contains:

```
UC->>UC: create Tour(guide_id, route, start_time=now, end_time=now)
```

If `end_time` is always set at creation time, `Tour.is_completed` (defined as `return self.end_time is not None`) is `True` immediately upon construction — making the property functionally meaningless. The engineer asked whether:

- Option A: `end_time` should be `None` at creation and set after the tour loop (but the loop is synchronous so the gap is microseconds).
- Option B: The architecture intentionally sets `end_time = now()` at creation, meaning the tour is immediately completed in a single synchronous request.

### Decision

**Option B — intentional.** The `ConductGuidedTourUseCase` executes the entire tour in a single synchronous HTTP request. All enclosures in the route are visited (fetched from the repo) within the same request. Creating the `Tour` with `start_time=now()` and `end_time=now()` reflects the real-world simplification: for MVP, a tour begins and ends in one request — there is no asynchronous "tour in progress" state machine.

`Tour.is_completed` is defined as `return self.end_time is not None`. Since `end_time` is always set at construction time for MVP, `is_completed` is always `True` for any persisted `Tour`. This is correct and expected. The property exists to:

1. Express the domain concept clearly (a completed tour has an end time).
2. Preserve the OOP `@property` requirement for grading.
3. Leave a clean extension point — a future async implementation could set `end_time=None` at creation and update it when the tour physically concludes.

**Implementers must not add a `TourStatus.IN_PROGRESS` state, a `PATCH /tours/{id}` endpoint, or any "pending tour" logic for MVP.**

### Consequences

- `Tour.__init__` takes `start_time: datetime` and `end_time: datetime` (both required, both set to `datetime.now()` by the use case).
- `Tour.is_completed: bool` → `return self.end_time is not None` — always `True` for MVP; the property is retained for semantic clarity and future use.
- C4.4 Process 5 sequence diagram gains an explicit note: `start_time == end_time == now() — synchronous MVP (see ADR-011)`.
- No `end_time: datetime | None` optional; no `TourStatus` enum; no tour update endpoint.

---

## ADR-012 — `AdmitAnimalUseCase` enclosure selection: first match in list order

**Status:** Accepted

### Context

Engineer finding G-1: `AdmitAnimalUseCase` calls `enclosure_repo.get_by_zoo(zoo_id)` and filters by `enclosure_type == animal.type_name`. If the zoo has more than one enclosure of the matching type, the architecture was silent on which one to pick. Leaving this unspecified makes BDD tests order-dependent and fragile.

### Decision

The use case selects the **first enclosure in list order** whose `enclosure_type` matches `animal.type_name`. Formally:

```python
matching = [e for e in enclosures if e.enclosure_type.value == animal.taxonomic_type]
if not matching:
    raise NoSuitableEnclosureError(animal.taxonomic_type)
enclosure = matching[0]   # first match in list order — deterministic
```

`animal.taxonomic_type` returns the mid-tier ABC name (`"Mammal"`, `"Bird"`, `"Reptile"`) — see ADR-020 for the full resolution of how this compares against `EnclosureType` values.

`enclosure_repo.get_by_zoo(zoo_id)` returns enclosures in insertion order (dict-based in-memory store). Since seed data has exactly one enclosure per type, the list will typically have one match; the rule kicks in only when multiple exist.

### Consequences

- Use case implementation must use `matching[0]` (or equivalent first-element extraction).
- `InMemoryRepositories.get_by_zoo` must return enclosures in insertion/seed order (standard dict iteration — Python 3.7+).
- BDD and unit tests that assert which enclosure an animal lands in must seed enclosures in known order and rely on "first match."
- No new repository method is needed.

---

## ADR-013 — `AdmitAnimalUseCase` raises `AnimalAlreadyPlacedError` if animal is already placed

**Status:** Accepted

### Context

Engineer finding G-2: Seed data has `animal-lion-1` already placed in `enc-mammal-1`. If `POST /animals/animal-lion-1/admit` is called again, the use case would:

1. Find a matching mammal enclosure (possibly the same one).
2. `enclosure.animals.append(animal)` — creating a duplicate entry.
3. Save a second `AdmissionRecord`.

No check existed for `animal.enclosure_id is not None`. The engineer asked: is re-admission "move" semantics (intentional) or a bug?

### Decision

Re-admission is **not supported for MVP**. If `animal.is_placed` is `True` (i.e., `animal.enclosure_id is not None`), `AdmitAnimalUseCase` raises `AnimalAlreadyPlacedError` immediately after fetching the animal, before any enclosure logic runs.

"Move" semantics (removing from current enclosure, placing in new one) is deferred — it requires fetching the current enclosure, removing the animal from its `animals` list, saving both enclosures, and is out of scope.

**`AnimalAlreadyPlacedError` maps to HTTP 422** (same bucket as other domain precondition violations).

### Consequences

- New domain exception: `AnimalAlreadyPlacedError` added to `domain/exceptions.py`.
- `exception_handlers.py` registers `AnimalAlreadyPlacedError → 422`.
- `AdmitAnimalUseCase` guard (immediately after `animal_repo.get_by_id`):

```python
if animal.is_placed:
    raise AnimalAlreadyPlacedError(animal_id)
```

- C3 exception table gains `AnimalAlreadyPlacedError → 422`.
- C4.3 `AdmitAnimalUseCase` domain exceptions table gains `AnimalAlreadyPlacedError`.
- C4.4 Process 2 sequence diagram gains an early guard step.
- BDD "re-admit already placed animal" scenario asserts HTTP 422.

---

## ADR-014 — `FeedingScheduleRepository` uniqueness: one schedule per enclosure per time slot

**Status:** Accepted

### Context

Engineer finding G-3: `FeedingScheduleRepository.get_by_enclosure_and_time` returns `FeedingSchedule | None`, implying at most one schedule per `(enclosure_id, scheduled_time)` pair. But nothing prevented saving two `FeedingSchedule` objects with the same enclosure and time. If that happened and the in-memory impl returned only the first, behaviour would be silently wrong.

### Decision

**Uniqueness invariant:** At most one `FeedingSchedule` may exist per `(enclosure_id, scheduled_time)` pair. This invariant is:

1. **Stated in the port contract** — `get_by_enclosure_and_time` is defined under the assumption of uniqueness. If the store ever contained duplicates, the method's behaviour is undefined.
2. **Enforced in the in-memory adapter** — `InMemoryRepositories.save(schedule: FeedingSchedule)` upserts by `(enclosure_id, scheduled_time)` key rather than by `schedule.id` alone. Any save for an existing `(enclosure_id, scheduled_time)` replaces the prior entry.

No new domain validation method is required; the enforcement lives at the adapter boundary.

### Consequences

- `domain/interfaces.py` port docstring for `get_by_enclosure_and_time` gains: *"Pre-condition: at most one schedule exists per (enclosure_id, scheduled_time) pair. Caller must not save duplicates."*
- `adapters/in_memory.py` `FeedingScheduleRepository.save` uses a composite key `(schedule.enclosure_id, schedule.scheduled_time)` as the dict key so duplicate-time saves overwrite silently.
- Seed data and BDD fixtures must not create two schedules for the same enclosure and time.
- No new repository method is added.

---

## ADR-015 — `ZooRepository.get_by_id` raises `EntityNotFoundError` on miss

**Status:** Accepted

### Context

Engineer finding M-1: All other `get_by_id` repository methods implicitly raise `EntityNotFoundError` when the entity is not in the store (consistent with the C3 exception table: `EntityNotFoundError → 404`). `ZooRepository` was the only port whose contract did not state this explicitly.

### Decision

`ZooRepository.get_by_id(id: str) -> Zoo` raises `EntityNotFoundError` if no `Zoo` with that `id` exists in the store. This is the same contract as every other `get_by_id` port method. The behaviour is **not** `return None`.

### Consequences

- `domain/interfaces.py` `ZooRepository.get_by_id` docstring gains: *"Raises EntityNotFoundError if not found."*
- `InMemoryRepositories` implementation raises `EntityNotFoundError` on a cache miss for `get_by_id`.
- No new domain exception or HTTP handler is required (the mapping already exists in C3).

---

## ADR-016 — `zoo_id` in `AssignZookeeperRequest` body is intentional

**Status:** Accepted

### Context

Engineer finding M-2: The HTTP endpoint is `POST /enclosures/{enclosure_id}/zookeeper`. The enclosure already carries `zoo_id` internally — the use case could read `enclosure.zoo_id` after fetching. Requiring the client to also supply `zoo_id` in the request body appears redundant and opens a surface for mismatch (`client.zoo_id != enclosure.zoo_id → EnclosureNotInZooError`).

### Decision

`zoo_id` in `AssignZookeeperRequest` is **intentional as an explicit contract**.

Rationale:

- The validation `enclosure.zoo_id == request.zoo_id == zookeeper.zoo_id` is the **core domain rule**: all three entities must belong to the same zoo. Requiring the client to assert the zoo context makes the domain invariant visible at the API surface and catches misconfigured callers early.
- Removing `zoo_id` from the request would require the use case to infer zoo membership from the enclosure alone, silently bypassing the explicit three-way check — weakening the invariant.
- For MVP this is not a security concern; it is an intentional strictness choice.

The `EnclosureNotInZooError` raised when `request.zoo_id` does not match `enclosure.zoo_id` is therefore a correct, expected validation response (HTTP 422), not a spurious error.

### Consequences

- `AssignZookeeperRequest` retains `zoo_id: str`.
- API documentation (C4.3) gains a note: *"zoo_id is required in the request body and must match the enclosure's zoo_id and the zookeeper's zoo_id — this is the three-way zoo-boundary check (ADR-016)."*
- No change to the use case logic.

---

## ADR-017 — Seed logic lives in `seed_data(repo)` standalone function, not `InMemoryRepositories.seed()`

**Status:** Accepted

### Context

Engineer finding M-3: Two incompatible designs existed in the docs:

- `architecture.md` C4.2 class diagram showed `InMemoryRepositories +seed(data: SeedData) None` — a method on the adapter.
- `architecture.md` C3 and C4.2 narrative described `seed_data(repo: InMemoryRepositories)` in `infrastructure/seed.py` — a standalone function.

These are different interfaces. Having `InMemoryRepositories.seed()` couples the repository to seed data logic, violating Single Responsibility Principle.

### Decision

**Standalone function wins.** The canonical design is:

```python
# infrastructure/seed.py
def seed_data(repo: InMemoryRepositories) -> None:
    ...  # construct and save all seed entities

# main.py
from infrastructure.seed import seed_data
...
seed_data(repo)
```

`InMemoryRepositories` has no `seed()` method. The C4.2 class diagram entry is incorrect and must be removed.

### Consequences

- C4.2 `InMemoryRepositories` class removes `+seed(data: SeedData) None`.
- `infrastructure/seed.py` is the single canonical location for all seed logic.
- `main.py` imports and calls `seed_data(repo)` once at startup.
- `InMemoryRepositories` remains a pure data-access class; no knowledge of seed data.

---

## ADR-018 — `ANIMAL.species` in ER diagram is removed; `type_name` is a `@property`, not a stored column

**Status:** Accepted

### Context

Engineer finding M-4: The C4.6 ER diagram showed:

```
ANIMAL {
    string id PK
    string name
    string species
    string animal_type
    ...
}
```

The `domain/entities.py` `Animal` class has no `species` field in `__init__`. `type_name` is a `@property` returning `type(self).__name__` (e.g. `"Lion"`, `"Penguin"`). For the in-memory adapter this is harmless, but the ER diagram is intended to guide a future SQL adapter implementer — showing `species` there would cause them to add a spurious column.

### Decision

**Remove `species` from the ER diagram.** The ER diagram reflects the logical data model that a future adapter must persist. Since `type_name` is derived at runtime from the Python class name (not stored), it maps to `animal_type` (the discriminator / concrete class identifier) in the ER, which already exists. No separate `species` column is needed.

A future SQL adapter must store `animal_type` as a discriminator column (e.g. SQLAlchemy `polymorphic_on`) to reconstruct the correct subclass on load. This is noted in the ER diagram.

### Consequences

- C4.6 ER diagram `ANIMAL` entity: `string species` row removed.
- `animal_type` remains as the discriminator — future SQL adapter uses it for polymorphic loading.
- No change to domain entities.

---

## ADR-019 — `current_time` in `FeedingRoundRequest` is supplied by the client intentionally

**Status:** Accepted

### Context

Engineer finding M-5: `FeedingRoundRequest` carries `current_time: time` in the request body, meaning the **client** decides what "now" is. An implementer reading this without context might treat it as a bug and replace it with `datetime.now().time()` inside the use case — which would silently break every BDD scenario that passes a fixed time like `09:00` to match the seed schedule.

### Decision

`current_time` supplied by the client is **intentional** and is a deliberate testability decision:

1. The feeding schedule comparison is an **exact match** (`current_time == schedule.scheduled_time`). If the use case called `datetime.now()` internally, BDD tests would need to execute within the exact second of the seeded time — impossible to control.
2. Allowing the client to pass `current_time` makes the behaviour deterministic for automated testing at any wall-clock time.
3. This is not a security concern at MVP scope — there is no authentication and no production data.

This pattern is sometimes called "explicit clock injection" and is consistent with the MVP's "testability over realism" principle (same rationale as in-memory state).

### Consequences

- `FeedingRoundRequest.current_time: time` is required in the request body. The use case **must not** call `datetime.now()` internally; it must use `req.current_time`.
- C4.3 DTO description gains: *"current_time: time — supplied by client; intentional testability decision (ADR-019). Use case must not call datetime.now() internally."*
- BDD `When` step for feeding round: `When the zookeeper executes a feeding round at time "09:00"` passes `current_time="09:00"` in the request body.

---

## ADR-020 — `Animal.taxonomic_type` property resolves EnclosureType matching (CRIT-1)

**Status:** Accepted

### Context

ADR-012 specified this enclosure-selection comparison:

```python
matching = [e for e in enclosures if e.enclosure_type.value == animal.type_name]
```

`animal.type_name` is a `@property` returning `type(self).__name__` — `"Lion"` for a Lion, `"Penguin"` for a Penguin (concrete class name). `EnclosureType` is an enum with taxonomic values (`MAMMAL`, `BIRD`, `REPTILE`). Any comparison of `"Mammal"` or `"MAMMAL"` against `"Lion"` is always `False` — **no animal would ever be placed in any enclosure**. This is a blocking correctness bug.

PRD §5: *"suitability = enclosure's type matches the animal's **taxonomic** type (Mammal, Bird, Reptile)"* — the match is at the mid-tier abstract class level, not the concrete class level.

Three options were considered:

- **Option A:** Keep `type_name` as concrete class name; define `EnclosureType` values to match concrete names (`"Lion"`, `"Penguin"` …) — architecturally wrong; requires one `EnclosureType` variant per species.
- **Option B:** Change `type_name` to return the mid-tier ABC name — misleading because `type_name` is used as the concrete discriminator in the ER model (`animal_type` column) and in logging/repr.
- **Option C:** Add a separate `@property taxonomic_type: str` on `Animal` that traverses the MRO to the mid-tier ABC, keeping `type_name` as the concrete class name.

### Decision

**Option C.** `Animal` gains a new read-only property:

```python
@property
def taxonomic_type(self) -> str:
    """Return the mid-tier ABC name: 'Mammal', 'Bird', or 'Reptile'."""
    return type(self).__mro__[1].__name__
```

MRO examples (Python resolves left to right):

| Concrete class | `__mro__[1]` | `taxonomic_type` |
|----------------|--------------|-----------------|
| `Lion` | `Mammal` | `"Mammal"` |
| `Elephant` | `Mammal` | `"Mammal"` |
| `Monkey` | `Mammal` | `"Mammal"` |
| `Eagle` | `Bird` | `"Bird"` |
| `Penguin` | `Bird` | `"Bird"` |
| `Crocodile` | `Reptile` | `"Reptile"` |

`EnclosureType` enum values are title-cased to match exactly:

```python
class EnclosureType(str, Enum):
    MAMMAL  = "Mammal"
    BIRD    = "Bird"
    REPTILE = "Reptile"
```

The corrected ADR-012 comparison becomes:

```python
matching = [e for e in enclosures if e.enclosure_type.value == animal.taxonomic_type]
if not matching:
    raise NoSuitableEnclosureError(animal.taxonomic_type)
enclosure = matching[0]
```

`type_name` continues to return `type(self).__name__` (`"Lion"`, `"Penguin"` …). It is used for logging, `__repr__`, and as the `animal_type` discriminator in the ER model. The two properties serve different purposes and must not be conflated.

### Consequences

- `domain/entities.py` `Animal` gains `taxonomic_type: str` as a new `@property`.
- `domain/entities.py` `EnclosureType` enum: values changed from `"MAMMAL"/"BIRD"/"REPTILE"` to `"Mammal"/"Bird"/"Reptile"`. Enum *member names* (`MAMMAL`, `BIRD`, `REPTILE`) are unchanged — only `.value` changes.
- `AdmitAnimalUseCase` uses `animal.taxonomic_type` (not `animal.type_name`) in the enclosure filter.
- `NoSuitableEnclosureError` message uses `animal.taxonomic_type`.
- C4.1 class diagram: `Animal` gains `+taxonomic_type() str`.
- C4.4 Process 2 sequence diagram note updated from `animal.type_name` to `animal.taxonomic_type`.
- ADR-012 pseudocode superseded above.
- Seed data enclosure construction (e.g. `Enclosure(enclosure_type=EnclosureType.MAMMAL)`) is unchanged in code; only the `.value` string changes.

---

## ADR-021 — Minimal GET endpoints added for grader state verification (DQ-1)

**Status:** Accepted

### Context

The original architecture specified zero GET endpoints. Without any read capability, a grader cannot verify that a `POST /animals/{id}/admit` placed the animal in the correct enclosure, or that `POST /enclosures/{id}/zookeeper` updated the assignment. The grader can only observe HTTP status codes, not resulting state.

### Decision

Add two minimal GET endpoints:

| Endpoint | Response fields |
|----------|----------------|
| `GET /animals/{animal_id}` | `id`, `name`, `type_name`, `taxonomic_type`, `origin`, `enclosure_id` |
| `GET /enclosures/{enclosure_id}` | `id`, `name`, `enclosure_type`, `zoo_id`, `assigned_zookeeper_id`, `animal_count` |

These are implemented as thin router handlers (no dedicated use case): the router calls `animal_repo.get_by_id` / `enclosure_repo.get_by_id` directly, maps the entity to a Pydantic response schema, and returns 200. On miss, `EntityNotFoundError` propagates to 404 via the existing handler.

Rationale:
- The port contracts already support these reads (`get_by_id` exists on both repositories).
- No business logic is introduced; these are pure projections.
- They are the minimum surface needed for a grader to confirm outcomes without reversing any architectural decisions.

### Consequences

- `adapters/web/routers.py` gains two `GET` route handlers.
- New Pydantic response schemas: `AnimalResponse`, `EnclosureResponse`.
- No new use cases, ports, or domain exceptions.
- C3 endpoint table updated with the two GET routes (success status 200).
- `EntityNotFoundError → 404` handler already covers miss cases for both.

---

## ADR-022 — Second guide added to seed data to mitigate one-shot tour risk (DQ-2)

**Status:** Accepted

### Context

`ConductGuidedTourUseCase` sets `guide.is_available = False` after a successful tour. There is no reset endpoint. With only one seeded guide (`emp-guide-1`), the grader can call `POST /tours` exactly once per server session before `NoGuideAvailableError` is permanently returned for that guide. There is no `POST /employees` endpoint to provision a second guide via the API.

### Decision

Add a second guide to seed data: `emp-guide-2` (name=`"Dave"`, `zoo_id="zoo-1"`, `is_available=True`). Both guides start available at every server startup. The grader can call `POST /tours` with `guide_id="emp-guide-1"` and then again with `guide_id="emp-guide-2"` before exhausting the pool.

This does not require any new endpoints, use cases, or domain changes.

### Consequences

- `infrastructure/seed.py` adds `Guide(id="emp-guide-2", name="Dave", zoo_id="zoo-1", is_available=True)` and saves it via `employee_repo.save(guide_2)`.
- `architecture.md` C3 seed data table gains the `emp-guide-2` row.
- No changes to domain entities, use cases, or ports.

---

## ADR-023 — `FeedingRoundRequest.current_time` wire format: `"HH:MM:SS"` (ISO 8601)

**Status:** Accepted

### Context

`FeedingRoundRequest.current_time: time` — Python's `datetime.time` type is serialised/deserialised by Pydantic v2 via `time.fromisoformat()`. On Python 3.12 this accepts both `"HH:MM"` and `"HH:MM:SS"`. The seed feeding schedules use `time(9, 0, 0)` and `time(10, 0, 0)`. The feeding round comparison is an exact-match: `req.current_time == schedule.scheduled_time`. Inconsistent formatting between client input and stored schedule would silently fail the comparison.

### Decision

The canonical wire format for `current_time` is **`"HH:MM:SS"`** (ISO 8601 full time, e.g. `"09:00:00"`, `"10:00:00"`). Pydantic v2 also accepts `"HH:MM"` (e.g. `"09:00"`) on Python 3.12, but this is not canonical and must not be relied upon in BDD scenarios or integration tests.

BDD `When` steps must use the `"HH:MM:SS"` form: `current_time="09:00:00"`.

No custom Pydantic validator is required. The standard `time` type annotation handles parsing; implementers must document the expected format in the OpenAPI schema description.

### Consequences

- `FeedingRoundRequest` schema: add `json_schema_extra={"example": "09:00:00"}` or equivalent field description.
- All BDD `When` steps for feeding rounds use `"09:00:00"` / `"10:00:00"`.
- `docs/bdd-scenarios.md` updated to show full `"HH:MM:SS"` format in time parameters.

---

## ADR-024 — `ExecuteFeedingRoundUseCase` check ordering is intentional: schedule before zookeeper existence (DQ-4)

**Status:** Accepted

### Context

Process 3 checks in this order:

1. `schedule_repo.get_by_enclosure_and_time` → `FeedingNotDueError` if `None`
2. `enclosure_repo.get_by_id` → `Enclosure`
3. `enclosure.assigned_zookeeper_id == zookeeper_id` → `ZookeeperNotAssignedError`
4. `employee_repo.get_by_id(zookeeper_id)` → `Employee`
5. `isinstance(employee, Zookeeper)` → `InvalidEmployeeRoleError`

The engineer noted that a caller with a valid `enclosure_id` but a non-existent `zookeeper_id` receives `ZookeeperNotAssignedError` (step 3), not `EntityNotFoundError` (step 4), because the employee existence check happens after the assignment check.

### Decision

The ordering is **intentional**. Rationale:

1. **Fail fast on the most common rejection:** *"Is feeding due right now?"* rejects the vast majority of spurious calls at minimal cost before loading any employee objects.
2. **Domain semantics:** `ZookeeperNotAssignedError` is the correct domain error when the provided `zookeeper_id` does not match the enclosure's assigned zookeeper — whether that ID does not exist or exists but belongs to a different enclosure is a secondary concern. The fundamental violation is *"this person is not authorised to feed this enclosure."*
3. **Step 4 is a guard against impersonation / data integrity:** The `isinstance(employee, Zookeeper)` check after `get_by_id` is a second layer of defence. It executes only when the ID passes the assignment check (i.e., it matches `enclosure.assigned_zookeeper_id`), so in practice the entity will always exist if the assignment check passes (seed data is consistent).

The known consequence — a caller with a fabricated but non-matching `zookeeper_id` receives `ZookeeperNotAssignedError` rather than `EntityNotFoundError` — is acceptable and by design.

### Consequences

- No change to the Process 3 sequence diagram or use case implementation.
- This ordering is documented and binding; implementers must not reorder the checks.

---

## ADR-025 — `seed_data()` Zoo persistence via non-port `seed_zoo()` method (BLK-1)

**Status:** Accepted

### Context

`ZooRepository.save()` was removed from the port (ADR rationale: no use case mutates a `Zoo` object — `get_by_id` is the only call site). However `seed_data(repo: InMemoryRepositories)` in `infrastructure/seed.py` still needs to persist the initial `Zoo` object at startup. Three options existed:

- **Option A:** Add a non-port public method `seed_zoo(zoo: Zoo) -> None` to `InMemoryRepositories`, callable only from `seed_data`. Not on any `abc.ABC` port.
- **Option B:** Restore `ZooRepository.save()` to the port interface — falsely implies a use case exists that mutates `Zoo`.
- **Option C:** Access `InMemoryRepositories._zoos` dict directly inside `seed_data` — breaches encapsulation; couples infrastructure to private adapter internals.

### Decision

**Option A.** `InMemoryRepositories` exposes one additional public method `seed_zoo(zoo: Zoo) -> None`. Its sole caller is `seed_data(repo: InMemoryRepositories)` in `infrastructure/seed.py`. This method is **not** declared on any `abc.ABC` port interface. No use case depends on it; it does not widen the port surface used by application code.

### Consequences

- `InMemoryRepositories` gains `seed_zoo(zoo: Zoo) -> None` (not on any port ABC).
- `seed_data(repo: InMemoryRepositories)` accepts the concrete adapter class (not a port interface). This is an accepted coupling: `seed_data` is already an infrastructure concern and is the only caller.
- If a SQL adapter is introduced, `seed_data` will need updating to call the SQL equivalent of `seed_zoo`. This is a known and accepted consequence — seed logic is adapter-specific by nature.
- `ZooRepository` port retains only `get_by_id`.
- C4.2 class diagram: `InMemoryRepositories` shows `+seed_zoo(zoo: Zoo) None` as a non-port method.

---

## ADR-026 — `ConductGuidedTourUseCase` validates `guide.zoo_id == request.zoo_id`

**Status:** Accepted

### Context

`AssignZookeeperUseCase` performs a three-way zoo-boundary check (ADR-016): `enclosure.zoo_id == request.zoo_id == zookeeper.zoo_id`. No equivalent check existed in `ConductGuidedTourUseCase` — the guide's `zoo_id` was never compared to `request.zoo_id`. For a single-zoo MVP this is benign, but it creates an architectural inconsistency: all other use cases that receive an employee ID guard zoo membership; `ConductGuidedTourUseCase` would not.

### Decision

After `isinstance(employee, Guide)` validation, `ConductGuidedTourUseCase` validates:

```python
if guide.zoo_id != request.zoo_id:
    raise GuideNotInZooError(guide_id)
```

`GuideNotInZooError` is a new domain exception mapping to HTTP 422 (same bucket as other precondition violations).

### Consequences

- New domain exception: `GuideNotInZooError` added to `domain/exceptions.py`.
- `exception_handlers.py` registers `GuideNotInZooError → 422`.
- C4.3 `ConductGuidedTourUseCase` domain exceptions table gains `GuideNotInZooError`.
- C4.4 Process 5 sequence diagram gains the guard step.
- Single-zoo seed data means this check never fails in practice — it is an architectural consistency guard, not a functionally active rule for MVP.

---

## ADR-027 — `AdmissionRecord.health_check_record_id: str | None`

**Status:** Accepted

### Context

`AdmitAnimalUseCase` creates two records for external-origin animals in the same execution: a `HealthCheckRecord` and an `AdmissionRecord`. No structural link existed between them. A future auditor reconstructing which health check was performed during a specific admission would need a join on `(animal_id, vet_id, date)` — fragile if multiple health checks occur on the same day.

### Decision

`AdmissionRecord` gains `health_check_record_id: str | None`.

- **External origin:** `AdmitAnimalUseCase` sets `health_check_record_id = health_check_record.id` before calling `admission_repo.save(record)`.
- **Internal origin:** `health_check_record_id = None` (no health check performed).

The field follows the same nullable pattern as `vet_id` already on `AdmissionRecord`.

### Consequences

- `AdmissionRecord.__init__` signature gains `health_check_record_id: str | None = None`.
- C4.1 entity table and C4.6 ER diagram: `AdmissionRecord` gains `health_check_record_id FK nullable`.
- No new repository method or port change required.
- BDD scenario for external admission: response `AdmitAnimalResponse` does not expose `health_check_record_id`; it is an internal audit field on the record, not returned in the API response.

---

## ADR-028 — `FeedingRoundResponse.note` is always-present `str`

**Status:** Accepted

### Context

`FeedingRoundResponse.note` was typed as `str | None` (optional) in early drafts. Two scenarios exist:

1. **Empty enclosure:** no animals to feed → response should communicate this clearly.
2. **Animals fed:** polymorphic `get_diet_type()` is called on each animal — the result should be visible in the API output (OOP grading requirement).

Leaving `note` as `Optional[str]` allowed an implementer to set it to `None` on success — discarding the polymorphic dispatch result silently.

### Decision

`note: str` is **always present** (never `None` or absent from the response). Two defined string values:

- **Empty enclosure:** `"no animals to feed"` — `fed_count` is `0`.
- **Success (animals fed):** `"Fed {n} animals (diets: {', '.join(diet_types)})"` — e.g. `"Fed 2 animals (diets: carnivore, piscivore)"`. `diet_types` is built by calling `animal.get_diet_type()` polymorphically on each animal in the enclosure (the primary OOP grading-signal dispatch). Order matches `enclosure.animals` list order.

### Consequences

- `FeedingRoundResponse`: `note: str` (not `Optional[str]`). The Pydantic router schema must not declare it with `Optional` or a default of `None`.
- C4.4 Process 3 sequence diagram response line updated from `{fed_count, note?}` to `{fed_count, note}`.
- BDD scenario postconditions assert the full note string, including diet type list.
- The polymorphic `get_diet_type()` result is included in the HTTP response — it is not discarded — making the OOP dispatch visible at the API boundary.

---

## ADR-029 — Process 3 non-existent `enclosure_id` yields `FeedingNotDueError`, not `EntityNotFoundError`

**Status:** Accepted

### Context

The Process 3 check order (ADR-024) is:

1. `schedule_repo.get_by_enclosure_and_time(enclosure_id, current_time)` → `FeedingNotDueError` if `None`
2. `enclosure_repo.get_by_id(enclosure_id)` → `EntityNotFoundError` if not found
3. Assignment check → `ZookeeperNotAssignedError`
4. Employee fetch → `EntityNotFoundError`
5. `isinstance` check → `InvalidEmployeeRoleError`

`schedule_repo.get_by_enclosure_and_time` returns `None` for any unknown key — including a non-existent `enclosure_id` with no seeded schedule. Therefore a caller that passes a completely invalid `enclosure_id` receives `FeedingNotDueError` (422) instead of `EntityNotFoundError` (404) because the schedule check fires first. This is the same pattern documented in ADR-024 for `zookeeper_id` ordering.

### Decision

**Accepted as-is.** The ordering is intentional and this side-effect is acceptable. Rationale:

- Fail-fast on the most common rejection: *"is feeding due right now?"* should reject spurious calls before loading any enclosure or employee objects.
- For in-memory storage, the performance gain is minimal, but the principle is correct and consistent with ADR-024.
- A caller with a malformed or non-existent `enclosure_id` receives 422 (not 404). This is a known, accepted inconsistency — the domain error *"feeding not due"* is raised before the system confirms the enclosure exists.
- BDD scenarios and integration tests that test invalid `enclosure_id` input should expect HTTP 422 (`FeedingNotDueError`), not 404.

### Consequences

- No change to the use-case implementation or check ordering.
- C4.4 Process 3 sequence diagram gains an explicit note documenting this side-effect.
- Test authors must not assert `EntityNotFoundError` / 404 for a non-existent `enclosure_id` in the feeding round endpoint.

---

## ADR-030 — `GuidedTourResponse` includes `end_time: datetime`

**Status:** Accepted

### Context

`GuidedTourResponse` was defined as `{tour_id, route, start_time}`. Since `start_time == end_time == now()` (ADR-011) and `is_completed` is always `True`, omitting `end_time` from the response meant the client had no API surface to observe the tour completion time. No `GET /tours/{id}` endpoint exists; the only opportunity to surface `end_time` to the caller is in the creation response.

For a grader verifying the tour entity was correctly persisted, the absence of `end_time` in the response reduces verifiability.

### Decision

Add `end_time: datetime` to `GuidedTourResponse`. Its value equals `start_time` (both set to `datetime.now()` by the use case at tour creation — see ADR-011). The response therefore always carries both timestamps with the same value for MVP.

### Consequences

- `GuidedTourResponse` gains `end_time: datetime`.
- C4.3 DTO class diagram updated.
- C4.4 Process 5 sequence diagram response line updated: `201 Created {tour_id, route, start_time, end_time}`.
- BDD and integration tests may assert `end_time == start_time` (or simply that `end_time` is present and non-null).
- No change to domain entities, use case logic, or ports.

---

## ADR-031 — `AssignZookeeperUseCase` idempotent re-assignment to the current zookeeper

**Status:** Accepted

### Context

If `POST /enclosures/{id}/zookeeper` is called with a `zookeeper_id` that is already `enclosure.assigned_zookeeper_id`, the use case:

1. Fetches the enclosure (succeeds).
2. Fetches the employee (succeeds).
3. `isinstance` check passes.
4. Zoo-boundary check passes.
5. `enclosure.assigned_zookeeper_id = zookeeper.id` — overwrites with the same value (no-op state change).
6. `enclosure_repo.save(enclosure)` — persists the unchanged enclosure.
7. Returns `200 OK {enclosure_id, zookeeper_id}`.

No branch in the architecture handled this case explicitly. The question was: should a guard be added to detect same-zookeeper re-assignment and return early or raise an error?

### Decision

**Idempotent — 200 OK, no exception.** Re-assigning the same zookeeper to an enclosure they already own is a valid, harmless, idempotent operation. The overwrite is safe; saving the same value has no side-effects for in-memory storage.

Rationale:
- HTTP semantics: PUT/PATCH-like operations are expected to be idempotent. Raising an error for a no-op assignment would be unexpected and harder to use.
- No new domain exception is needed — there is no business rule that forbids re-assigning the same person.
- Adding a guard (`if enclosure.assigned_zookeeper_id == request.zookeeper_id: return early`) would be a micro-optimisation with no correctness benefit. The current overwrite path is kept as-is.

**Implementers must not add an "already assigned" check or a new exception for this case.**

### Consequences

- No new domain exception, no new HTTP handler registration.
- C4.4 Process 1 sequence diagram gains an explanatory note on the assignment step.
- Integration and BDD tests may call `POST /enclosures/{id}/zookeeper` twice with the same body and assert 200 OK both times.

---

## ADR Cross-reference

| ADR | Resolves engineer issue | Files affected |
|-----|------------------------|----------------|
| ADR-001 | Gap #1 — `Enclosure.animals` / `animal_count` / `is_occupied` | `architecture.md` C4.1 |
| ADR-002 | Gap #2 — health-check cleared logic; Gap #5 — `vet_id` optionality | `architecture.md` C4.3, C4.4 |
| ADR-003 | Gap #3 — `Guide.is_available`; C-2 BDD test isolation | `architecture.md` C4.1, C4.5 |
| ADR-004 | Gap #4 — `AdmissionRecord.zookeeper_id` source and nullability | `architecture.md` C4.1, C4.4 |
| ADR-005 | Inconsistency #6 — sync vs async test client | `architecture.md` C4.5 |
| ADR-006 | Inconsistency #7 — `Zoo` properties without backing data | `architecture.md` C4.1 |
| ADR-007 | Open question #8 — no `FeedingRecord` | `architecture.md` ADR Summary |
| ADR-008 | Open question #9 — no zoo existence validation | `architecture.md` ADR Summary |
| ADR-009 | GAP-1 (third review) — Seed data via standalone `seed_data(repo)` function | `architecture.md` C3, ADR Summary |
| ADR-010 | GAP-1 (third review) — Employee role via `isinstance` in use case, not repository | `architecture.md` C4.3, C4.4 |
| ADR-011 | C-3 — Tour `start_time == end_time == now()` intentional; `is_completed` always `True` | `architecture.md` C4.4 |
| ADR-012 | G-1 — Enclosure selection: first match in list order | `architecture.md` C4.4 |
| ADR-013 | G-2 — Re-admission guard: `AnimalAlreadyPlacedError` → 422 | `architecture.md` C3, C4.3, C4.4 |
| ADR-014 | G-3 — `FeedingSchedule` uniqueness invariant at port + adapter | `architecture.md` C4.2 |
| ADR-015 | M-1 — `ZooRepository.get_by_id` raises on miss | `architecture.md` C4.2 |
| ADR-016 | M-2 — `zoo_id` in request body is intentional three-way check | `architecture.md` C4.3 |
| ADR-017 | M-3 — `seed_data(repo)` standalone function; no `InMemoryRepositories.seed()` | `architecture.md` C4.2 |
| ADR-018 | M-4 — `ANIMAL.species` removed from ER; `animal_type` is the discriminator | `architecture.md` C4.6 |
| ADR-019 | M-5 — `current_time` from client is intentional explicit-clock pattern | `architecture.md` C4.3 |
| ADR-020 | CRIT-1 — `animal.taxonomic_type` + `EnclosureType` title-case values fix always-False match | `architecture.md` C4.1, C4.4; `adr.md` ADR-012 |
| ADR-021 | DQ-1 — Minimal GET endpoints for grader state verification | `architecture.md` C3 |
| ADR-022 | DQ-2 — Second seed guide prevents one-shot tour exhaustion | `architecture.md` C3 |
| ADR-023 | DQ-3 — `current_time` wire format: `"HH:MM:SS"` canonical | `architecture.md` C4.3; `docs/bdd-scenarios.md` |
| ADR-024 | DQ-4 — Process 3 check ordering: schedule-first, assignment before existence | `architecture.md` C4.4 |
| ADR-025 | BLK-1 (fifth review) — `seed_zoo()` non-port method; `ZooRepository.save()` stays removed | `architecture.md` C4.2 |
| ADR-026 | DQ-B (fourth review) — `ConductGuidedTourUseCase` zoo-boundary check; `GuideNotInZooError` | `architecture.md` C4.3, C4.4 |
| ADR-027 | DQ-C (fourth review) — `AdmissionRecord.health_check_record_id: str \| None` | `architecture.md` C4.1, C4.3, C4.6 |
| ADR-028 | DQ-A (fourth review) — `FeedingRoundResponse.note` always-present `str` | `architecture.md` C4.3, C4.4 |
| ADR-029 | INC-5 (fifth review) — Process 3 non-existent `enclosure_id` → `FeedingNotDueError` not 404 | `architecture.md` C4.4 |
| ADR-030 | DQ-2 (fifth review) — `GuidedTourResponse.end_time` added for grader verifiability | `architecture.md` C4.3, C4.4 |
| ADR-031 | DQ-3 (fifth review) — `AssignZookeeperUseCase` idempotent same-zookeeper re-assignment | `architecture.md` C4.4 |
