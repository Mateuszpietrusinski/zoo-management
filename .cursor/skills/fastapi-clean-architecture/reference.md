# FastAPI Clean Architecture — Full Reference

This document contains the complete project structure, code samples, and rationale from the production-grade FastAPI Clean Architecture guide.

## Why Clean Architecture with FastAPI

FastAPI's decorators and Pydantic make it easy to put business logic, DB access, and HTTP in one place. That coupling makes swapping ORMs, changing DBs, or unit testing hard. Clean Architecture separates domain, use cases, adapters, and infrastructure so the core stays framework-agnostic.

## Project Structure

```
.
├── domain/
│   ├── entities.py
│   └── interfaces.py
├── usecases/
│   └── register_user.py
├── adapters/
│   ├── database.py
│   ├── security.py
│   └── web/
│       ├── routers.py
│       └── exception_handlers.py
├── infrastructure/
│   ├── config.py
│   ├── database.py
│   ├── db_models.py
│   ├── dependencies.py
│   └── logging.py
├── tests/
│   ├── unit/
│   │   └── test_register_user.py
│   └── integration/
│       └── test_register_user_router.py
├── alembic/
│   └── versions/
├── alembic.ini
├── main.py
└── requirements.txt
```

---

## 1. Configuration Management

All env config is read at startup via Pydantic `BaseSettings`. Validated at launch; fail fast if required vars are missing.

```python
# infrastructure/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    app_name: str = "Clean Architecture API"
    environment: str = "development"
    database_url: str  # e.g. postgresql+asyncpg://user:pass@host/db
    log_level: str = "INFO"

settings = Settings()
```

`.env` (never commit):

```
DATABASE_URL=postgresql+asyncpg://postgres:secret@localhost/appdb
LOG_LEVEL=INFO
ENVIRONMENT=production
```

---

## 2. Structured Logging

JSON logging for aggregators (Datadog, CloudWatch, Loki). Configure once at startup.

```python
# infrastructure/logging.py
import logging
import json
from datetime import datetime, timezone

class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        for key, value in record.__dict__.items():
            if key not in (
                "message", "asctime", "levelname", "name", "msg",
                "args", "exc_info", "exc_text", "stack_info",
                "created", "msecs", "relativeCreated", "thread",
                "threadName", "processName", "process", "levelno",
                "pathname", "filename", "module", "funcName", "lineno",
            ):
                log_entry[key] = value
        return json.dumps(log_entry)

def configure_logging(log_level: str = "INFO") -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    logging.basicConfig(level=log_level, handlers=[handler])
```

---

## 3. Domain Layer

Pure Python: no FastAPI, SQLAlchemy, or Pydantic. Entities are dataclasses; interfaces use `abc`.

```python
# domain/entities.py
from dataclasses import dataclass

@dataclass
class User:
    id: str
    email: str
    password_hash: str
```

```python
# domain/interfaces.py
import abc
from domain.entities import User

class UserRepository(abc.ABC):
    @abc.abstractmethod
    async def get_by_email(self, email: str) -> User | None:
        pass

    @abc.abstractmethod
    async def save(self, user: User) -> None:
        pass

class PasswordHasher(abc.ABC):
    @abc.abstractmethod
    def hash(self, password: str) -> str:
        pass

    @abc.abstractmethod
    def verify(self, plain: str, hashed: str) -> bool:
        pass
```

- Repository methods are async so the stack stays async end-to-end.
- Define the full interface (e.g. `verify` for login) upfront to avoid breaking changes.

---

## 4. Use Case Layer

Business rules only; depends only on domain. Dependencies injected via `__init__`. No `commit` in use case — transaction is the caller’s responsibility (Unit of Work).

```python
# usecases/register_user.py
import logging
import uuid
from dataclasses import dataclass
from domain.entities import User
from domain.interfaces import UserRepository, PasswordHasher

logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class RegisterUserRequest:
    email: str
    password: str

@dataclass(frozen=True)
class RegisterUserResponse:
    id: str
    email: str

class EmailAlreadyExistsError(Exception):
    pass

class RegisterUserUseCase:
    def __init__(self, repo: UserRepository, hasher: PasswordHasher):
        self.repo = repo
        self.hasher = hasher

    async def execute(self, request: RegisterUserRequest) -> RegisterUserResponse:
        logger.info("Attempting user registration", extra={"email": request.email})
        existing = await self.repo.get_by_email(request.email)
        if existing:
            logger.warning("Registration rejected — email already exists", extra={"email": request.email})
            raise EmailAlreadyExistsError(f"Email '{request.email}' is already registered.")
        hashed_password = self.hasher.hash(request.password)
        user = User(
            id=str(uuid.uuid4()),
            email=request.email,
            password_hash=hashed_password,
        )
        await self.repo.save(user)
        logger.info("User registered successfully", extra={"user_id": user.id})
        return RegisterUserResponse(id=user.id, email=user.email)
```

---

## 5. Interface Adapters

### Database Adapter

Adapter receives `AsyncSession` from outside; never commits. Unit of Work is at the request boundary.

```python
# infrastructure/db_models.py
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class UserModel(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
```

```python
# adapters/database.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from domain.entities import User
from domain.interfaces import UserRepository
from infrastructure.db_models import UserModel

class SQLAlchemyUserRepository(UserRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(
            select(UserModel).where(UserModel.email == email)
        )
        db_user = result.scalar_one_or_none()
        if not db_user:
            return None
        return User(id=db_user.id, email=db_user.email, password_hash=db_user.password_hash)

    async def save(self, user: User) -> None:
        db_user = UserModel(
            id=user.id,
            email=user.email,
            password_hash=user.password_hash,
        )
        self.session.add(db_user)
        # No commit — Unit of Work manages commit externally
```

### Security Adapter

```python
# adapters/security.py
from passlib.context import CryptContext
from domain.interfaces import PasswordHasher

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class BcryptPasswordHasher(PasswordHasher):
    def hash(self, password: str) -> str:
        return _pwd_context.hash(password)

    def verify(self, plain: str, hashed: str) -> bool:
        return _pwd_context.verify(plain, hashed)
```

### Web Adapter — Routers and Validation

Pydantic at the HTTP boundary; map to use-case request/response. Use `EmailStr` and `Field` for validation.

```python
# adapters/web/routers.py
import logging
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, EmailStr, Field
from usecases.register_user import (
    RegisterUserUseCase,
    RegisterUserRequest,
    EmailAlreadyExistsError,
)
from infrastructure.dependencies import get_register_use_case

router = APIRouter(prefix="/users", tags=["users"])
logger = logging.getLogger(__name__)

class CreateUserAPIRequest(BaseModel):
    email: EmailStr
    password: str = Field(
        min_length=8,
        max_length=128,
        description="Password must be between 8 and 128 characters.",
    )

class CreateUserAPIResponse(BaseModel):
    id: str
    email: str

@router.post(
    "",
    response_model=CreateUserAPIResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
async def register_user(
    request: CreateUserAPIRequest,
    use_case: RegisterUserUseCase = Depends(get_register_use_case),
) -> CreateUserAPIResponse:
    uc_request = RegisterUserRequest(email=request.email, password=request.password)
    result = await use_case.execute(uc_request)
    return CreateUserAPIResponse(id=result.id, email=result.email)
```

### Global Exception Handlers

Single place for error shape; domain and validation errors mapped to HTTP status.

```python
# adapters/web/exception_handlers.py
import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from usecases.register_user import EmailAlreadyExistsError

logger = logging.getLogger(__name__)

def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(EmailAlreadyExistsError)
    async def email_exists_handler(request: Request, exc: EmailAlreadyExistsError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": str(exc)},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": exc.errors()},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(
            "Unhandled exception",
            extra={"path": request.url.path, "method": request.method},
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An unexpected error occurred. Please try again later."},
        )
```

---

## 6. Infrastructure Layer

### Async Database Session (Unit of Work)

Commit once per request in the dependency; rollback on exception. Repositories do not commit.

```python
# infrastructure/database.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from infrastructure.config import settings

engine = create_async_engine(
    settings.database_url,
    pool_size=10,
    max_overflow=20,
    echo=(settings.environment == "development"),
)
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

async def get_db_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

### Dependency Injection

```python
# infrastructure/dependencies.py
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from infrastructure.database import get_db_session
from adapters.database import SQLAlchemyUserRepository
from adapters.security import BcryptPasswordHasher
from usecases.register_user import RegisterUserUseCase

def get_password_hasher() -> BcryptPasswordHasher:
    return BcryptPasswordHasher()

async def get_user_repository(
    session: AsyncSession = Depends(get_db_session),
) -> SQLAlchemyUserRepository:
    return SQLAlchemyUserRepository(session)

async def get_register_use_case(
    repo: SQLAlchemyUserRepository = Depends(get_user_repository),
    hasher: BcryptPasswordHasher = Depends(get_password_hasher),
) -> RegisterUserUseCase:
    return RegisterUserUseCase(repo=repo, hasher=hasher)
```

---

## 7. Alembic Migrations

Version schema; no manual `CREATE TABLE` or `create_all()` in production.

- `alembic init alembic`
- In `alembic/env.py`: set `sqlalchemy.url` from settings, `target_metadata = Base.metadata`
- `alembic revision --autogenerate -m "create users table"`
- `alembic upgrade head`

---

## 8. Application Entry Point

Thin `main.py`: wire app, logging, routers, exception handlers.

```python
# main.py
from fastapi import FastAPI
from infrastructure.config import settings
from infrastructure.logging import configure_logging
from adapters.web.routers import router as user_router
from adapters.web.exception_handlers import register_exception_handlers

configure_logging(settings.log_level)
app = FastAPI(title=settings.app_name)
register_exception_handlers(app)
app.include_router(user_router)
```

---

## 9. Testing

### Unit Tests — Use Case Only

In-memory fakes (real implementations, not mocks) for repositories and hasher. No DB, no HTTP.

```python
# tests/unit/test_register_user.py
import pytest
from domain.entities import User
from domain.interfaces import UserRepository, PasswordHasher
from usecases.register_user import (
    RegisterUserUseCase,
    RegisterUserRequest,
    RegisterUserResponse,
    EmailAlreadyExistsError,
)

class InMemoryUserRepository(UserRepository):
    def __init__(self):
        self._store: dict[str, User] = {}

    async def get_by_email(self, email: str) -> User | None:
        return next((u for u in self._store.values() if u.email == email), None)

    async def save(self, user: User) -> None:
        self._store[user.id] = user

class FakePasswordHasher(PasswordHasher):
    def hash(self, password: str) -> str:
        return f"hashed:{password}"

    def verify(self, plain: str, hashed: str) -> bool:
        return hashed == f"hashed:{plain}"

@pytest.fixture
def repo():
    return InMemoryUserRepository()

@pytest.fixture
def hasher():
    return FakePasswordHasher()

@pytest.fixture
def use_case(repo, hasher):
    return RegisterUserUseCase(repo=repo, hasher=hasher)

@pytest.mark.asyncio
async def test_registers_new_user_successfully(use_case, repo):
    request = RegisterUserRequest(email="alice@example.com", password="securepassword")
    result = await use_case.execute(request)
    assert isinstance(result, RegisterUserResponse)
    assert result.email == "alice@example.com"
    assert result.id is not None
    saved = await repo.get_by_email("alice@example.com")
    assert saved is not None
    assert saved.password_hash == "hashed:securepassword"

@pytest.mark.asyncio
async def test_raises_error_when_email_already_exists(use_case):
    request = RegisterUserRequest(email="alice@example.com", password="securepassword")
    await use_case.execute(request)
    with pytest.raises(EmailAlreadyExistsError):
        await use_case.execute(request)

@pytest.mark.asyncio
async def test_hashes_password_before_storing(use_case, repo):
    request = RegisterUserRequest(email="bob@example.com", password="mypassword")
    await use_case.execute(request)
    saved = await repo.get_by_email("bob@example.com")
    assert saved.password_hash != "mypassword"
    assert saved.password_hash == "hashed:mypassword"
```

### Integration Tests — HTTP Layer

Real FastAPI app and router; override use-case dependency with same fakes. No real DB.

```python
# tests/integration/test_register_user_router.py
import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
from adapters.web.routers import router as user_router
from adapters.web.exception_handlers import register_exception_handlers
from usecases.register_user import RegisterUserUseCase
from tests.unit.test_register_user import InMemoryUserRepository, FakePasswordHasher
from infrastructure.dependencies import get_register_use_case

def create_test_app() -> FastAPI:
    test_repo = InMemoryUserRepository()
    test_hasher = FakePasswordHasher()

    def override_use_case() -> RegisterUserUseCase:
        return RegisterUserUseCase(repo=test_repo, hasher=test_hasher)

    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(user_router)
    app.dependency_overrides[get_register_use_case] = override_use_case
    return app

@pytest.fixture
def test_app():
    return create_test_app()

@pytest.fixture
async def client(test_app):
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as c:
        yield c

@pytest.mark.asyncio
async def test_post_users_returns_201_on_success(client):
    response = await client.post("/users", json={"email": "alice@example.com", "password": "securepassword"})
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "alice@example.com"
    assert "id" in body
    assert "password" not in body

@pytest.mark.asyncio
async def test_post_users_returns_409_on_duplicate_email(client):
    payload = {"email": "alice@example.com", "password": "securepassword"}
    await client.post("/users", json=payload)
    response = await client.post("/users", json=payload)
    assert response.status_code == 409
    assert "already registered" in response.json()["detail"]

@pytest.mark.asyncio
async def test_post_users_returns_422_on_invalid_email(client):
    response = await client.post("/users", json={"email": "not-an-email", "password": "securepassword"})
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_post_users_returns_422_on_short_password(client):
    response = await client.post("/users", json={"email": "alice@example.com", "password": "short"})
    assert response.status_code == 422
```

---

## 10. Requirements

```text
# requirements.txt
fastapi>=0.111.0
uvicorn[standard]>=0.29.0
pydantic[email]>=2.7.0
pydantic-settings>=2.2.0
sqlalchemy[asyncio]>=2.0.0
asyncpg>=0.29.0
passlib[bcrypt]>=1.7.4
alembic>=1.13.0
# dev/test
pytest>=8.0.0
pytest-asyncio>=0.23.0
httpx>=0.27.0
```

---

## Summary: Production-Grade Checklist

- **Async end-to-end**: session, repository, use case, route handler.
- **Unit of Work**: single commit at request boundary in `get_db_session`; repositories never commit.
- **Full interfaces**: e.g. `PasswordHasher` defines both `hash` and `verify`.
- **Validation at boundary**: Pydantic in routers; use case receives validated DTOs.
- **Global exception handlers**: consistent JSON error shape.
- **Structured logging**: JSON formatter; use case logs with `extra={}`.
- **Config at startup**: Pydantic Settings; fail fast on missing env.
- **Migrations**: Alembic; no manual schema or `create_all()` in production.
- **Two test layers**: unit tests with fakes (no DB); integration tests with dependency overrides (no DB).
- **Framework-agnostic core**: `domain/` and `usecases/` have no FastAPI/SQLAlchemy imports.
