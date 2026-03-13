"""Integration tests for POST /animals/{id}/admit and GET /animals, GET /enclosures (Phase 4)."""

from fastapi.testclient import TestClient

from main import app
from zoo_management.adapters.in_memory import InMemoryRepositories
from zoo_management.domain.entities import (
    Enclosure,
    EnclosureType,
    Lion,
    Origin,
    Penguin,
    Veterinarian,
)
from zoo_management.infrastructure.dependencies import get_admit_animal_use_case
from zoo_management.usecases.admit_animal import AdmitAnimalUseCase


def test_admit_internal_animal_returns_201() -> None:
    """POST admit with zoo_id returns 201; body has animal_id, enclosure_id, admission_record_id."""
    repo = InMemoryRepositories()
    lion = Lion(id="animal-lion-1", name="Leo", origin=Origin.INTERNAL, enclosure_id=None)
    enc = Enclosure(
        id="enc-mammal-1",
        name="Mammal House",
        enclosure_type=EnclosureType.MAMMAL,
        zoo_id="zoo-1",
    )
    repo.save(lion)
    repo.save(enc)

    app.dependency_overrides[get_admit_animal_use_case] = lambda: AdmitAnimalUseCase(
        repo, repo, repo, repo, repo
    )
    try:
        with TestClient(app) as client:
            response = client.post(
                "/animals/animal-lion-1/admit",
                json={"zoo_id": "zoo-1"},
            )
        assert response.status_code == 201
        data = response.json()
        assert data["animal_id"] == "animal-lion-1"
        assert data["enclosure_id"] == "enc-mammal-1"
        assert "admission_record_id" in data
    finally:
        app.dependency_overrides.clear()


def test_admit_external_animal_returns_201_with_health_check() -> None:
    """POST with zoo_id, vet_id, health_check_result healthy returns 201."""
    repo = InMemoryRepositories()
    penguin = Penguin(
        id="animal-penguin-ext", name="Pingu", origin=Origin.EXTERNAL, enclosure_id=None
    )
    enc = Enclosure(
        id="enc-bird-1",
        name="Bird House",
        enclosure_type=EnclosureType.BIRD,
        zoo_id="zoo-1",
    )
    vet = Veterinarian(id="emp-vet-1", name="Dr. Bob", zoo_id="zoo-1")
    repo.save(penguin)
    repo.save(enc)
    repo.save(vet)

    app.dependency_overrides[get_admit_animal_use_case] = lambda: AdmitAnimalUseCase(
        repo, repo, repo, repo, repo
    )
    try:
        with TestClient(app) as client:
            response = client.post(
                "/animals/animal-penguin-ext/admit",
                json={
                    "zoo_id": "zoo-1",
                    "vet_id": "emp-vet-1",
                    "health_check_result": "healthy",
                },
            )
        assert response.status_code == 201
        data = response.json()
        assert data["animal_id"] == "animal-penguin-ext"
        assert data["enclosure_id"] == "enc-bird-1"
    finally:
        app.dependency_overrides.clear()


def test_admit_returns_404_for_missing_animal() -> None:
    """POST /animals/nonexistent/admit returns 404."""
    repo = InMemoryRepositories()
    app.dependency_overrides[get_admit_animal_use_case] = lambda: AdmitAnimalUseCase(
        repo, repo, repo, repo, repo
    )
    try:
        with TestClient(app) as client:
            response = client.post(
                "/animals/nonexistent/admit",
                json={"zoo_id": "zoo-1"},
            )
        assert response.status_code == 404
        assert "detail" in response.json()
    finally:
        app.dependency_overrides.clear()


def test_admit_returns_422_for_already_placed_animal() -> None:
    """Animal already in enclosure -> 422."""
    repo = InMemoryRepositories()
    lion = Lion(
        id="animal-lion-placed",
        name="Leo",
        origin=Origin.INTERNAL,
        enclosure_id="enc-mammal-1",
    )
    enc = Enclosure(
        id="enc-mammal-1",
        name="Mammal House",
        enclosure_type=EnclosureType.MAMMAL,
        zoo_id="zoo-1",
    )
    enc.animals.append(lion)
    repo.save(lion)
    repo.save(enc)

    app.dependency_overrides[get_admit_animal_use_case] = lambda: AdmitAnimalUseCase(
        repo, repo, repo, repo, repo
    )
    try:
        with TestClient(app) as client:
            response = client.post(
                "/animals/animal-lion-placed/admit",
                json={"zoo_id": "zoo-1"},
            )
        assert response.status_code == 422
        assert "detail" in response.json()
    finally:
        app.dependency_overrides.clear()


def test_admit_returns_422_for_health_check_not_cleared() -> None:
    """External animal with result critical -> 422."""
    repo = InMemoryRepositories()
    lion = Lion(
        id="animal-lion-ext", name="Scar", origin=Origin.EXTERNAL, enclosure_id=None
    )
    enc = Enclosure(
        id="enc-mammal-1",
        name="Mammal House",
        enclosure_type=EnclosureType.MAMMAL,
        zoo_id="zoo-1",
    )
    vet = Veterinarian(id="emp-vet-1", name="Dr. Bob", zoo_id="zoo-1")
    repo.save(lion)
    repo.save(enc)
    repo.save(vet)

    app.dependency_overrides[get_admit_animal_use_case] = lambda: AdmitAnimalUseCase(
        repo, repo, repo, repo, repo
    )
    try:
        with TestClient(app) as client:
            response = client.post(
                "/animals/animal-lion-ext/admit",
                json={
                    "zoo_id": "zoo-1",
                    "vet_id": "emp-vet-1",
                    "health_check_result": "critical",
                },
            )
        assert response.status_code == 422
        assert "detail" in response.json()
    finally:
        app.dependency_overrides.clear()


def test_admit_returns_422_for_no_suitable_enclosure() -> None:
    """Reptile with only mammal enclosures -> 422."""
    from zoo_management.domain.entities import Crocodile

    repo = InMemoryRepositories()
    croc = Crocodile(
        id="animal-croc-1", name="Snappy", origin=Origin.INTERNAL, enclosure_id=None
    )
    enc = Enclosure(
        id="enc-mammal-1",
        name="Mammal House",
        enclosure_type=EnclosureType.MAMMAL,
        zoo_id="zoo-1",
    )
    repo.save(croc)
    repo.save(enc)

    app.dependency_overrides[get_admit_animal_use_case] = lambda: AdmitAnimalUseCase(
        repo, repo, repo, repo, repo
    )
    try:
        with TestClient(app) as client:
            response = client.post(
                "/animals/animal-croc-1/admit",
                json={"zoo_id": "zoo-1"},
            )
        assert response.status_code == 422
        assert "detail" in response.json()
    finally:
        app.dependency_overrides.clear()


def test_get_animal_returns_200_with_correct_fields() -> None:
    """GET /animals/{id} returns 200 with M-3 schema (ADR-021)."""
    repo = InMemoryRepositories()
    lion = Lion(id="animal-lion-1", name="Leo", origin=Origin.INTERNAL, enclosure_id=None)
    repo.save(lion)

    from zoo_management.infrastructure.dependencies import get_repositories
    app.dependency_overrides[get_repositories] = lambda: repo
    try:
        with TestClient(app) as client:
            response = client.get("/animals/animal-lion-1")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "animal-lion-1"
        assert data["name"] == "Leo"
        assert data["origin"] == "internal"
        assert data["enclosure_id"] is None
        assert data["type_name"] == "Lion"
        assert data["taxonomic_type"] == "Mammal"
        assert data["diet_type"] == "carnivore"
    finally:
        app.dependency_overrides.clear()


def test_get_animal_returns_404_for_missing() -> None:
    """GET /animals/nonexistent returns 404."""
    repo = InMemoryRepositories()
    from zoo_management.infrastructure.dependencies import get_repositories
    app.dependency_overrides[get_repositories] = lambda: repo
    try:
        with TestClient(app) as client:
            response = client.get("/animals/nonexistent")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_get_enclosure_returns_200_with_correct_fields() -> None:
    """GET /enclosures/{id} returns 200 with M-3 fields: animal_count, animal_ids."""
    repo = InMemoryRepositories()
    enc = Enclosure(
        id="enc-mammal-1",
        name="Mammal House",
        enclosure_type=EnclosureType.MAMMAL,
        zoo_id="zoo-1",
        assigned_zookeeper_id="emp-zk-1",
    )
    repo.save(enc)

    from zoo_management.infrastructure.dependencies import get_repositories
    app.dependency_overrides[get_repositories] = lambda: repo
    try:
        with TestClient(app) as client:
            response = client.get("/enclosures/enc-mammal-1")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "enc-mammal-1"
        assert data["name"] == "Mammal House"
        assert data["enclosure_type"] == "Mammal"
        assert data["zoo_id"] == "zoo-1"
        assert data["assigned_zookeeper_id"] == "emp-zk-1"
        assert data["animal_count"] == 0
        assert data["animal_ids"] == []
    finally:
        app.dependency_overrides.clear()


def test_get_enclosure_returns_404_for_missing() -> None:
    """GET /enclosures/nonexistent returns 404."""
    repo = InMemoryRepositories()
    from zoo_management.infrastructure.dependencies import get_repositories
    app.dependency_overrides[get_repositories] = lambda: repo
    try:
        with TestClient(app) as client:
            response = client.get("/enclosures/nonexistent")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()
