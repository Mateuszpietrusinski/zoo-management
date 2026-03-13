"""Integration tests for POST /enclosures/{id}/zookeeper (Phase 3)."""

from fastapi.testclient import TestClient

from main import app
from zoo_management.adapters.in_memory import InMemoryRepositories
from zoo_management.domain.entities import (
    Enclosure,
    EnclosureType,
    Guide,
    Zookeeper,
)
from zoo_management.infrastructure.dependencies import (
    get_assign_zookeeper_use_case,
)
from zoo_management.usecases.assign_zookeeper import AssignZookeeperUseCase


def test_assign_zookeeper_returns_200_with_correct_body() -> None:
    """POST with valid enclosure and zookeeper returns 200 and JSON body."""
    repo = InMemoryRepositories()
    enc = Enclosure(
        id="enc-mammal-1",
        name="Mammal House",
        enclosure_type=EnclosureType.MAMMAL,
        zoo_id="zoo-1",
    )
    zk = Zookeeper(id="emp-zk-1", name="Jane", zoo_id="zoo-1")
    repo.save(enc)
    repo.save(zk)

    use_case = AssignZookeeperUseCase(repo, repo)
    app.dependency_overrides[get_assign_zookeeper_use_case] = lambda: use_case
    try:
        with TestClient(app) as client:
            response = client.post(
                "/enclosures/enc-mammal-1/zookeeper",
                json={"zookeeper_id": "emp-zk-1", "zoo_id": "zoo-1"},
            )
        assert response.status_code == 200
        data = response.json()
        assert data["enclosure_id"] == "enc-mammal-1"
        assert data["zookeeper_id"] == "emp-zk-1"
    finally:
        app.dependency_overrides.clear()


def test_assign_zookeeper_returns_404_for_missing_enclosure() -> None:
    """POST with non-existent enclosure_id returns 404."""
    repo = InMemoryRepositories()
    zk = Zookeeper(id="emp-zk-1", name="Jane", zoo_id="zoo-1")
    repo.save(zk)

    app.dependency_overrides[get_assign_zookeeper_use_case] = lambda: AssignZookeeperUseCase(
        repo, repo
    )
    try:
        with TestClient(app) as client:
            response = client.post(
                "/enclosures/missing-enc/zookeeper",
                json={"zookeeper_id": "emp-zk-1", "zoo_id": "zoo-1"},
            )
        assert response.status_code == 404
        assert "detail" in response.json()
    finally:
        app.dependency_overrides.clear()


def test_assign_zookeeper_returns_422_for_invalid_role() -> None:
    """POST with guide id instead of zookeeper returns 422."""
    repo = InMemoryRepositories()
    enc = Enclosure(
        id="enc-mammal-1",
        name="Mammal House",
        enclosure_type=EnclosureType.MAMMAL,
        zoo_id="zoo-1",
    )
    guide = Guide(id="emp-guide-1", name="Alice", zoo_id="zoo-1")
    repo.save(enc)
    repo.save(guide)

    app.dependency_overrides[get_assign_zookeeper_use_case] = lambda: AssignZookeeperUseCase(
        repo, repo
    )
    try:
        with TestClient(app) as client:
            response = client.post(
                "/enclosures/enc-mammal-1/zookeeper",
                json={"zookeeper_id": "emp-guide-1", "zoo_id": "zoo-1"},
            )
        assert response.status_code == 422
        assert "detail" in response.json()
    finally:
        app.dependency_overrides.clear()


def test_assign_zookeeper_returns_422_for_zoo_mismatch() -> None:
    """Enclosure in zoo-1, zookeeper in zoo-2, request zoo-1 -> 422."""
    repo = InMemoryRepositories()
    enc = Enclosure(
        id="enc-mammal-1",
        name="Mammal House",
        enclosure_type=EnclosureType.MAMMAL,
        zoo_id="zoo-1",
    )
    zk = Zookeeper(id="emp-zk-1", name="Jane", zoo_id="zoo-2")
    repo.save(enc)
    repo.save(zk)

    app.dependency_overrides[get_assign_zookeeper_use_case] = lambda: AssignZookeeperUseCase(
        repo, repo
    )
    try:
        with TestClient(app) as client:
            response = client.post(
                "/enclosures/enc-mammal-1/zookeeper",
                json={"zookeeper_id": "emp-zk-1", "zoo_id": "zoo-1"},
            )
        assert response.status_code == 422
        assert "detail" in response.json()
    finally:
        app.dependency_overrides.clear()
