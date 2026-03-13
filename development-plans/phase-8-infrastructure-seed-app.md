# Phase 8 — Infrastructure, Seed Data & App Assembly

**Goal:** Wire everything together — implement infrastructure modules (config, logging, dependency injection, seed data), assemble the FastAPI application in `main.py`, and verify that the application starts and serves all endpoints correctly with seed data.

**Depends on:** Phase 1–7 (all domain, adapter, use cases, routers, and exception handlers).
**Unlocks:** Phase 9 (final validation).

---

## Step 8.1 — Infrastructure: Config

**File:** `zoo_management/infrastructure/config.py`

**Implementation (plain dataclass, no Pydantic Settings — PRD §7.5):**

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class AppConfig:
    app_name: str = "Zoo Management System"
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"
```

**Tests:** No dedicated tests needed — config is trivial and consumed by `main.py`. Covered by integration tests.

---

## Step 8.2 — Infrastructure: Logging

**File:** `zoo_management/infrastructure/logging.py`

**Implementation (structured JSON logging — PRD §7.6):**

```python
import logging
import json
from datetime import datetime, timezone

class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "__dict__"):
            extras = {k: v for k, v in record.__dict__.items()
                      if k not in logging.LogRecord.__dict__ and not k.startswith("_")}
            if extras:
                log_record["extra"] = extras
        return json.dumps(log_record)

def configure_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(handler)
```

**Tests:** `tests/unit/test_logging.py`
```
- test_json_formatter_produces_valid_json
- test_configure_logging_sets_level
```

---

## Step 8.3 — Infrastructure: Seed Data

**File:** `zoo_management/infrastructure/seed.py`

**Tests first:** `tests/unit/test_seed_data.py`
```
- test_seed_data_creates_zoo_with_id_zoo_1
- test_seed_data_creates_three_enclosures
- test_seed_data_creates_zookeeper_alice
- test_seed_data_creates_veterinarian_dr_bob
- test_seed_data_creates_two_guides
- test_seed_data_creates_lion_in_mammal_enclosure
- test_seed_data_creates_unplaced_penguin
- test_seed_data_creates_two_feeding_schedules
- test_seed_data_mammal_enclosure_has_zookeeper_assigned
- test_seed_data_zoo_tour_route_has_three_enclosures
```

**Implementation (from architecture.md C3 — Pre-seeded entities table):**

```python
from zoo_management.adapters.in_memory import InMemoryRepositories
from zoo_management.domain.entities import *

def seed_data(repo: InMemoryRepositories) -> None:
    # Zoo
    zoo = Zoo(id="zoo-1", name="City Zoo",
              tour_route=["enc-mammal-1", "enc-bird-1", "enc-reptile-1"])
    repo.seed_zoo(zoo)  # Non-port method (ADR-025)

    # Enclosures
    enc_mammal = Enclosure(id="enc-mammal-1", name="Mammal Enclosure",
                           enclosure_type=EnclosureType.MAMMAL, zoo_id="zoo-1",
                           assigned_zookeeper_id="emp-zk-1")
    enc_bird = Enclosure(id="enc-bird-1", name="Bird Enclosure",
                         enclosure_type=EnclosureType.BIRD, zoo_id="zoo-1",
                         assigned_zookeeper_id="emp-zk-1")
    enc_reptile = Enclosure(id="enc-reptile-1", name="Reptile Enclosure",
                            enclosure_type=EnclosureType.REPTILE, zoo_id="zoo-1",
                            assigned_zookeeper_id="emp-zk-1")
    repo.save(enc_mammal)
    repo.save(enc_bird)
    repo.save(enc_reptile)

    # Employees
    repo.save(Zookeeper(id="emp-zk-1", name="Alice", zoo_id="zoo-1"))
    repo.save(Veterinarian(id="emp-vet-1", name="Dr. Bob", zoo_id="zoo-1"))
    repo.save(Guide(id="emp-guide-1", name="Carol", zoo_id="zoo-1", is_available=True))
    repo.save(Guide(id="emp-guide-2", name="Dave", zoo_id="zoo-1", is_available=True))

    # Animals
    lion = Lion(id="animal-lion-1", name="Simba", origin=Origin.INTERNAL,
                enclosure_id="enc-mammal-1")
    enc_mammal.animals.append(lion)
    repo.save(lion)
    repo.save(enc_mammal)  # re-save with updated animals list

    penguin = Penguin(id="animal-penguin-1", name="Pingu", origin=Origin.INTERNAL,
                      enclosure_id=None)
    repo.save(penguin)

    # Feeding Schedules
    repo.save(FeedingSchedule(id="sched-mammal-1", enclosure_id="enc-mammal-1",
                              scheduled_time=time(9, 0), diet="meat"))
    repo.save(FeedingSchedule(id="sched-bird-1", enclosure_id="enc-bird-1",
                              scheduled_time=time(10, 0), diet="fish"))
```

**Key constraints:**
- Use `repo.seed_zoo()` for Zoo (non-port method, ADR-025).
- Lion is pre-placed in `enc-mammal-1` (added to enclosure's animals list).
- Penguin is NOT placed (enclosure_id=None).
- All IDs are stable across restarts.
- Three enclosures all have `emp-zk-1` assigned.

**Verification:** `pytest tests/unit/test_seed_data.py` — all pass.

---

## Step 8.4 — Infrastructure: Dependency Injection

**File:** `zoo_management/infrastructure/dependencies.py`

**Implementation:**

```python
from zoo_management.adapters.in_memory import InMemoryRepositories
from zoo_management.usecases.assign_zookeeper import AssignZookeeperUseCase
from zoo_management.usecases.admit_animal import AdmitAnimalUseCase
from zoo_management.usecases.execute_feeding_round import ExecuteFeedingRoundUseCase
from zoo_management.usecases.conduct_health_check import ConductHealthCheckUseCase
from zoo_management.usecases.conduct_guided_tour import ConductGuidedTourUseCase

# Singleton repo instance — created once, reused across requests
_repo: InMemoryRepositories | None = None

def get_repository() -> InMemoryRepositories:
    """Returns the singleton InMemoryRepositories instance."""
    global _repo
    if _repo is None:
        _repo = InMemoryRepositories()
    return _repo

def set_repository(repo: InMemoryRepositories) -> None:
    """Allows main.py to set the seeded repository."""
    global _repo
    _repo = repo

def get_assign_zookeeper_use_case() -> AssignZookeeperUseCase:
    repo = get_repository()
    return AssignZookeeperUseCase(enclosure_repo=repo, employee_repo=repo)

def get_admit_animal_use_case() -> AdmitAnimalUseCase:
    repo = get_repository()
    return AdmitAnimalUseCase(
        animal_repo=repo, enclosure_repo=repo, employee_repo=repo,
        admission_repo=repo, health_repo=repo,
    )

def get_execute_feeding_round_use_case() -> ExecuteFeedingRoundUseCase:
    repo = get_repository()
    return ExecuteFeedingRoundUseCase(
        enclosure_repo=repo, employee_repo=repo, schedule_repo=repo,
    )

def get_conduct_health_check_use_case() -> ConductHealthCheckUseCase:
    repo = get_repository()
    return ConductHealthCheckUseCase(
        animal_repo=repo, employee_repo=repo, health_repo=repo,
    )

def get_conduct_guided_tour_use_case() -> ConductGuidedTourUseCase:
    repo = get_repository()
    return ConductGuidedTourUseCase(
        zoo_repo=repo, enclosure_repo=repo, employee_repo=repo, tour_repo=repo,
    )
```

**Note:** Integration tests use `app.dependency_overrides` to replace these factories with test-specific instances.

---

## Step 8.5 — Assemble main.py

**File:** `main.py`

**Implementation:**

```python
from fastapi import FastAPI
from zoo_management.adapters.in_memory import InMemoryRepositories
from zoo_management.adapters.web.routers import router
from zoo_management.adapters.web.exception_handlers import register_exception_handlers
from zoo_management.infrastructure.config import AppConfig
from zoo_management.infrastructure.logging import configure_logging
from zoo_management.infrastructure.seed import seed_data
from zoo_management.infrastructure.dependencies import set_repository

config = AppConfig()
configure_logging(config.log_level)

app = FastAPI(title=config.app_name)

# Register exception handlers
register_exception_handlers(app)

# Include routers
app.include_router(router)

# Seed data at startup
repo = InMemoryRepositories()
seed_data(repo)
set_repository(repo)
```

**Verification:**
1. `uvicorn main:app --port 8000` starts without error.
2. Visit `http://localhost:8000/docs` — OpenAPI docs show all endpoints.
3. `curl http://localhost:8000/animals/animal-lion-1` returns 200 with AnimalResponse.
4. `curl http://localhost:8000/enclosures/enc-mammal-1` returns 200 with EnclosureResponse.

---

## Step 8.6 — Smoke Test: End-to-End Endpoint Calls

**File:** `tests/integration/test_app_smoke.py`

**Tests (using the fully assembled app with seed data):**

```
- test_get_seeded_animal_returns_200
- test_get_seeded_enclosure_returns_200
- test_assign_zookeeper_with_seed_data
- test_admit_unplaced_penguin_with_seed_data
- test_feeding_round_with_seed_data_at_scheduled_time
- test_health_check_with_seed_data
- test_guided_tour_with_seed_data
```

These tests use the real app (no dependency overrides) and validate that seed data + all endpoints work together.

---

## Step 8.7 — Lint, Type Check, and Commit

```bash
ruff check .
mypy zoo_management/
pytest tests/
git add . && git commit -m "feat: infrastructure — config, logging, seed data, DI, app assembly"
```

---

## Phase 8 Completion Checklist

- [x] `AppConfig` dataclass in `infrastructure/config.py`
- [x] `JSONFormatter` and `configure_logging()` in `infrastructure/logging.py`
- [x] `seed_data(repo)` in `infrastructure/seed.py` with all stable IDs from architecture
- [x] Dependency injection factories in `infrastructure/dependencies.py`
- [x] `main.py` assembles app: FastAPI + routers + exception handlers + seed data
- [x] `uvicorn main:app` starts and serves all 7 endpoints
- [x] OpenAPI docs accessible at `/docs`
- [x] Smoke tests pass with seed data
- [x] ~10 seed data unit tests pass
- [x] ~7 smoke integration tests pass
- [x] ruff and mypy clean (for Phase 8 files)

---

**Previous phase:** [Phase 7 — Guided Tour](phase-7-feature-guided-tour.md)
**Next phase:** [Phase 9 — Final Validation & Documentation](phase-9-final-validation.md)
