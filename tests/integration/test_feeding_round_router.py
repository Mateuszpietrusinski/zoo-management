"""Integration tests for POST /enclosures/{id}/feeding-rounds (Phase 5)."""

from datetime import time

from fastapi.testclient import TestClient

from main import app
from zoo_management.adapters.in_memory import InMemoryRepositories
from zoo_management.domain.entities import (
    Enclosure,
    EnclosureType,
    FeedingSchedule,
    Lion,
    Origin,
    Veterinarian,
    Zookeeper,
)
from zoo_management.infrastructure.dependencies import (
    get_execute_feeding_round_use_case,
)
from zoo_management.usecases.execute_feeding_round import (
    ExecuteFeedingRoundUseCase,
)


def test_feeding_round_returns_200_with_fed_count_and_note() -> None:
    """POST with valid data returns 200 and body has enclosure_id, fed_count, note."""
    repo = InMemoryRepositories()
    lion = Lion(
        id="animal-lion-1",
        name="Leo",
        origin=Origin.INTERNAL,
        enclosure_id="enc-mammal-1",
    )
    enc = Enclosure(
        id="enc-mammal-1",
        name="Mammal House",
        enclosure_type=EnclosureType.MAMMAL,
        zoo_id="zoo-1",
        assigned_zookeeper_id="emp-zk-1",
        animals=[lion],
    )
    zk = Zookeeper(id="emp-zk-1", name="Jane", zoo_id="zoo-1")
    schedule = FeedingSchedule(
        id="sched-1",
        enclosure_id="enc-mammal-1",
        scheduled_time=time(9, 0, 0),
        diet="meat",
    )
    repo.save(enc)
    repo.save(lion)
    repo.save(zk)
    repo.save(schedule)

    use_case = ExecuteFeedingRoundUseCase(repo, repo, repo)
    app.dependency_overrides[get_execute_feeding_round_use_case] = lambda: use_case
    try:
        with TestClient(app) as client:
            response = client.post(
                "/enclosures/enc-mammal-1/feeding-rounds",
                json={"zookeeper_id": "emp-zk-1", "current_time": "09:00:00"},
            )
        assert response.status_code == 200
        data = response.json()
        assert data["enclosure_id"] == "enc-mammal-1"
        assert data["fed_count"] == 1
        assert "note" in data
        assert "Fed 1 animals" in data["note"]
    finally:
        app.dependency_overrides.clear()


def test_feeding_round_returns_422_for_time_mismatch() -> None:
    """Schedule at 09:00, request 10:00 -> 422 FeedingNotDueError."""
    repo = InMemoryRepositories()
    schedule = FeedingSchedule(
        id="sched-1",
        enclosure_id="enc-mammal-1",
        scheduled_time=time(9, 0, 0),
        diet="meat",
    )
    repo.save(schedule)

    use_case = ExecuteFeedingRoundUseCase(repo, repo, repo)
    app.dependency_overrides[get_execute_feeding_round_use_case] = lambda: use_case
    try:
        with TestClient(app) as client:
            response = client.post(
                "/enclosures/enc-mammal-1/feeding-rounds",
                json={"zookeeper_id": "emp-zk-1", "current_time": "10:00:00"},
            )
        assert response.status_code == 422
        assert "detail" in response.json()
    finally:
        app.dependency_overrides.clear()


def test_feeding_round_returns_422_for_unassigned_zookeeper() -> None:
    """Enclosure has other zookeeper assigned; request from emp-zk-1 -> 422."""
    repo = InMemoryRepositories()
    enc = Enclosure(
        id="enc-mammal-1",
        name="Mammal House",
        enclosure_type=EnclosureType.MAMMAL,
        zoo_id="zoo-1",
        assigned_zookeeper_id="emp-zk-other",
        animals=[],
    )
    zk = Zookeeper(id="emp-zk-1", name="Jane", zoo_id="zoo-1")
    schedule = FeedingSchedule(
        id="sched-1",
        enclosure_id="enc-mammal-1",
        scheduled_time=time(9, 0, 0),
        diet="meat",
    )
    repo.save(enc)
    repo.save(zk)
    repo.save(schedule)

    use_case = ExecuteFeedingRoundUseCase(repo, repo, repo)
    app.dependency_overrides[get_execute_feeding_round_use_case] = lambda: use_case
    try:
        with TestClient(app) as client:
            response = client.post(
                "/enclosures/enc-mammal-1/feeding-rounds",
                json={"zookeeper_id": "emp-zk-1", "current_time": "09:00:00"},
            )
        assert response.status_code == 422
        assert "detail" in response.json()
    finally:
        app.dependency_overrides.clear()


def test_feeding_round_returns_422_for_nonexistent_enclosure() -> None:
    """No schedule for enclosure -> 422 FeedingNotDueError (ADR-029), not 404."""
    repo = InMemoryRepositories()
    use_case = ExecuteFeedingRoundUseCase(repo, repo, repo)
    app.dependency_overrides[get_execute_feeding_round_use_case] = lambda: use_case
    try:
        with TestClient(app) as client:
            response = client.post(
                "/enclosures/enc-nonexistent/feeding-rounds",
                json={"zookeeper_id": "emp-zk-1", "current_time": "09:00:00"},
            )
        assert response.status_code == 422
        assert "detail" in response.json()
    finally:
        app.dependency_overrides.clear()


def test_feeding_round_returns_422_for_non_zookeeper_role() -> None:
    """Veterinarian id as zookeeper_id -> 422."""
    repo = InMemoryRepositories()
    enc = Enclosure(
        id="enc-mammal-1",
        name="Mammal House",
        enclosure_type=EnclosureType.MAMMAL,
        zoo_id="zoo-1",
        assigned_zookeeper_id="emp-vet-1",
        animals=[],
    )
    vet = Veterinarian(id="emp-vet-1", name="Doc", zoo_id="zoo-1")
    schedule = FeedingSchedule(
        id="sched-1",
        enclosure_id="enc-mammal-1",
        scheduled_time=time(9, 0, 0),
        diet="meat",
    )
    repo.save(enc)
    repo.save(vet)
    repo.save(schedule)
    use_case = ExecuteFeedingRoundUseCase(repo, repo, repo)
    app.dependency_overrides[get_execute_feeding_round_use_case] = lambda: use_case
    try:
        with TestClient(app) as client:
            response = client.post(
                "/enclosures/enc-mammal-1/feeding-rounds",
                json={"zookeeper_id": "emp-vet-1", "current_time": "09:00:00"},
            )
        assert response.status_code == 422
        assert "detail" in response.json()
    finally:
        app.dependency_overrides.clear()
