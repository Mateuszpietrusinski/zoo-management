# Zoo Management System

A REST API for zoo operations: animal admission, zookeeper assignment, feeding rounds, health checks, and guided tours. Built with Python 3.12, FastAPI, and a hexagonal (ports & adapters) architecture.

---

## 1. Project Overview

The **Zoo Management System** exposes an HTTP API used by four roles: Zoo Manager, Zookeeper, Veterinarian, and Guide. It supports admitting animals to enclosures, assigning zookeepers to enclosures, executing feeding rounds, recording health checks, and conducting guided tours. State is held in-memory (no database for MVP); the design allows swapping to PostgreSQL via adapters without changing domain or use-case code.

### How to run

```bash
pip install -r requirements.txt && uvicorn main:app
```

The API is served at `http://localhost:8000` (or the host/port configured in `AppConfig`). OpenAPI docs: `http://localhost:8000/docs`.

### How to test

```bash
pip install -r requirements-dev.txt && pytest
```

Run subsets: `pytest tests/unit/`, `pytest tests/integration/`, `pytest tests/step_defs/`.

---

## 2. User Stories

1. As a **zoo manager**, I want to admit a new animal to a suitable enclosure  
   so that it is correctly housed and has an assigned caretaker.

2. As a **zookeeper**, I want to execute a feeding round for my assigned enclosure  
   so that animals are fed on time.

3. As a **veterinarian**, I want to conduct a health check on an animal and record the result  
   so that the zoo can track health and schedule follow-up.

4. As a **zoo manager**, I want to assign a zookeeper to an enclosure  
   so that feeding and daily care are clearly owned.

5. As a **guide**, I want to conduct a guided tour through the zoo's enclosures  
   so that visitors see all animals.

---

## 3. Class Diagram (Mermaid)

Domain model: Animal hierarchy (ABC → Mammal/Bird/Reptile → concrete), Employee hierarchy (ABC → Zookeeper/Veterinarian/Guide), Zoo, Enclosure, FeedingSchedule, and record types. Relationships: composition (Zoo–Enclosure), aggregation (Enclosure–Animal, Zoo–Employee), association (Zookeeper–Enclosure).

```mermaid
classDiagram
  class Animal {
    <<abstract>>
    +id: str
    +name: str
    +origin: Origin
    +enclosure_id: str | None
    +type_name() str
    +taxonomic_type() str
    +is_placed() bool
    +get_diet_type()* str
    +__repr__()
    +__str__()
    +__eq__()
  }
  class Mammal { <<abstract>> }
  class Bird   { <<abstract>> }
  class Reptile{ <<abstract>> }

  Animal <|-- Mammal
  Animal <|-- Bird
  Animal <|-- Reptile

  class Lion      { +get_diet_type() str }
  class Elephant  { +get_diet_type() str }
  class Monkey    { +get_diet_type() str }
  class Eagle     { +get_diet_type() str }
  class Penguin   { +get_diet_type() str }
  class Crocodile { +get_diet_type() str }

  Mammal  <|-- Lion
  Mammal  <|-- Elephant
  Mammal  <|-- Monkey
  Bird    <|-- Eagle
  Bird    <|-- Penguin
  Reptile <|-- Crocodile

  class Employee {
    <<abstract>>
    +id: str
    +name: str
    +zoo_id: str
    +role() str
    +__repr__()
    +__str__()
    +__eq__()
  }
  class Zookeeper    { }
  class Veterinarian { }
  class Guide        { +is_available: bool }

  Employee <|-- Zookeeper
  Employee <|-- Veterinarian
  Employee <|-- Guide

  class Zoo {
    +id: str
    +name: str
    +tour_route: list
    +__repr__()
    +__str__()
    +__eq__()
  }
  class Enclosure {
    +id: str
    +name: str
    +enclosure_type: EnclosureType
    +zoo_id: str
    +assigned_zookeeper_id: str | None
    +animals: list
    +is_occupied() bool
    +animal_count() int
    +__repr__()
    +__str__()
    +__eq__()
  }
  class FeedingSchedule {
    +id: str
    +enclosure_id: str
    +scheduled_time: time
    +diet: str
    +schedule_info() str
    +__repr__()
    +__str__()
  }
  class AdmissionRecord {
    +id: str
    +date: date
    +animal_id: str
    +enclosure_id: str
    +zookeeper_id: str | None
    +vet_id: str | None
    +health_check_record_id: str | None
    +__repr__()
    +__str__()
  }
  class HealthCheckRecord {
    +id: str
    +date: date
    +animal_id: str
    +vet_id: str
    +result: HealthResult
    +notes: str | None
    +__repr__()
    +__str__()
  }
  class Tour {
    +id: str
    +guide_id: str
    +route: list
    +start_time: datetime
    +end_time: datetime
    +is_completed() bool
    +__repr__()
    +__str__()
  }

  Zoo       "1" *-- "0..*" Enclosure   : composition
  Enclosure "1" o-- "0..*" Animal      : aggregation
  Zoo       "1" o-- "0..*" Employee    : aggregation
  Zookeeper "0..1" -- "0..*" Enclosure : association
```

---

## 4. API Endpoints

| Method | Path | Success |
|--------|------|---------|
| GET | `/animals/{animal_id}` | 200 |
| GET | `/enclosures/{enclosure_id}` | 200 |
| POST | `/enclosures/{enclosure_id}/zookeeper` | 200 |
| POST | `/animals/{animal_id}/admit` | 201 |
| POST | `/enclosures/{enclosure_id}/feeding-rounds` | 200 |
| POST | `/animals/{animal_id}/health-checks` | 201 |
| POST | `/tours` | 201 |

All POST endpoints expect JSON bodies; validation errors and domain rule violations return 422 with `{"detail": "<message>"}`. Not-found entities return 404.

---

## 5. Architecture

The application follows **hexagonal (ports & adapters)** and **Clean Architecture**:

- **Domain** (`zoo_management/domain/`): Entities (Animal/Employee hierarchies, Zoo, Enclosure, records), enums, exceptions, and **repository port** interfaces (ABCs). No FastAPI, Pydantic, or SQLAlchemy.

- **Use cases** (`zoo_management/usecases/`): Application logic (admit animal, assign zookeeper, execute feeding round, conduct health check, conduct guided tour). They depend only on domain and ports; no HTTP or framework imports.

- **Adapters**: **In-memory** (`adapters/in_memory.py`) implements all repository ports with dict-based storage. **Web** (`adapters/web/`) provides FastAPI routers (thin: validate → call use case → map response) and exception handlers (domain exceptions → HTTP status).

- **Infrastructure** (`zoo_management/infrastructure/`): Config, logging, dependency injection (FastAPI `Depends`), and seed data. `main.py` wires the app, seeds the repository once at startup, and serves requests.

Dependencies point inward: adapters and infrastructure depend on domain and use cases; domain and use cases stay free of framework and I/O details. Replacing the in-memory store with a SQL adapter requires only implementing the same ports in a new adapter module.
