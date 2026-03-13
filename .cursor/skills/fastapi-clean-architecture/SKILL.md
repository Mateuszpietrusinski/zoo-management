---
name: fastapi-clean-architecture
description: Guides FastAPI application design using Clean Architecture—domain/use-case/adapter layers, async I/O, Unit of Work, structured logging, and testable structure. Use when building or refactoring FastAPI APIs, when the user asks about Clean Architecture with FastAPI, or when avoiding business logic in router functions.
---

# FastAPI Clean Architecture

Apply this skill when designing or refactoring FastAPI applications so business logic, persistence, and HTTP stay decoupled. The goal is framework-agnostic domain and use cases, with adapters for web, database, and infrastructure.

## When to Apply

- Adding or changing FastAPI routes and you want logic outside routers
- Introducing repositories, use cases, or dependency injection
- Setting up config, logging, migrations, or testing for a FastAPI service
- User mentions "Clean Architecture", "hexagonal", or "layered" with FastAPI

## Project Structure

```
domain/           # Pure Python, no framework imports
  entities.py     # Dataclasses
  interfaces.py   # abc.ABC repositories and ports
usecases/         # Business rules only, depends on domain
adapters/         # Implement interfaces (DB, security, web)
  database.py
  security.py
  web/routers.py, exception_handlers.py
infrastructure/   # Config, DB engine/session, logging, DI wiring
  config.py, database.py, db_models.py, dependencies.py, logging.py
tests/
  unit/           # Use case tests with in-memory fakes
  integration/    # HTTP tests with dependency overrides
```

## Layer Rules

| Layer | Allowed | Forbidden |
|-------|---------|-----------|
| **Domain** | `dataclasses`, `abc`, `uuid`, `logging` | FastAPI, SQLAlchemy, Pydantic |
| **Use cases** | Domain entities/interfaces, logging | HTTP, DB, framework imports |
| **Adapters** | Domain interfaces, framework (FastAPI, SQLAlchemy) | Business logic |
| **Infrastructure** | Wiring, config, session lifecycle | Business logic |

- **Routers**: Validate input (Pydantic), build use-case request DTO, call use case, map response to API schema. No business logic, no direct DB.
- **Repositories**: Accept `AsyncSession` from outside; never `commit()`—transaction boundary is in infrastructure (e.g. `get_db_session`).
- **Use cases**: Receive request DTO and injected repo/hasher/etc.; no framework types. Raise domain exceptions (e.g. `EmailAlreadyExistsError`) for the web layer to map to HTTP status.

## Key Principles

1. **Async all the way** — Session, repository, and use case are async so the event loop is not blocked.
2. **Unit of Work** — One commit per request, in the session dependency; repositories only add/query.
3. **Interfaces at the boundary** — Define full contracts (e.g. `PasswordHasher` with both `hash` and `verify`) in `domain/interfaces.py`.
4. **Validate at HTTP boundary** — Pydantic (e.g. `EmailStr`, `Field(min_length=8)`) in router/schemas; use case receives already-valid DTOs.
5. **Global exception handlers** — Register domain and validation handlers on the app; return consistent JSON error shape.
6. **Config at startup** — Use Pydantic Settings; fail fast if required env (e.g. `DATABASE_URL`) is missing.
7. **Structured logging** — JSON formatter, use case logs with `extra={}` for context (e.g. `email`, `user_id`).

## Testing

- **Unit**: Use case only. In-memory fakes implementing domain interfaces (e.g. `InMemoryUserRepository`, `FakePasswordHasher`). No DB, no HTTP. Assert on return value and fake state.
- **Integration**: FastAPI app with real router and exception handlers; override use-case dependency to inject the same fakes. Use `httpx.AsyncClient` with `ASGITransport(app)`. Assert status codes and JSON; no real DB required.

## Full Reference

For complete code (config, logging, domain entities/interfaces, register-user use case, SQLAlchemy adapter, security adapter, routers, exception handlers, session/dependencies, Alembic, main.py, unit and integration tests, requirements), see [reference.md](reference.md).
