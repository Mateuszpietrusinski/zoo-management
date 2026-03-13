"""Smoke tests: fully assembled app with seed data, no dependency overrides (Phase 8.6)."""

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_get_seeded_animal_returns_200() -> None:
    """GET /animals/animal-lion-1 returns 200 and AnimalResponse with seed data."""
    response = client.get("/animals/animal-lion-1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "animal-lion-1"
    assert data["name"] == "Simba"
    assert data["enclosure_id"] == "enc-mammal-1"
    assert data["type_name"] == "Lion"
    assert "diet_type" in data


def test_get_seeded_enclosure_returns_200() -> None:
    """GET /enclosures/enc-mammal-1 returns 200 and EnclosureResponse with seed data."""
    response = client.get("/enclosures/enc-mammal-1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "enc-mammal-1"
    assert data["name"] == "Mammal Enclosure"
    assert data["zoo_id"] == "zoo-1"
    assert data["assigned_zookeeper_id"] == "emp-zk-1"
    assert "animal_ids" in data
    assert "animal-lion-1" in data["animal_ids"]


def test_assign_zookeeper_with_seed_data() -> None:
    """POST assign zookeeper with seed enclosure and zookeeper returns 200."""
    response = client.post(
        "/enclosures/enc-reptile-1/zookeeper",
        json={"zookeeper_id": "emp-zk-1", "zoo_id": "zoo-1"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["enclosure_id"] == "enc-reptile-1"
    assert data["zookeeper_id"] == "emp-zk-1"


def test_admit_unplaced_penguin_with_seed_data() -> None:
    """POST admit animal for seeded unplaced penguin returns 201 and places in bird enclosure."""
    response = client.post(
        "/animals/animal-penguin-1/admit",
        json={"zoo_id": "zoo-1"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["animal_id"] == "animal-penguin-1"
    assert data["enclosure_id"] == "enc-bird-1"
    assert "admission_record_id" in data


def test_feeding_round_with_seed_data_at_scheduled_time() -> None:
    """POST feeding round at 09:00 for enc-mammal-1 with emp-zk-1 returns 200 and fed_count."""
    response = client.post(
        "/enclosures/enc-mammal-1/feeding-rounds",
        json={"zookeeper_id": "emp-zk-1", "current_time": "09:00:00"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["enclosure_id"] == "enc-mammal-1"
    assert data["fed_count"] >= 0
    assert "note" in data


def test_health_check_with_seed_data() -> None:
    """POST health check for seeded lion with Dr. Bob returns 201."""
    response = client.post(
        "/animals/animal-lion-1/health-checks",
        json={"vet_id": "emp-vet-1", "result": "healthy", "notes": None},
    )
    assert response.status_code == 201
    data = response.json()
    assert "health_check_record_id" in data
    assert data["result"] == "healthy"


def test_guided_tour_with_seed_data() -> None:
    """POST guided tour with seeded guide and zoo returns 201 and tour with route."""
    response = client.post(
        "/tours",
        json={"guide_id": "emp-guide-1", "zoo_id": "zoo-1"},
    )
    assert response.status_code == 201
    data = response.json()
    assert "tour_id" in data
    assert data["route"] == ["enc-mammal-1", "enc-bird-1", "enc-reptile-1"]
    assert "start_time" in data
    assert "end_time" in data
