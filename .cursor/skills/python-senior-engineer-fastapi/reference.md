# Python Senior Engineer — Reference (Lint, Diagrams, Tests)

## FastAPI and Python Lint Rules

Apply these unless the project has stricter overrides (e.g. in `pyproject.toml`, `.flake8`, `ruff.toml`).

### General Python

- **Type hints**: All public functions, method signatures, and DTOs. Use `typing` or `from __future__ import annotations`.
- **Async**: Use `async def` for I/O (DB, HTTP client); avoid blocking calls in async code.
- **Imports**: Absolute or consistent relative; no unused imports. Use `isort` or ruff `I` for order.
- **Naming**: `snake_case` for functions/variables; `PascalCase` for classes; `UPPER` for constants.
- **Line length**: Typically 88 (Black) or 100; match project config.
- **Docstrings**: Public modules, classes, and functions; prefer Google or NumPy style if project uses one.

### FastAPI-Specific

- **Routers**: Only validate (Pydantic), call use case, map response. No `await session.execute()`, no business conditionals.
- **Dependencies**: Inject session, use cases, repos via FastAPI `Depends()`; no global state for request-scoped data.
- **Schemas**: Pydantic models for request/response; validate at boundary (e.g. `Field`, `EmailStr`). No ORM models in API schemas.
- **Status codes**: Explicit (e.g. `status_code=201`); use `HTTPException` or mapped domain exceptions for errors.
- **Tags and prefixes**: Use for grouping and OpenAPI clarity.

### Ruff / Flake8 / Pylint (typical)

- Enable: unused imports (F401), undefined names (F821), line length (E501 if not Black).
- Prefer: ruff for speed; mypy for strict typing. Run before commit.
- Ignore only with justification (e.g. `# noqa` with comment).

### Clean Architecture Boundaries

- **Domain**: No `fastapi`, `sqlalchemy`, or `pydantic` (except if Pydantic used for domain DTOs by convention).
- **Use cases**: No HTTP or DB imports; only domain and port interfaces.
- **Adapters**: May import FastAPI, SQLAlchemy, etc.; implement ports only; no business rules.

---

## Implementing from BPMN

| BPMN element   | Implementation focus |
|----------------|------------------------|
| Start event   | Trigger (e.g. API endpoint, message handler). |
| Task          | Use case or adapter step; one task ≈ one use case or one repo call. |
| Gateway       | `if/elif` or match; document condition in code comment. |
| Sequence flow | Order of calls in use case or step definitions. |
| End event     | Response or side-effect (e.g. commit, send event). |

Name use cases and step definitions after task IDs or labels (e.g. `perform_health_check`, `assign_zookeeper`) for traceability.

---

## Implementing from Mermaid

- **Flowchart (LR/TD)**: Nodes = components (router, use case, repo). Arrows = calls. Implement same direction and boundaries (e.g. router → use case → repo).
- **Sequence diagram**: Each arrow = one call; implement the same order and return values. Use for request/response and error paths.
- **ER diagram**: Entities = tables or domain aggregates; relations = FKs and repo methods. Implement models and migrations to match cardinality.

---

## BDD and Integration Test Conventions

- **Gherkin**: `features/*.feature`; one feature per process or capability. Steps reuse across scenarios.
- **Step definitions**: Map to use case or API call; use shared fixtures (DB, app client). Prefer one layer (e.g. HTTP) for integration.
- **Integration**: Use real app + test DB (Docker or SQLite for speed). Seed data in Given; assert on DB and response in Then.
- **IDs and names**: Use stable test data (e.g. "Savanna", "Alice") so scenarios stay readable; avoid random IDs in Given/Then.

---

## When to Ask (No Guessing)

- Acceptance criteria missing or contradictory.
- BPMN/Mermaid has multiple valid interpretations (e.g. parallel vs sequential).
- Non-functional requirement unclear (e.g. "fast", "scalable", timeouts).
- Conflicting lint/format rules or project structure.
- API contract (status codes, error shape) not specified.

Ask in the form: “Requirement X says …; should the implementation do A or B (or something else)?”
