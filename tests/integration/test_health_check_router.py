"""Integration tests for POST /animals/{id}/health-checks (Phase 6)."""

from fastapi.testclient import TestClient

from main import app
from zoo_management.adapters.in_memory import InMemoryRepositories
from zoo_management.domain.entities import (
    Lion,
    Origin,
    Veterinarian,
    Zookeeper,
)
from zoo_management.infrastructure.dependencies import (
    get_conduct_health_check_use_case,
)
from zoo_management.usecases.conduct_health_check import (
    ConductHealthCheckUseCase,
)


def test_health_check_returns_201_with_record_id() -> None:
    """POST with vet_id and result 'healthy' -> 201, body has health_check_record_id and result."""
    repo = InMemoryRepositories()
    lion = Lion(
        id="animal-lion-1",
        name="Leo",
        origin=Origin.INTERNAL,
        enclosure_id=None,
    )
    vet = Veterinarian(id="emp-vet-1", name="Dr. Bob", zoo_id="zoo-1")
    repo.save(lion)
    repo.save(vet)

    use_case = ConductHealthCheckUseCase(repo, repo, repo)
    app.dependency_overrides[get_conduct_health_check_use_case] = lambda: use_case
    try:
        with TestClient(app) as client:
            response = client.post(
                "/animals/animal-lion-1/health-checks",
                json={"vet_id": "emp-vet-1", "result": "healthy"},
            )
        assert response.status_code == 201
        data = response.json()
        assert "health_check_record_id" in data
        assert data["result"] == "healthy"
    finally:
        app.dependency_overrides.clear()


def test_health_check_with_notes_returns_201() -> None:
    """POST with notes='observation' -> 201."""
    repo = InMemoryRepositories()
    lion = Lion(
        id="animal-lion-1",
        name="Leo",
        origin=Origin.INTERNAL,
        enclosure_id=None,
    )
    vet = Veterinarian(id="emp-vet-1", name="Dr. Bob", zoo_id="zoo-1")
    repo.save(lion)
    repo.save(vet)

    use_case = ConductHealthCheckUseCase(repo, repo, repo)
    app.dependency_overrides[get_conduct_health_check_use_case] = lambda: use_case
    try:
        with TestClient(app) as client:
            response = client.post(
                "/animals/animal-lion-1/health-checks",
                json={
                    "vet_id": "emp-vet-1",
                    "result": "healthy",
                    "notes": "observation",
                },
            )
        assert response.status_code == 201
        data = response.json()
        assert data["result"] == "healthy"
    finally:
        app.dependency_overrides.clear()


def test_health_check_returns_404_for_missing_animal() -> None:
    """POST for non-existent animal -> 404."""
    repo = InMemoryRepositories()
    vet = Veterinarian(id="emp-vet-1", name="Dr. Bob", zoo_id="zoo-1")
    repo.save(vet)

    use_case = ConductHealthCheckUseCase(repo, repo, repo)
    app.dependency_overrides[get_conduct_health_check_use_case] = lambda: use_case
    try:
        with TestClient(app) as client:
            response = client.post(
                "/animals/missing-animal/health-checks",
                json={"vet_id": "emp-vet-1", "result": "healthy"},
            )
        assert response.status_code == 404
        assert "detail" in response.json()
    finally:
        app.dependency_overrides.clear()


def test_health_check_returns_422_for_non_vet_role() -> None:
    """POST with zookeeper as vet_id -> 422 InvalidEmployeeRoleError."""
    repo = InMemoryRepositories()
    lion = Lion(
        id="animal-lion-1",
        name="Leo",
        origin=Origin.INTERNAL,
        enclosure_id=None,
    )
    zk = Zookeeper(id="emp-zk-1", name="Jane", zoo_id="zoo-1")
    repo.save(lion)
    repo.save(zk)

    use_case = ConductHealthCheckUseCase(repo, repo, repo)
    app.dependency_overrides[get_conduct_health_check_use_case] = lambda: use_case
    try:
        with TestClient(app) as client:
            response = client.post(
                "/animals/animal-lion-1/health-checks",
                json={"vet_id": "emp-zk-1", "result": "healthy"},
            )
        assert response.status_code == 422
        assert "detail" in response.json()
    finally:
        app.dependency_overrides.clear()


def test_health_check_critical_returns_201() -> None:
    """POST with result 'critical' -> 201 (all results valid)."""
    repo = InMemoryRepositories()
    lion = Lion(
        id="animal-lion-1",
        name="Leo",
        origin=Origin.INTERNAL,
        enclosure_id=None,
    )
    vet = Veterinarian(id="emp-vet-1", name="Dr. Bob", zoo_id="zoo-1")
    repo.save(lion)
    repo.save(vet)

    use_case = ConductHealthCheckUseCase(repo, repo, repo)
    app.dependency_overrides[get_conduct_health_check_use_case] = lambda: use_case
    try:
        with TestClient(app) as client:
            response = client.post(
                "/animals/animal-lion-1/health-checks",
                json={"vet_id": "emp-vet-1", "result": "critical"},
            )
        assert response.status_code == 201
        data = response.json()
        assert data["result"] == "critical"
        assert "health_check_record_id" in data
    finally:
        app.dependency_overrides.clear()
