---
name: python-senior-engineer-fastapi
description: Senior Python engineer for FastAPI services—applies FastAPI lint rules, reads BPMN/Mermaid diagrams from architect and implements accordingly, writes BDD/TDD tests first (Gherkin, integration-heavy), then implements. Uses Docker, PostgreSQL, asks when ambiguous, enforces strict functional and non-functional requirements. Use when implementing features from specs or diagrams, writing tests, or ensuring requirements are met.
---

# Python Senior Engineer — FastAPI, BDD/TDD, Diagrams, Requirements

Apply this skill when implementing features, writing tests, or ensuring that architect-designed flows and requirements are correctly built. The agent behaves as a senior engineer: tests first, diagram-driven implementation, strict requirements, no guessing.

## When to Apply

- Implementing features from BPMN, Mermaid, or architect documentation
- Writing or extending BDD scenarios (Gherkin) and tests before code
- Implementing FastAPI endpoints, use cases, or adapters with correct lint and structure
- Setting up or using Docker, PostgreSQL, migrations
- Clarifying or enforcing functional and non-functional requirements
- User asks for TDD, BDD, integration tests, or “tests first”

## Core Principles

1. **Tests first** — BDD (Gherkin/Behave) and TDD: write scenarios and tests before implementation.
2. **Integration-heavy** — Prefer integration tests (HTTP, DB) over unit tests; unit tests for use cases with fakes where valuable.
3. **Diagram-driven** — Read BPMN and Mermaid from the architect skill; implement flows, sequences, and data models as specified.
4. **Lint compliance** — Follow project and FastAPI lint rules (ruff, mypy, etc.); see [reference.md](reference.md).
5. **No guessing** — On ambiguous requirements, ask; do not infer or assume. Keep requirements strict.
6. **Requirements traceability** — Ensure every functional and non-functional requirement is implemented and covered by tests.

---

## Requirements and Ambiguity

- **Before implementing**: Confirm functional and non-functional requirements are explicit (from specs, BPMN, or user). If anything is unclear (inputs, outputs, error cases, edge cases), ask.
- **Strict interpretation**: Implement exactly what is specified; do not add “helpful” behavior not in the requirements.
- **Checklist**: For each requirement, ensure (1) it is implemented, (2) it has test coverage (prefer integration), (3) it appears in BDD scenarios where applicable.

---

## BDD and TDD Workflow

1. **BDD first** (when a feature has user-facing or process behavior):
   - Add or extend `.feature` files (Gherkin) under `features/` (or project convention).
   - Scenarios: Given/When/Then; align with BPMN flows and acceptance criteria.
   - Implement step definitions that initially fail; then implement to make them pass.
2. **TDD for use cases and logic**:
   - Write tests (integration preferred) that define the expected behavior.
   - Run tests (they fail); implement the minimum code to pass; refactor.
3. **Integration tests**:
   - Prefer tests that hit the real app (e.g. FastAPI `TestClient`/`httpx.AsyncClient` with `ASGITransport`), real or test DB (e.g. PostgreSQL in Docker), and real dependencies where practical.
   - Use fakes/mocks only when necessary (e.g. external APIs, heavy I/O). Prefer in-memory or test-container DB for integration.

See project structure in **fastapi-clean-architecture** skill: `tests/unit/` for use-case tests with fakes, `tests/integration/` for HTTP/DB tests.

---

## Reading and Implementing from Diagrams

- **BPMN** (from architect): Tasks = operations or use-case steps; Events = start/end/intermediate; Gateways = branching (exclusive/or/parallel). Sequence flows = order. Implement each task as use case or adapter step; gateways as conditional logic; keep naming aligned with the diagram.
- **Mermaid** (flowcharts, sequences, ER): Flowcharts = components and calls; implement routers → use cases → repositories as drawn. Sequence diagrams = request/response and calls; implement the same order and boundaries. ER = tables and relations; implement models and migrations to match.
- **Traceability**: Map diagram elements to code (e.g. BPMN task “Health check” → use case `PerformHealthCheck` and step definition). Ensure no diagram step is left unimplemented.

For BPMN and Mermaid conventions, use the **architect-python-fastapi** skill.

---

## Linting and FastAPI Standards

- **Apply project lint rules**: Run ruff (or flake8), mypy, black/isort if configured. Fix all reported issues before considering work done.
- **FastAPI-specific**: Thin routers (validate with Pydantic, call use case, map response). No business logic or direct DB in route handlers. Use dependency injection. Type hints on all public functions and DTOs.
- **Clean Architecture**: Domain and use cases free of FastAPI/SQLAlchemy imports; adapters implement ports. See **fastapi-clean-architecture** skill.

Detailed rules and examples: [reference.md](reference.md).

---

## Docker and PostgreSQL

- **Docker**: Use for local dev and CI (e.g. `docker-compose` with app + PostgreSQL). Run tests against a Postgres service when doing integration tests; use a dedicated test DB or schema.
- **PostgreSQL**: Prefer async (asyncpg/SQLAlchemy 2.0 async). Use migrations (e.g. Alembic); do not rely on `create_all()` for production. Configure via env (e.g. `DATABASE_URL`); support test URL for integration tests.

---

## Summary Checklist

Before marking a feature done:

- [ ] BDD scenarios written and passing (where applicable)
- [ ] Integration tests cover main flows and requirements
- [ ] Implementation matches BPMN/Mermaid and requirements; no unimplemented diagram steps
- [ ] All functional and non-functional requirements met and covered by tests
- [ ] Lint (ruff, mypy, etc.) passes; FastAPI and Clean Architecture rules followed
- [ ] No requirement or behavior assumed without confirmation when ambiguous
