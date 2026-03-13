"""Unit tests for seed data (Phase 8.3)."""

from datetime import time

import pytest

from zoo_management.adapters.in_memory import InMemoryRepositories
from zoo_management.domain.entities import (
    Guide,
    Lion,
    Penguin,
    Veterinarian,
    Zoo,
    Zookeeper,
)
from zoo_management.infrastructure.seed import seed_data


@pytest.fixture
def seeded_repo() -> InMemoryRepositories:
    """Repository with seed data loaded."""
    repo = InMemoryRepositories()
    seed_data(repo)
    return repo


def test_seed_data_creates_zoo_with_id_zoo_1(seeded_repo: InMemoryRepositories) -> None:
    """Seed data creates a zoo with id zoo-1."""
    entity = seeded_repo.get_by_id("zoo-1")
    assert isinstance(entity, Zoo)
    assert entity.id == "zoo-1"
    assert entity.name == "City Zoo"


def test_seed_data_creates_three_enclosures(seeded_repo: InMemoryRepositories) -> None:
    """Seed data creates three enclosures."""
    enclosures = seeded_repo.get_by_zoo("zoo-1")
    assert len(enclosures) == 3
    ids = {e.id for e in enclosures}
    assert ids == {"enc-mammal-1", "enc-bird-1", "enc-reptile-1"}


def test_seed_data_creates_zookeeper_alice(seeded_repo: InMemoryRepositories) -> None:
    """Seed data creates zookeeper Alice (emp-zk-1)."""
    zookeepers = seeded_repo.get_by_zoo_and_type("zoo-1", "Zookeeper")
    assert len(zookeepers) >= 1
    alice = next((e for e in zookeepers if e.id == "emp-zk-1"), None)
    assert alice is not None
    assert isinstance(alice, Zookeeper)
    assert alice.name == "Alice"


def test_seed_data_creates_veterinarian_dr_bob(seeded_repo: InMemoryRepositories) -> None:
    """Seed data creates veterinarian Dr. Bob (emp-vet-1)."""
    vets = seeded_repo.get_by_zoo_and_type("zoo-1", "Veterinarian")
    assert len(vets) >= 1
    bob = next((e for e in vets if e.id == "emp-vet-1"), None)
    assert bob is not None
    assert isinstance(bob, Veterinarian)
    assert bob.name == "Dr. Bob"


def test_seed_data_creates_two_guides(seeded_repo: InMemoryRepositories) -> None:
    """Seed data creates two guides."""
    guides = seeded_repo.get_by_zoo_and_type("zoo-1", "Guide")
    assert len(guides) >= 2
    guide_ids = {e.id for e in guides}
    assert "emp-guide-1" in guide_ids
    assert "emp-guide-2" in guide_ids
    carol = next(e for e in guides if e.id == "emp-guide-1")
    assert isinstance(carol, Guide)
    assert carol.name == "Carol"


def test_seed_data_creates_lion_in_mammal_enclosure(seeded_repo: InMemoryRepositories) -> None:
    """Seed data creates lion Simba in mammal enclosure."""
    entity = seeded_repo.get_by_id("animal-lion-1")
    assert isinstance(entity, Lion)
    assert entity.name == "Simba"
    assert entity.enclosure_id == "enc-mammal-1"
    enclosures = seeded_repo.get_by_zoo("zoo-1")
    mammal = next(e for e in enclosures if e.id == "enc-mammal-1")
    assert mammal.animal_count >= 1
    assert any(a.id == "animal-lion-1" for a in mammal.animals)


def test_seed_data_creates_unplaced_penguin(seeded_repo: InMemoryRepositories) -> None:
    """Seed data creates penguin Pingu with no enclosure."""
    entity = seeded_repo.get_by_id("animal-penguin-1")
    assert isinstance(entity, Penguin)
    assert entity.name == "Pingu"
    assert entity.enclosure_id is None


def test_seed_data_creates_two_feeding_schedules(seeded_repo: InMemoryRepositories) -> None:
    """Seed data creates two feeding schedules (mammal 09:00, bird 10:00)."""
    sched_mammal = seeded_repo.get_by_enclosure_and_time("enc-mammal-1", time(9, 0))
    sched_bird = seeded_repo.get_by_enclosure_and_time("enc-bird-1", time(10, 0))
    assert sched_mammal is not None
    assert sched_bird is not None
    assert sched_mammal.diet == "meat"
    assert sched_bird.diet == "fish"


def test_seed_data_mammal_enclosure_has_zookeeper_assigned(
    seeded_repo: InMemoryRepositories,
) -> None:
    """Mammal enclosure has zookeeper emp-zk-1 assigned."""
    enclosures = seeded_repo.get_by_zoo("zoo-1")
    mammal = next(e for e in enclosures if e.id == "enc-mammal-1")
    assert mammal.assigned_zookeeper_id == "emp-zk-1"


def test_seed_data_zoo_tour_route_has_three_enclosures(seeded_repo: InMemoryRepositories) -> None:
    """Zoo tour route contains three enclosure ids."""
    entity = seeded_repo.get_by_id("zoo-1")
    assert isinstance(entity, Zoo)
    assert entity.tour_route == ["enc-mammal-1", "enc-bird-1", "enc-reptile-1"]
