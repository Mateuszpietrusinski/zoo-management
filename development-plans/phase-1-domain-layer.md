# Phase 1 — Domain Layer Foundation

**Goal:** Implement all domain entities (18 classes), enums, domain exceptions, and repository port interfaces. This is the pure-Python core with zero framework imports. Every class gets `__repr__`, `__str__`, `__eq__`, and `@property` as required.

**Depends on:** Phase 0 (project structure exists).
**Unlocks:** Phase 2 (in-memory adapter), Phase 3–7 (features).

---

## ✓ Step 1.1 — Domain Enums

**File:** `zoo_management/domain/entities.py` (top of file)

**Tests first** — `tests/unit/test_domain_enums.py`:
```
- test_origin_enum_has_internal_and_external
- test_enclosure_type_enum_values_are_title_cased (Mammal, Bird, Reptile)
- test_health_result_enum_has_three_values (HEALTHY, NEED_FOLLOW_UP, CRITICAL)
```

**Implementation:**
```python
import enum

class Origin(enum.Enum):
    INTERNAL = "internal"
    EXTERNAL = "external"

class EnclosureType(enum.Enum):
    MAMMAL = "Mammal"
    BIRD = "Bird"
    REPTILE = "Reptile"

class HealthResult(enum.Enum):
    HEALTHY = "healthy"
    NEED_FOLLOW_UP = "need_follow_up"
    CRITICAL = "critical"
```

**Key constraint (ADR-020):** `EnclosureType` values are title-cased (`"Mammal"`, `"Bird"`, `"Reptile"`) to match `Animal.taxonomic_type` which returns the MRO class name.

**Verification:** `pytest tests/unit/test_domain_enums.py` — all pass.

**Done.**

---

## ✓ Step 1.2 — Domain Exceptions

**File:** `zoo_management/domain/exceptions.py` (new file)

**Tests first** — `tests/unit/test_domain_exceptions.py`:
```
- test_entity_not_found_error_is_exception
- test_entity_not_found_error_carries_message
- test_all_domain_exceptions_are_subclasses_of_exception
```

**Implementation — all exceptions from architecture.md C3:**
```python
class EntityNotFoundError(Exception): ...
class NoSuitableEnclosureError(Exception): ...
class HealthCheckNotClearedError(Exception): ...
class ZookeeperNotAssignedError(Exception): ...
class FeedingNotDueError(Exception): ...
class EnclosureNotInZooError(Exception): ...
class NoGuideAvailableError(Exception): ...
class InvalidEmployeeRoleError(Exception): ...
class InvalidRequestError(Exception): ...
class AnimalAlreadyPlacedError(Exception): ...
class GuideNotInZooError(Exception): ...
```

**Total: 11 domain exception classes** (from architecture.md §C3 exception table).

**Verification:** `pytest tests/unit/test_domain_exceptions.py` — all pass.

**Done.**

---

## ✓ Step 1.3 — Animal Hierarchy (ABC → Mid-tier → Concrete)

**File:** `zoo_management/domain/entities.py`

**Tests first** — `tests/unit/test_animal_entities.py`:
```
- test_cannot_instantiate_animal_directly (ABC)
- test_cannot_instantiate_mammal_directly (ABC)
- test_cannot_instantiate_bird_directly (ABC)
- test_cannot_instantiate_reptile_directly (ABC)
- test_lion_get_diet_type_returns_carnivore
- test_elephant_get_diet_type_returns_herbivore
- test_monkey_get_diet_type_returns_omnivore
- test_eagle_get_diet_type_returns_carnivore
- test_penguin_get_diet_type_returns_piscivore
- test_crocodile_get_diet_type_returns_carnivore
- test_lion_type_name_returns_lion
- test_lion_taxonomic_type_returns_mammal
- test_penguin_taxonomic_type_returns_bird
- test_crocodile_taxonomic_type_returns_reptile
- test_animal_is_placed_false_when_no_enclosure
- test_animal_is_placed_true_when_enclosure_set
- test_animal_repr_contains_id_and_name
- test_animal_str_contains_name
- test_animal_eq_by_id
- test_animal_eq_different_id_not_equal
```

**Implementation details (from architecture.md C4.1):**

- `Animal` (ABC): `__init__(self, id, name, origin, enclosure_id=None)`
  - `@property type_name -> str`: returns `type(self).__name__`
  - `@property taxonomic_type -> str`: returns `type(self).__mro__[1].__name__` — **must include docstring warning per M-1**
  - `@property is_placed -> bool`: returns `self.enclosure_id is not None`
  - `@abc.abstractmethod get_diet_type(self) -> str`
  - `__repr__`, `__str__`, `__eq__` (by id)

- `Mammal(Animal)` (ABC): no new fields, `get_diet_type` still abstract
- `Bird(Animal)` (ABC): no new fields, `get_diet_type` still abstract
- `Reptile(Animal)` (ABC): no new fields, `get_diet_type` still abstract

- `Lion(Mammal)`: `get_diet_type() -> "carnivore"`
- `Elephant(Mammal)`: `get_diet_type() -> "herbivore"`
- `Monkey(Mammal)`: `get_diet_type() -> "omnivore"`
- `Eagle(Bird)`: `get_diet_type() -> "carnivore"`
- `Penguin(Bird)`: `get_diet_type() -> "piscivore"`
- `Crocodile(Reptile)`: `get_diet_type() -> "carnivore"`

**Verification:** `pytest tests/unit/test_animal_entities.py` — all pass. `ruff check` + `mypy` clean.

**Done.**

---

## ✓ Step 1.4 — Employee Hierarchy (ABC → Concrete)

**File:** `zoo_management/domain/entities.py`

**Tests first** — `tests/unit/test_employee_entities.py`:
```
- test_cannot_instantiate_employee_directly (ABC)
- test_zookeeper_role_returns_zookeeper
- test_veterinarian_role_returns_veterinarian
- test_guide_role_returns_guide
- test_guide_is_available_defaults_to_true
- test_guide_is_available_can_be_set_false
- test_employee_repr_contains_id_and_name
- test_employee_str_contains_name
- test_employee_eq_by_id
```

**Implementation (from architecture.md C4.1):**

- `Employee` (ABC): `__init__(self, id, name, zoo_id)`
  - `@property role -> str`: returns `type(self).__name__`
  - `__repr__`, `__str__`, `__eq__` (by id)

- `Zookeeper(Employee)`: no new fields
- `Veterinarian(Employee)`: no new fields
- `Guide(Employee)`: adds `is_available: bool = True` (ADR-003)

**Verification:** `pytest tests/unit/test_employee_entities.py` — all pass.

**Done.**

---

## ✓ Step 1.5 — Zoo, Enclosure, FeedingSchedule

**File:** `zoo_management/domain/entities.py`

**Tests first** — `tests/unit/test_supporting_entities.py`:
```
- test_zoo_creation_with_tour_route
- test_zoo_repr_str_eq
- test_enclosure_creation_with_type_and_zoo_id
- test_enclosure_animals_defaults_to_empty_list
- test_enclosure_is_occupied_false_when_no_animals
- test_enclosure_is_occupied_true_when_animals_present
- test_enclosure_animal_count_matches_list_length
- test_enclosure_assigned_zookeeper_id_defaults_to_none
- test_enclosure_repr_str_eq
- test_feeding_schedule_creation
- test_feeding_schedule_schedule_info_property
- test_feeding_schedule_repr_str
```

**Implementation (from architecture.md C4.1):**

- `Zoo`: `__init__(self, id, name, tour_route: list[str])`
  - `__repr__`, `__str__`, `__eq__` (by id)

- `Enclosure`: `__init__(self, id, name, enclosure_type: EnclosureType, zoo_id, assigned_zookeeper_id=None, animals=None)`
  - `animals: list[Animal]` — initialized to `[]` if None (ADR-001)
  - `@property is_occupied -> bool`: `len(self.animals) > 0`
  - `@property animal_count -> int`: `len(self.animals)`
  - `__repr__`, `__str__`, `__eq__` (by id)

- `FeedingSchedule`: `__init__(self, id, enclosure_id, scheduled_time: time, diet: str)`
  - `@property schedule_info -> str`: formatted summary
  - `__repr__`, `__str__`

**Verification:** `pytest tests/unit/test_supporting_entities.py` — all pass.

**Done.**

---

## ✓ Step 1.6 — Record Entities (AdmissionRecord, HealthCheckRecord, Tour)

**File:** `zoo_management/domain/entities.py`

**Tests first** — `tests/unit/test_record_entities.py`:
```
- test_admission_record_creation
- test_admission_record_health_check_record_id_nullable (ADR-027)
- test_admission_record_repr_str
- test_health_check_record_creation
- test_health_check_record_notes_nullable
- test_health_check_record_repr_str
- test_tour_creation_with_route_and_times
- test_tour_is_completed_true_when_end_time_set
- test_tour_repr_str
```

**Implementation (from architecture.md C4.1):**

- `AdmissionRecord`: `__init__(self, id, date, animal_id, enclosure_id, zookeeper_id: str|None, vet_id: str|None, health_check_record_id: str|None)`
  - `__repr__`, `__str__`

- `HealthCheckRecord`: `__init__(self, id, date, animal_id, vet_id, result: HealthResult, notes: str|None)`
  - `__repr__`, `__str__`

- `Tour`: `__init__(self, id, guide_id, route: list[str], start_time: datetime, end_time: datetime)`
  - `@property is_completed -> bool`
  - `__repr__`, `__str__`

**Verification:** `pytest tests/unit/test_record_entities.py` — all pass.

**Done.**

---

## ✓ Step 1.7 — Repository Port Interfaces

**File:** `zoo_management/domain/interfaces.py`

**Tests first** — `tests/unit/test_interfaces.py`:
```
- test_zoo_repository_is_abstract
- test_enclosure_repository_is_abstract
- test_animal_repository_is_abstract
- test_employee_repository_is_abstract
- test_feeding_schedule_repository_is_abstract
- test_admission_record_repository_is_abstract
- test_health_check_record_repository_is_abstract
- test_tour_repository_is_abstract
- test_cannot_instantiate_any_repository_directly
```

**Implementation (from architecture.md C4.2 — exact method signatures):**

```python
import abc
from datetime import time
from zoo_management.domain.entities import (
    Zoo, Enclosure, Animal, Employee,
    FeedingSchedule, AdmissionRecord, HealthCheckRecord, Tour,
)

class ZooRepository(abc.ABC):
    @abc.abstractmethod
    def get_by_id(self, id: str) -> Zoo: ...

class EnclosureRepository(abc.ABC):
    @abc.abstractmethod
    def get_by_id(self, id: str) -> Enclosure: ...
    @abc.abstractmethod
    def get_by_zoo(self, zoo_id: str) -> list[Enclosure]: ...
    @abc.abstractmethod
    def save(self, enclosure: Enclosure) -> None: ...

class AnimalRepository(abc.ABC):
    @abc.abstractmethod
    def get_by_id(self, id: str) -> Animal: ...
    @abc.abstractmethod
    def save(self, animal: Animal) -> None: ...

class EmployeeRepository(abc.ABC):
    @abc.abstractmethod
    def get_by_id(self, id: str) -> Employee: ...
    @abc.abstractmethod
    def get_by_zoo_and_type(self, zoo_id: str, role: str) -> list[Employee]: ...
    @abc.abstractmethod
    def save(self, employee: Employee) -> None: ...

class FeedingScheduleRepository(abc.ABC):
    @abc.abstractmethod
    def get_by_enclosure_and_time(self, enclosure_id: str, t: time) -> FeedingSchedule | None: ...
    @abc.abstractmethod
    def save(self, schedule: FeedingSchedule) -> None: ...

class AdmissionRecordRepository(abc.ABC):
    @abc.abstractmethod
    def save(self, record: AdmissionRecord) -> None: ...

class HealthCheckRecordRepository(abc.ABC):
    @abc.abstractmethod
    def save(self, record: HealthCheckRecord) -> None: ...

class TourRepository(abc.ABC):
    @abc.abstractmethod
    def save(self, tour: Tour) -> None: ...
```

**Key constraint:**
- `ZooRepository` has **no** `save()` method (ADR-025).
- `AnimalRepository` has **no** `get_unplaced()` method.
- `FeedingScheduleRepository.get_by_enclosure_and_time` returns `FeedingSchedule | None`.
- All `get_by_id` methods raise `EntityNotFoundError` on miss (ADR-015).

**Verification:** `pytest tests/unit/test_interfaces.py` — all pass. `mypy zoo_management/domain/` clean.

**Done.**

---

## ✓ Step 1.8 — Lint and Type Check Full Domain Layer

**Action:**
1. `ruff check zoo_management/domain/`
2. `mypy zoo_management/domain/`
3. Fix any issues.

**Verification:** Both tools exit 0.

**Done.**

---

## ✓ Step 1.9 — Commit Phase 1

**Action:**
```bash
git add .
git commit -m "feat: domain layer — entities, enums, exceptions, repository ports"
```

**Verification:** All domain tests pass. Clean lint/mypy.

**Done.**

---

## Phase 1 Completion Checklist

- [x] 3 enums implemented: `Origin`, `EnclosureType`, `HealthResult`
- [x] 11 domain exceptions implemented
- [x] 10 Animal hierarchy classes (ABC + mid-tier + 6 concrete) with `get_diet_type()` polymorphism
- [x] 4 Employee hierarchy classes (ABC + 3 concrete) with `role` property
- [x] `Zoo`, `Enclosure`, `FeedingSchedule` with all `@property` methods
- [x] `AdmissionRecord`, `HealthCheckRecord`, `Tour` record entities
- [x] 8 repository port interfaces (ABC) with exact method signatures
- [x] All classes have `__repr__`, `__str__`, `__eq__` where specified
- [x] `taxonomic_type` property has required M-1 docstring
- [x] All unit tests pass (~40+ tests)
- [x] ruff and mypy clean

---

**Previous phase:** [Phase 0 — Project Setup](phase-0-project-setup.md)
**Next phase:** [Phase 2 — In-Memory Adapter](phase-2-in-memory-adapter.md)
