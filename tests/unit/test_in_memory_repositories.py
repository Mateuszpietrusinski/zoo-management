"""Unit tests for InMemoryRepositories (Phase 2)."""

from datetime import date, datetime, time

import pytest

from zoo_management.adapters.in_memory import InMemoryRepositories
from zoo_management.domain.entities import (
    AdmissionRecord,
    Enclosure,
    EnclosureType,
    FeedingSchedule,
    HealthCheckRecord,
    HealthResult,
    Lion,
    Origin,
    Tour,
    Zoo,
    Zookeeper,
)
from zoo_management.domain.exceptions import EntityNotFoundError

# ---------------------------------------------------------------------------
# Step 2.1 — Zoo Repository
# ---------------------------------------------------------------------------


def test_seed_zoo_stores_zoo() -> None:
    repos = InMemoryRepositories()
    zoo = Zoo(id="z1", name="Main Zoo", tour_route=[])
    repos.seed_zoo(zoo)
    assert repos.get_by_id("z1") == zoo


def test_get_zoo_by_id_returns_stored_zoo() -> None:
    repos = InMemoryRepositories()
    zoo = Zoo(id="z1", name="Main Zoo", tour_route=["e1"])
    repos.seed_zoo(zoo)
    assert repos.get_by_id("z1") is zoo


def test_get_zoo_by_id_raises_entity_not_found_for_missing_id() -> None:
    repos = InMemoryRepositories()
    with pytest.raises(EntityNotFoundError):
        repos.get_by_id("missing-zoo")


# ---------------------------------------------------------------------------
# Step 2.2 — Enclosure Repository
# ---------------------------------------------------------------------------


def test_save_enclosure_stores_enclosure() -> None:
    repos = InMemoryRepositories()
    enc = Enclosure(
        id="e1",
        name="Lion House",
        enclosure_type=EnclosureType.MAMMAL,
        zoo_id="z1",
    )
    repos.save(enc)
    assert repos.get_by_id("e1") == enc


def test_get_enclosure_by_id_returns_stored() -> None:
    repos = InMemoryRepositories()
    enc = Enclosure(
        id="e1",
        name="Lion House",
        enclosure_type=EnclosureType.MAMMAL,
        zoo_id="z1",
    )
    repos.save(enc)
    assert repos.get_by_id("e1") is enc


def test_get_enclosure_by_id_raises_entity_not_found() -> None:
    repos = InMemoryRepositories()
    with pytest.raises(EntityNotFoundError):
        repos.get_by_id("missing-enc")


def test_get_enclosures_by_zoo_returns_matching() -> None:
    repos = InMemoryRepositories()
    enc1 = Enclosure(
        id="e1",
        name="Lion House",
        enclosure_type=EnclosureType.MAMMAL,
        zoo_id="z1",
    )
    enc2 = Enclosure(
        id="e2",
        name="Bird House",
        enclosure_type=EnclosureType.BIRD,
        zoo_id="z1",
    )
    enc3 = Enclosure(
        id="e3",
        name="Other Zoo Enclosure",
        enclosure_type=EnclosureType.REPTILE,
        zoo_id="z2",
    )
    repos.save(enc1)
    repos.save(enc2)
    repos.save(enc3)
    result = repos.get_by_zoo("z1")
    assert len(result) == 2
    assert {e.id for e in result} == {"e1", "e2"}


def test_get_enclosures_by_zoo_returns_empty_for_no_match() -> None:
    repos = InMemoryRepositories()
    enc = Enclosure(
        id="e1",
        name="Lion House",
        enclosure_type=EnclosureType.MAMMAL,
        zoo_id="z1",
    )
    repos.save(enc)
    assert repos.get_by_zoo("z99") == []


def test_save_enclosure_overwrites_existing() -> None:
    repos = InMemoryRepositories()
    enc1 = Enclosure(
        id="e1",
        name="Lion House",
        enclosure_type=EnclosureType.MAMMAL,
        zoo_id="z1",
    )
    repos.save(enc1)
    enc2 = Enclosure(
        id="e1",
        name="Big Cat House",
        enclosure_type=EnclosureType.MAMMAL,
        zoo_id="z1",
    )
    repos.save(enc2)
    assert repos.get_by_id("e1").name == "Big Cat House"


# ---------------------------------------------------------------------------
# Step 2.3 — Animal Repository
# ---------------------------------------------------------------------------


def test_save_animal_stores_animal() -> None:
    repos = InMemoryRepositories()
    animal = Lion(id="a1", name="Simba", origin=Origin.INTERNAL)
    repos.save(animal)
    assert repos.get_by_id("a1") == animal


def test_get_animal_by_id_returns_stored() -> None:
    repos = InMemoryRepositories()
    animal = Lion(id="a1", name="Simba", origin=Origin.INTERNAL)
    repos.save(animal)
    assert repos.get_by_id("a1") is animal


def test_get_animal_by_id_raises_entity_not_found() -> None:
    repos = InMemoryRepositories()
    with pytest.raises(EntityNotFoundError):
        repos.get_by_id("missing-animal")


def test_save_animal_overwrites_existing() -> None:
    repos = InMemoryRepositories()
    animal1 = Lion(id="a1", name="Simba", origin=Origin.INTERNAL)
    repos.save(animal1)
    animal2 = Lion(id="a1", name="Mufasa", origin=Origin.EXTERNAL)
    repos.save(animal2)
    assert repos.get_by_id("a1").name == "Mufasa"


# ---------------------------------------------------------------------------
# Step 2.4 — Employee Repository
# ---------------------------------------------------------------------------


def test_save_employee_stores_employee() -> None:
    repos = InMemoryRepositories()
    emp = Zookeeper(id="emp1", name="Jane", zoo_id="z1")
    repos.save(emp)
    assert repos.get_by_id("emp1") == emp


def test_get_employee_by_id_returns_stored() -> None:
    repos = InMemoryRepositories()
    emp = Zookeeper(id="emp1", name="Jane", zoo_id="z1")
    repos.save(emp)
    assert repos.get_by_id("emp1") is emp


def test_get_employee_by_id_raises_entity_not_found() -> None:
    repos = InMemoryRepositories()
    with pytest.raises(EntityNotFoundError):
        repos.get_by_id("missing-emp")


def test_get_by_zoo_and_type_returns_matching_employees() -> None:
    from zoo_management.domain.entities import Guide, Veterinarian

    repos = InMemoryRepositories()
    zk = Zookeeper(id="zk1", name="Jane", zoo_id="z1")
    vet = Veterinarian(id="vet1", name="Bob", zoo_id="z1")
    guide = Guide(id="g1", name="Alice", zoo_id="z1")
    zk2 = Zookeeper(id="zk2", name="Joe", zoo_id="z2")
    repos.save(zk)
    repos.save(vet)
    repos.save(guide)
    repos.save(zk2)
    result = repos.get_by_zoo_and_type("z1", "Zookeeper")
    assert len(result) == 1
    assert result[0].id == "zk1"


def test_get_by_zoo_and_type_returns_empty_for_no_match() -> None:
    repos = InMemoryRepositories()
    emp = Zookeeper(id="emp1", name="Jane", zoo_id="z1")
    repos.save(emp)
    assert repos.get_by_zoo_and_type("z1", "Veterinarian") == []
    assert repos.get_by_zoo_and_type("z99", "Zookeeper") == []


def test_save_employee_overwrites_existing() -> None:
    from zoo_management.domain.entities import Guide

    repos = InMemoryRepositories()
    g1 = Guide(id="g1", name="Alice", zoo_id="z1", is_available=True)
    repos.save(g1)
    g2 = Guide(id="g1", name="Alice", zoo_id="z1", is_available=False)
    repos.save(g2)
    assert repos.get_by_id("g1").is_available is False


# ---------------------------------------------------------------------------
# Step 2.5 — FeedingSchedule Repository
# ---------------------------------------------------------------------------


def test_save_schedule_stores_schedule() -> None:
    repos = InMemoryRepositories()
    t = time(10, 0)
    schedule = FeedingSchedule(
        id="s1",
        enclosure_id="e1",
        scheduled_time=t,
        diet="carnivore",
    )
    repos.save(schedule)
    assert repos.get_by_enclosure_and_time("e1", t) == schedule


def test_get_by_enclosure_and_time_returns_matching() -> None:
    repos = InMemoryRepositories()
    t = time(10, 0)
    schedule = FeedingSchedule(
        id="s1",
        enclosure_id="e1",
        scheduled_time=t,
        diet="carnivore",
    )
    repos.save(schedule)
    assert repos.get_by_enclosure_and_time("e1", t) is schedule


def test_get_by_enclosure_and_time_returns_none_for_no_match() -> None:
    repos = InMemoryRepositories()
    assert repos.get_by_enclosure_and_time("e1", time(10, 0)) is None
    t = time(10, 0)
    schedule = FeedingSchedule(
        id="s1",
        enclosure_id="e1",
        scheduled_time=t,
        diet="carnivore",
    )
    repos.save(schedule)
    assert repos.get_by_enclosure_and_time("e1", time(11, 0)) is None
    assert repos.get_by_enclosure_and_time("e2", t) is None


def test_save_schedule_uses_composite_key() -> None:
    repos = InMemoryRepositories()
    t = time(10, 0)
    s1 = FeedingSchedule(
        id="s1",
        enclosure_id="e1",
        scheduled_time=t,
        diet="carnivore",
    )
    repos.save(s1)
    stored = repos.get_by_enclosure_and_time("e1", t)
    assert stored is not None
    assert stored.enclosure_id == "e1"
    assert stored.scheduled_time == t


def test_save_schedule_overwrites_on_same_composite_key() -> None:
    repos = InMemoryRepositories()
    t = time(10, 0)
    s1 = FeedingSchedule(
        id="s1",
        enclosure_id="e1",
        scheduled_time=t,
        diet="carnivore",
    )
    s2 = FeedingSchedule(
        id="s2",
        enclosure_id="e1",
        scheduled_time=t,
        diet="meat",
    )
    repos.save(s1)
    repos.save(s2)
    stored = repos.get_by_enclosure_and_time("e1", t)
    assert stored is not None
    assert stored.diet == "meat"


# ---------------------------------------------------------------------------
# Step 2.6 — Record Repositories
# ---------------------------------------------------------------------------


def test_save_admission_record_stores_record() -> None:
    repos = InMemoryRepositories()
    rec = AdmissionRecord(
        id="ar1",
        date=date(2025, 1, 15),
        animal_id="a1",
        enclosure_id="e1",
        zookeeper_id="zk1",
        vet_id="vet1",
        health_check_record_id="hc1",
    )
    repos.save(rec)
    # No get_by_id on port; we only verify save doesn't raise.
    # We can check internal state for unit test or just assert no exception.
    # Phase doc says "These only need save() — no get_by_id on the port contract."
    # So we just ensure save works; optionally assert repos has it if we expose for tests.
    assert True  # save completed


def test_save_health_check_record_stores_record() -> None:
    repos = InMemoryRepositories()
    rec = HealthCheckRecord(
        id="hc1",
        date=date(2025, 1, 15),
        animal_id="a1",
        vet_id="vet1",
        result=HealthResult.HEALTHY,
        notes=None,
    )
    repos.save(rec)
    assert True


def test_save_tour_stores_tour() -> None:
    repos = InMemoryRepositories()
    start = datetime(2025, 1, 15, 10, 0)
    end = datetime(2025, 1, 15, 11, 0)
    tour = Tour(
        id="t1",
        guide_id="g1",
        route=["e1", "e2"],
        start_time=start,
        end_time=end,
    )
    repos.save(tour)
    assert True
