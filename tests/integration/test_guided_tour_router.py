"""Integration tests for POST /tours (Phase 7)."""

from fastapi.testclient import TestClient

from main import app
from zoo_management.adapters.in_memory import InMemoryRepositories
from zoo_management.domain.entities import (
    Enclosure,
    EnclosureType,
    Guide,
    Zoo,
    Zookeeper,
)
from zoo_management.infrastructure.dependencies import (
    get_conduct_guided_tour_use_case,
)
from zoo_management.usecases.conduct_guided_tour import (
    ConductGuidedTourUseCase,
)


def test_guided_tour_returns_201_with_tour_details() -> None:
    """POST /tours with guide_id, zoo_id -> 201, body has tour_id, route, start_time, end_time."""
    repo = InMemoryRepositories()
    guide = Guide(id="emp-guide-1", name="Eve", zoo_id="zoo-1", is_available=True)
    zoo = Zoo(id="zoo-1", name="Main", tour_route=["enc-1", "enc-2"])
    repo.seed_zoo(zoo)
    repo.save(guide)
    repo.save(
        Enclosure(id="enc-1", name="M", enclosure_type=EnclosureType.MAMMAL, zoo_id="zoo-1")
    )
    repo.save(
        Enclosure(id="enc-2", name="B", enclosure_type=EnclosureType.BIRD, zoo_id="zoo-1")
    )

    use_case = ConductGuidedTourUseCase(repo, repo, repo, repo)
    app.dependency_overrides[get_conduct_guided_tour_use_case] = lambda: use_case
    try:
        with TestClient(app) as client:
            response = client.post(
                "/tours",
                json={"guide_id": "emp-guide-1", "zoo_id": "zoo-1"},
            )
        assert response.status_code == 201
        data = response.json()
        assert "tour_id" in data
        assert data["route"] == ["enc-1", "enc-2"]
        assert "start_time" in data
        assert "end_time" in data
    finally:
        app.dependency_overrides.clear()


def test_guided_tour_returns_422_for_unavailable_guide() -> None:
    """POST with Guide(is_available=False) -> 422."""
    repo = InMemoryRepositories()
    guide = Guide(id="g1", name="Eve", zoo_id="zoo-1", is_available=False)
    zoo = Zoo(id="zoo-1", name="Z", tour_route=["enc-1"])
    repo.seed_zoo(zoo)
    repo.save(guide)
    repo.save(
        Enclosure(id="enc-1", name="M", enclosure_type=EnclosureType.MAMMAL, zoo_id="zoo-1")
    )

    use_case = ConductGuidedTourUseCase(repo, repo, repo, repo)
    app.dependency_overrides[get_conduct_guided_tour_use_case] = lambda: use_case
    try:
        with TestClient(app) as client:
            response = client.post(
                "/tours",
                json={"guide_id": "g1", "zoo_id": "zoo-1"},
            )
        assert response.status_code == 422
        assert "detail" in response.json()
    finally:
        app.dependency_overrides.clear()


def test_guided_tour_returns_422_for_guide_not_in_zoo() -> None:
    """Guide in other zoo -> 422."""
    repo = InMemoryRepositories()
    guide = Guide(id="g1", name="Eve", zoo_id="zoo-other", is_available=True)
    zoo = Zoo(id="zoo-1", name="Z", tour_route=["enc-1"])
    repo.seed_zoo(zoo)
    repo.save(guide)
    repo.save(
        Enclosure(id="enc-1", name="M", enclosure_type=EnclosureType.MAMMAL, zoo_id="zoo-1")
    )

    use_case = ConductGuidedTourUseCase(repo, repo, repo, repo)
    app.dependency_overrides[get_conduct_guided_tour_use_case] = lambda: use_case
    try:
        with TestClient(app) as client:
            response = client.post(
                "/tours",
                json={"guide_id": "g1", "zoo_id": "zoo-1"},
            )
        assert response.status_code == 422
        assert "detail" in response.json()
    finally:
        app.dependency_overrides.clear()


def test_guided_tour_returns_422_for_non_guide_role() -> None:
    """Zookeeper as guide_id -> 422."""
    repo = InMemoryRepositories()
    zk = Zookeeper(id="emp-zk-1", name="Jane", zoo_id="zoo-1")
    zoo = Zoo(id="zoo-1", name="Z", tour_route=["enc-1"])
    repo.seed_zoo(zoo)
    repo.save(zk)
    repo.save(
        Enclosure(id="enc-1", name="M", enclosure_type=EnclosureType.MAMMAL, zoo_id="zoo-1")
    )

    use_case = ConductGuidedTourUseCase(repo, repo, repo, repo)
    app.dependency_overrides[get_conduct_guided_tour_use_case] = lambda: use_case
    try:
        with TestClient(app) as client:
            response = client.post(
                "/tours",
                json={"guide_id": "emp-zk-1", "zoo_id": "zoo-1"},
            )
        assert response.status_code == 422
        assert "detail" in response.json()
    finally:
        app.dependency_overrides.clear()


def test_guided_tour_returns_404_for_missing_guide() -> None:
    """POST with non-existent guide_id -> 404."""
    repo = InMemoryRepositories()
    zoo = Zoo(id="zoo-1", name="Z", tour_route=[])
    repo.seed_zoo(zoo)

    use_case = ConductGuidedTourUseCase(repo, repo, repo, repo)
    app.dependency_overrides[get_conduct_guided_tour_use_case] = lambda: use_case
    try:
        with TestClient(app) as client:
            response = client.post(
                "/tours",
                json={"guide_id": "missing-guide", "zoo_id": "zoo-1"},
            )
        assert response.status_code == 404
        assert "detail" in response.json()
    finally:
        app.dependency_overrides.clear()


def test_consecutive_tours_second_fails_with_same_guide() -> None:
    """First POST 201, second POST with same guide -> 422 NoGuideAvailableError."""
    repo = InMemoryRepositories()
    guide = Guide(id="g1", name="Eve", zoo_id="zoo-1", is_available=True)
    zoo = Zoo(id="zoo-1", name="Z", tour_route=["enc-1"])
    repo.seed_zoo(zoo)
    repo.save(guide)
    repo.save(
        Enclosure(id="enc-1", name="M", enclosure_type=EnclosureType.MAMMAL, zoo_id="zoo-1")
    )

    use_case = ConductGuidedTourUseCase(repo, repo, repo, repo)
    app.dependency_overrides[get_conduct_guided_tour_use_case] = lambda: use_case
    try:
        with TestClient(app) as client:
            first = client.post(
                "/tours",
                json={"guide_id": "g1", "zoo_id": "zoo-1"},
            )
            assert first.status_code == 201
            second = client.post(
                "/tours",
                json={"guide_id": "g1", "zoo_id": "zoo-1"},
            )
            assert second.status_code == 422
            assert "detail" in second.json()
    finally:
        app.dependency_overrides.clear()
