---
name: architect-python-fastapi
description: Guides system and API design using Python, FastAPI, PostgreSQL, Docker, hexagonal (ports & adapters) architecture, BPMN for process flows, and Mermaid for diagrams. Use when designing or documenting systems, choosing architecture, modeling business processes (BPMN), or creating architecture or flow diagrams in Mermaid.
---

# Architect — Python, FastAPI, PostgreSQL, Docker, Hexagonal, BPMN, Mermaid

Apply this skill when making architecture decisions, designing services, modeling processes, or producing diagrams. It covers a consistent stack: Python/FastAPI for APIs, PostgreSQL for persistence, Docker for runtimes, hexagonal architecture for structure, BPMN for process modeling, and Mermaid for visuals.

## When to Apply

- Designing or documenting a new service or system
- Choosing or explaining hexagonal/ports-and-adapters layout
- Defining APIs (REST, async), data models, or DB schema
- Planning Docker images, Docker Compose, or deployment
- Modeling business processes or workflows (BPMN)
- Creating architecture, sequence, ER, or flow diagrams (Mermaid)

## Stack at a Glance

| Concern | Use |
|--------|-----|
| **Python** | Type hints, async/await, dataclasses, `abc` for ports |
| **FastAPI** | HTTP adapter only; business logic in use cases / domain |
| **PostgreSQL** | Primary data store; async via asyncpg; migrations (e.g. Alembic) |
| **Docker** | Multi-stage Dockerfile, non-root user; Compose for local dev |
| **Hexagonal** | Domain at center; ports (interfaces); adapters (web, DB, messaging) |
| **BPMN** | Process flows: tasks, gateways, events, sequence flows |
| **Mermaid** | Flowcharts, sequence diagrams, ER, C4-style context/container |

---

## Hexagonal Architecture (Ports & Adapters)

- **Domain**: Entities and business rules; no framework or I/O.
- **Ports**: Interfaces (e.g. `UserRepository`, `EventPublisher`) defined in or next to domain; implemented by adapters.
- **Adapters**: Implement ports — e.g. HTTP (FastAPI routers), PostgreSQL (repositories), message queues, external APIs. Dependency rule: dependencies point inward (adapters depend on ports, not the reverse).
- **Application/use cases**: Orchestrate domain and ports; no HTTP or SQL. Inject ports via constructors or DI.

For a FastAPI + PostgreSQL service, align with the project’s FastAPI Clean Architecture skill: domain → use cases → adapters (web, DB) → infrastructure (config, session, DI).

---

## Python & FastAPI

- **Python**: Prefer type hints, `dataclass` or Pydantic where appropriate, `async`/`await` for I/O-bound work. Use `abc.ABC` for ports.
- **FastAPI**: Keep routers thin — validate input (Pydantic), call use case, map response. No business logic or direct DB access in route handlers. Use dependency injection for use cases and repositories (session, etc.).

---

## PostgreSQL

- Use **async** drivers (e.g. **asyncpg**) with SQLAlchemy 2.0 async or raw asyncpg so the event loop is not blocked.
- Prefer **migrations** (e.g. Alembic) over ad-hoc DDL; never rely only on `create_all()` in production.
- Connection handling: pool in app (e.g. SQLAlchemy engine + session per request); configure pool size and timeouts from config/env.

---

## Docker

- **Dockerfile**: Multi-stage build (e.g. builder stage for deps, runtime stage with only app + venv or installed package). Run as non-root when possible. Set `WORKDIR`, explicit `CMD`/`ENTRYPOINT`.
- **Images**: Prefer slim base images; pin versions. Copy only what’s needed for the run stage.
- **Compose**: Use for local dev (app + Postgres + optional queues). Env vars for `DATABASE_URL`, etc.; health checks for DB and app if useful.

---

## BPMN (Business Process Model and Notation)

- Use for **process flows**: who does what, in what order, with decisions and events.
- **Core elements**: **Tasks** (work), **Events** (start, end, intermediate), **Gateways** (exclusive/or/parallel), **Sequence flows** (order), **Pools/lanes** (actors/systems).
- **Good for**: User journeys, approval flows, order/fulfillment, integration choreography. Prefer BPMN when the user asks for “process”, “workflow”, or “BPMN”; use Mermaid for diagram syntax unless a dedicated BPMN tool is used.

---

## Mermaid Diagrams

Use Mermaid for version-controlled, text-based diagrams in docs or ADRs.

- **Flowchart**: `graph TD/LR`, `A --> B`, `subgraph`, decisions with `-->|label|`.
- **Sequence**: `participant`, `->`/`-->` for sync/async; `activate`/`deactivate` for lifelines.
- **ER**: `Entity ||--o{ Entity` (one-to-many), `entity { type id }`.
- **C4-style**: Use `flowchart` with subgraphs for Context (system + users/external systems) and Container (high-level components); optional Container diagram per system.

Prefer a single diagram per concern (e.g. one context, one sequence per scenario). Put recurring snippets and examples in [reference.md](reference.md).

---

## Diagram and Doc Conventions

- **One diagram, one purpose**: e.g. one architecture context, one sequence per main flow.
- **Names**: Use consistent names for systems, services, and components across docs and code.
- **ADR**: For big decisions (e.g. “use hexagonal”, “PostgreSQL + asyncpg”), consider a short ADR (context, decision, consequences) and link a Mermaid diagram if it helps.

---

## Additional Reference

- Mermaid syntax snippets and BPMN-by-Mermaid patterns: [reference.md](reference.md).
- FastAPI + hexagonal/Clean Architecture in this project: use the **fastapi-clean-architecture** skill.
