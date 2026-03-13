# Zoo Management System — Incremental Development Plan

**Master Index**

This document is the entry point for the step-by-step incremental implementation plan of the Zoo Management System. Each phase is a self-contained iteration that builds on the previous one. The approach follows a strict **tests-first** (BDD + TDD) methodology: write failing tests, then implement the minimum code to make them pass, then refactor.

---

## Architecture & Skill References

| Document | Purpose |
|----------|---------|
| `docs/architecture.md` | C4 model, domain classes, repository ports, sequence diagrams, testing architecture |
| `docs/PRD.md` | Product requirements, business rules, tech stack, graded criteria |
| `docs/bdd-scenarios.md` | Gherkin scenarios for all 5 processes |
| `docs/business-processes-detailed.md` | Step-by-step process definitions |
| `docs/init-requriements.md` | Graded OOP requirements |
| `docs/adr.md` | Architectural Decision Records (ADR-001 through ADR-031) |
| `.cursor/skills/python-senior-engineer-fastapi/` | Engineering skill: tests first, diagram-driven, lint compliance |
| `.cursor/skills/fastapi-clean-architecture/` | Clean Architecture layers, testing patterns |

---

## Phase Overview

```
Phase 0 ─── Project Setup & Infrastructure
    │
Phase 1 ─── Domain Layer (entities, enums, exceptions, ports)
    │
Phase 2 ─── In-Memory Adapter (repository implementation)
    │
    ├── Phase 3 ─── Feature 1: Assign Zookeeper ────┐
    │                                                │
    ├── Phase 4 ─── Feature 2: Animal Admission ─────┤
    │                                                │
    ├── Phase 5 ─── Feature 3: Feeding Round ────────┤  (can partially parallel)
    │                                                │
    ├── Phase 6 ─── Feature 4: Health Check ─────────┤
    │                                                │
    └── Phase 7 ─── Feature 5: Guided Tour ──────────┘
                                                     │
Phase 8 ─── Infrastructure, Seed Data & App Assembly ─┘
    │
Phase 9 ─── Final Validation & Documentation
```

---

## Phase Details

### [Phase 0 — Repository Setup & Project Infrastructure](phase-0-project-setup.md)
- Git init, `.gitignore`
- Python 3.12 virtual environment
- `requirements.txt` + `requirements-dev.txt` (fastapi, uvicorn, pytest, pytest-bdd, httpx, ruff, mypy)
- `pyproject.toml` (ruff, mypy, pytest configuration)
- Full directory structure with `__init__.py` files
- Smoke test verification
- **Steps: 7 | Estimated tests: 1**

### [Phase 1 — Domain Layer Foundation](phase-1-domain-layer.md)
- Enums: `Origin`, `EnclosureType`, `HealthResult`
- 11 domain exceptions
- Animal hierarchy: `Animal` → `Mammal`/`Bird`/`Reptile` → 6 concrete classes
- Employee hierarchy: `Employee` → `Zookeeper`/`Veterinarian`/`Guide`
- Supporting entities: `Zoo`, `Enclosure`, `FeedingSchedule`
- Record entities: `AdmissionRecord`, `HealthCheckRecord`, `Tour`
- 8 repository port interfaces (ABC)
- All `__repr__`, `__str__`, `__eq__`, `@property`
- **Steps: 9 | Estimated tests: ~40**

### [Phase 2 — In-Memory Adapter](phase-2-in-memory-adapter.md)
- `InMemoryRepositories` implementing all 8 ports
- `seed_zoo()` non-port method (ADR-025)
- `EntityNotFoundError` on all `get_by_id` misses
- Composite key for `FeedingSchedule` (ADR-014)
- Port compliance `isinstance` tests
- **Steps: 9 | Estimated tests: ~28**

### [Phase 3 — Feature 1: Assign Zookeeper to Enclosure](phase-3-feature-assign-zookeeper.md)
- BDD feature file (4 scenarios)
- `AssignZookeeperUseCase` with three-way zoo check (ADR-016)
- Idempotent re-assignment (ADR-031)
- Router `POST /enclosures/{id}/zookeeper` → 200
- Exception handlers (first batch)
- Unit tests, integration tests, BDD step definitions
- **Steps: 7 | Estimated tests: ~16 (8 unit + 4 integration + 4 BDD)**

### [Phase 4 — Feature 2: Animal Admission](phase-4-feature-animal-admission.md)
- BDD feature file (5 scenarios)
- `AdmitAnimalUseCase` — most complex use case
- External/internal animal flow (ADR-002)
- `taxonomic_type` matching (ADR-020), first match (ADR-012)
- `AnimalAlreadyPlacedError` guard (ADR-013)
- `GET /animals/{id}` and `GET /enclosures/{id}` (ADR-021)
- Unit tests, integration tests, BDD step definitions
- **Steps: 8 | Estimated tests: ~28 (13 unit + 10 integration + 5 BDD)**

### [Phase 5 — Feature 3: Execute Feeding Round](phase-5-feature-feeding-round.md)
- BDD feature file (4 scenarios)
- `ExecuteFeedingRoundUseCase` with schedule matching
- Check ordering (ADR-024): schedule → enclosure → assignment → role
- Client-supplied `current_time` (ADR-019)
- Polymorphic `get_diet_type()` dispatch
- Note format (ADR-028): `"Fed N animals (diets: ...)"` / `"no animals to feed"`
- Non-existent enclosure → `FeedingNotDueError` (ADR-029)
- **Steps: 7 | Estimated tests: ~18 (9 unit + 5 integration + 4 BDD)**

### [Phase 6 — Feature 4: Conduct Health Check](phase-6-feature-health-check.md)
- BDD feature file (4 scenarios)
- `ConductHealthCheckUseCase` — simplest standalone use case
- HealthCheckRecord with date, result, notes
- Unit tests, integration tests, BDD step definitions
- **Steps: 7 | Estimated tests: ~18 (9 unit + 5 integration + 4 BDD)**

### [Phase 7 — Feature 5: Conduct Guided Tour](phase-7-feature-guided-tour.md)
- BDD feature file (4 scenarios)
- `ConductGuidedTourUseCase` with guide availability
- `start_time == end_time == now()` (ADR-011)
- Guide availability toggle (ADR-003)
- Guide-zoo match check (ADR-026)
- BDD test isolation (fresh state per scenario)
- **Steps: 7 | Estimated tests: ~20 (10 unit + 6 integration + 4 BDD)**

### [Phase 8 — Infrastructure, Seed Data & App Assembly](phase-8-infrastructure-seed-app.md)
- `AppConfig` dataclass
- `JSONFormatter` + `configure_logging()`
- `seed_data(repo)` with all stable IDs
- Dependency injection factories
- `main.py` — FastAPI app assembly
- End-to-end smoke tests with seed data
- **Steps: 7 | Estimated tests: ~19 (10 seed + 2 logging + 7 smoke)**

### [Phase 9 — Final Validation & Documentation](phase-9-final-validation.md)
- Docstrings on all public APIs (Google style)
- README.md: overview, user stories, class diagram, API table
- Full test suite run (168+ tests)
- Graded requirements traceability
- Layer isolation verification
- Manual API smoke test
- **Steps: 8 | Estimated tests: 0 new (validation only)**

---

## Summary Statistics

| Metric | Count |
|--------|-------|
| Total phases | 10 (0–9) |
| Total implementation steps | ~76 |
| Total estimated unit tests | ~105+ |
| Total estimated integration tests | ~37+ |
| Total BDD scenarios | 21 |
| Total estimated tests | ~168+ |
| Domain classes | 18 |
| Use cases | 5 |
| API endpoints | 7 |
| Repository ports | 8 |
| Domain exceptions | 11 |
| ADRs referenced | 31 |

---

## Implementation Order Rationale

The order follows the PRD §8.5 delivery sequence with dependencies:

1. **Phase 0–2 (foundation):** Must come first — project structure, domain, and adapter are prerequisites for everything.
2. **Phase 3 (assign zookeeper):** Simplest feature; establishes the end-to-end pattern (use case → router → tests → BDD).
3. **Phase 4 (animal admission):** Depends on enclosures existing; most complex logic. GET endpoints added here for state verification.
4. **Phase 5 (feeding round):** Needs animals in enclosures and zookeeper assignments.
5. **Phase 6 (health check):** Independent; simplest standalone process.
6. **Phase 7 (guided tour):** Independent; needs zoo and enclosures.
7. **Phase 8 (assembly):** Wires everything together; seed data for grader.
8. **Phase 9 (validation):** Final documentation and quality gate.

---

## Test-First Workflow Per Feature

Every feature phase (3–7) follows the same workflow:

```
1. Write BDD feature file (.feature)
2. Write unit tests for use case (tests/unit/)
3. Implement use case (usecases/)
4. Run unit tests — all pass
5. Write integration tests (tests/integration/)
6. Implement router + Pydantic schemas (adapters/web/)
7. Add exception handlers
8. Run integration tests — all pass
9. Write BDD step definitions (tests/step_defs/)
10. Run BDD tests — all pass
11. Lint + type check
12. Commit
```

This ensures no production code is written without a preceding test.
