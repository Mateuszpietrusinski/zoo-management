"""Seed data for development and testing (architecture C3 — pre-seeded entities)."""

from datetime import time

from zoo_management.adapters.in_memory import InMemoryRepositories
from zoo_management.domain.entities import (
    Enclosure,
    EnclosureType,
    FeedingSchedule,
    Guide,
    Lion,
    Origin,
    Penguin,
    Veterinarian,
    Zoo,
    Zookeeper,
)


def seed_data(repo: InMemoryRepositories) -> None:
    """Populate repository with stable seed data (ADR-025: seed_zoo for Zoo).

    Creates one zoo, three enclosures, employees (zookeepers, vets, guides),
    a placed lion and unplaced penguin, and feeding schedules. Called once at
    app startup.

    Args:
        repo: In-memory repository instance to populate.
    """
    # Zoo
    zoo = Zoo(
        id="zoo-1",
        name="City Zoo",
        tour_route=["enc-mammal-1", "enc-bird-1", "enc-reptile-1"],
    )
    repo.seed_zoo(zoo)

    # Enclosures
    enc_mammal = Enclosure(
        id="enc-mammal-1",
        name="Mammal Enclosure",
        enclosure_type=EnclosureType.MAMMAL,
        zoo_id="zoo-1",
        assigned_zookeeper_id="emp-zk-1",
    )
    enc_bird = Enclosure(
        id="enc-bird-1",
        name="Bird Enclosure",
        enclosure_type=EnclosureType.BIRD,
        zoo_id="zoo-1",
        assigned_zookeeper_id="emp-zk-1",
    )
    enc_reptile = Enclosure(
        id="enc-reptile-1",
        name="Reptile Enclosure",
        enclosure_type=EnclosureType.REPTILE,
        zoo_id="zoo-1",
        assigned_zookeeper_id="emp-zk-1",
    )
    repo.save(enc_mammal)
    repo.save(enc_bird)
    repo.save(enc_reptile)

    # Employees
    repo.save(Zookeeper(id="emp-zk-1", name="Alice", zoo_id="zoo-1"))
    repo.save(Veterinarian(id="emp-vet-1", name="Dr. Bob", zoo_id="zoo-1"))
    repo.save(Guide(id="emp-guide-1", name="Carol", zoo_id="zoo-1", is_available=True))
    repo.save(Guide(id="emp-guide-2", name="Dave", zoo_id="zoo-1", is_available=True))

    # Animals: lion in mammal enclosure, penguin unplaced
    lion = Lion(
        id="animal-lion-1",
        name="Simba",
        origin=Origin.INTERNAL,
        enclosure_id="enc-mammal-1",
    )
    enc_mammal.animals.append(lion)
    repo.save(lion)
    repo.save(enc_mammal)

    penguin = Penguin(
        id="animal-penguin-1",
        name="Pingu",
        origin=Origin.INTERNAL,
        enclosure_id=None,
    )
    repo.save(penguin)

    # Feeding Schedules
    repo.save(
        FeedingSchedule(
            id="sched-mammal-1",
            enclosure_id="enc-mammal-1",
            scheduled_time=time(9, 0),
            diet="meat",
        )
    )
    repo.save(
        FeedingSchedule(
            id="sched-bird-1",
            enclosure_id="enc-bird-1",
            scheduled_time=time(10, 0),
            diet="fish",
        )
    )
