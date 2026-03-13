# Phase 0 — Repository Setup & Project Infrastructure

**Goal:** Initialize the repository, install dependencies, configure tooling (linter, type checker, test runner), and establish the project directory structure so all subsequent phases have a working development environment.

**Depends on:** Nothing (first phase).
**Unlocks:** All subsequent phases.

---

## Step 0.1 — Initialize Git Repository ✅

**Action:**
1. Run `git init` in the project root.
2. Create `.gitignore` for Python projects (include `__pycache__/`, `*.pyc`, `.mypy_cache/`, `.ruff_cache/`, `.pytest_cache/`, `*.egg-info/`, `dist/`, `build/`, `.venv/`, `venv/`).
3. Make initial commit: `"chore: initialize repository"`.

**Verification:**
- `git status` shows clean working tree.
- `.gitignore` covers all standard Python artifacts.

---

## Step 0.2 — Create Python Virtual Environment ✅

**Action:**
1. Create a virtual environment: `python3.12 -m venv .venv`.
2. Activate: `source .venv/bin/activate`.
3. Verify: `python --version` outputs `3.12.x`.

**Verification:**
- `.venv/` directory exists.
- `python --version` confirms Python 3.12+.

---

## Step 0.3 — Create Dependency Files ✅

**Action:**

Create `requirements.txt` (production dependencies):
```
fastapi
uvicorn[standard]
```

Create `requirements-dev.txt` (development/test dependencies):
```
-r requirements.txt
pytest
pytest-bdd
httpx
ruff
mypy
```

**Rationale (from architecture.md):**
- FastAPI is the HTTP adapter framework.
- uvicorn is the ASGI server (`uvicorn main:app`).
- pytest + pytest-bdd for unit/integration/BDD tests.
- httpx for integration tests with `ASGITransport` (sync `httpx.Client`, ADR-005).
- ruff for linting, mypy for type checking.
- No `pytest-asyncio` — all tests are sync (ADR-005).
- No SQLAlchemy, asyncpg, alembic, docker — in-memory only (PRD §10 Q1).

**Verification:**
- `pip install -r requirements-dev.txt` succeeds.
- `python -c "import fastapi; import httpx; import pytest"` runs without error.

---

## Step 0.4 — Configure Tooling (pyproject.toml) ✅

**Action:**

Create `pyproject.toml` with ruff and mypy configuration:

```toml
[tool.ruff]
target-version = "py312"
line-length = 100
select = ["E", "F", "W", "I", "N", "UP", "B", "A", "SIM"]
ignore = []

[tool.ruff.isort]
known-first-party = ["zoo_management"]

[tool.mypy]
python_version = "3.12"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[tool.pytest.ini_options]
testpaths = ["tests"]
bdd_features_base_dir = "features/"
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
```

**Verification:**
- `ruff check .` runs (may show no files yet).
- `mypy --version` confirms installation.

---

## Step 0.5 — Create Project Directory Structure ✅

**Action:**

Create the full directory tree (empty `__init__.py` files where needed):

```
zoo_management/
├── __init__.py
├── domain/
│   ├── __init__.py
│   ├── entities.py          # (empty placeholder)
│   └── interfaces.py        # (empty placeholder)
├── usecases/
│   ├── __init__.py
│   ├── assign_zookeeper.py  # (empty placeholder)
│   ├── admit_animal.py      # (empty placeholder)
│   ├── execute_feeding_round.py
│   ├── conduct_health_check.py
│   └── conduct_guided_tour.py
├── adapters/
│   ├── __init__.py
│   ├── in_memory.py         # (empty placeholder)
│   └── web/
│       ├── __init__.py
│       ├── routers.py       # (empty placeholder)
│       └── exception_handlers.py
├── infrastructure/
│   ├── __init__.py
│   ├── config.py            # (empty placeholder)
│   ├── dependencies.py      # (empty placeholder)
│   ├── logging.py           # (empty placeholder)
│   └── seed.py              # (empty placeholder)
tests/
├── __init__.py
├── unit/
│   └── __init__.py
├── integration/
│   └── __init__.py
└── step_defs/
    └── __init__.py
features/
main.py                      # (empty placeholder)
```

**Verification:**
- All directories and `__init__.py` files exist.
- `python -c "import zoo_management"` runs without error.

---

## Step 0.6 — Verify Toolchain End-to-End ✅

**Action:**
1. Create a trivial test in `tests/unit/test_smoke.py`:
   ```python
   def test_smoke() -> None:
       assert 1 + 1 == 2
   ```
2. Run `pytest tests/` — should discover and pass 1 test.
3. Run `ruff check zoo_management/ tests/` — should pass (no source files with issues).
4. Run `mypy zoo_management/` — should pass (empty modules).

**Verification:**
- `pytest` output: `1 passed`.
- `ruff check`: no errors.
- `mypy`: no errors.

---

## Step 0.7 — Commit Phase 0 ✅

**Action:**
1. `git add .`
2. `git commit -m "chore: project structure, dependencies, and tooling"`

**Verification:**
- `git log` shows two commits (init + structure).
- All files tracked.

---

## Phase 0 Completion Checklist

- [x] Git repository initialized with `.gitignore`
- [x] Python 3.12 virtual environment created and activated
- [x] `requirements.txt` and `requirements-dev.txt` created and installed
- [x] `pyproject.toml` with ruff, mypy, pytest configuration
- [x] Full directory structure created (domain, usecases, adapters, infrastructure, tests, features)
- [x] Smoke test passes via pytest
- [x] Linter and type checker pass on empty codebase
- [x] All changes committed

---

**Next phase:** [Phase 1 — Domain Layer Foundation](phase-1-domain-layer.md)
