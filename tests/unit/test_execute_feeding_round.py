"""Unit tests for ExecuteFeedingRoundUseCase (Phase 5)."""

from datetime import time

import pytest

from zoo_management.adapters.in_memory import InMemoryRepositories
from zoo_management.domain.entities import (
    Elephant,
    Enclosure,
    EnclosureType,
    FeedingSchedule,
    Lion,
    Origin,
    Penguin,
    Veterinarian,
    Zookeeper,
)
from zoo_management.domain.exceptions import (
    EntityNotFoundError,
    FeedingNotDueError,
    InvalidEmployeeRoleError,
    ZookeeperNotAssignedError,
)
from zoo_management.usecases.execute_feeding_round import (
    ExecuteFeedingRoundUseCase,
    FeedingRoundRequest,
)


def test_feeding_round_happy_path_with_animals() -> None:
    """Enclosure with Lion and Elephant; schedule at 09:00; zookeeper assigned."""
    repo = InMemoryRepositories()
    lion = Lion(id="animal-lion-1", name="Leo", origin=Origin.INTERNAL, enclosure_id="enc-mammal-1")
    elephant = Elephant(
        id="animal-elephant-1",
        name="Dumbo",
        origin=Origin.INTERNAL,
        enclosure_id="enc-mammal-1",
    )
    enc = Enclosure(
        id="enc-mammal-1",
        name="Mammal House",
        enclosure_type=EnclosureType.MAMMAL,
        zoo_id="zoo-1",
        assigned_zookeeper_id="emp-zk-1",
        animals=[lion, elephant],
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
    repo.save(elephant)
    repo.save(zk)
    repo.save(schedule)

    use_case = ExecuteFeedingRoundUseCase(repo, repo, repo)
    req = FeedingRoundRequest(
        enclosure_id="enc-mammal-1",
        zookeeper_id="emp-zk-1",
        current_time=time(9, 0, 0),
    )
    response = use_case.execute(req)

    assert response.enclosure_id == "enc-mammal-1"
    assert response.fed_count == 2
    assert response.note == "Fed 2 animals (diets: carnivore, herbivore)"


def test_feeding_round_empty_enclosure() -> None:
    """Empty enclosure; schedule exists; zookeeper assigned."""
    repo = InMemoryRepositories()
    enc = Enclosure(
        id="enc-bird-1",
        name="Bird House",
        enclosure_type=EnclosureType.BIRD,
        zoo_id="zoo-1",
        assigned_zookeeper_id="emp-zk-1",
        animals=[],
    )
    zk = Zookeeper(id="emp-zk-1", name="Jane", zoo_id="zoo-1")
    schedule = FeedingSchedule(
        id="sched-1",
        enclosure_id="enc-bird-1",
        scheduled_time=time(10, 0, 0),
        diet="fish",
    )
    repo.save(enc)
    repo.save(zk)
    repo.save(schedule)

    use_case = ExecuteFeedingRoundUseCase(repo, repo, repo)
    req = FeedingRoundRequest(
        enclosure_id="enc-bird-1",
        zookeeper_id="emp-zk-1",
        current_time=time(10, 0, 0),
    )
    response = use_case.execute(req)

    assert response.fed_count == 0
    assert response.note == "no animals to feed"


def test_feeding_round_polymorphic_diet_types() -> None:
    """Enclosure with Lion (carnivore) and Penguin (piscivore); note order matches animals."""
    repo = InMemoryRepositories()
    lion = Lion(id="animal-lion-1", name="Leo", origin=Origin.INTERNAL, enclosure_id="enc-mixed")
    penguin = Penguin(
        id="animal-penguin-1",
        name="Pingu",
        origin=Origin.INTERNAL,
        enclosure_id="enc-mixed",
    )
    enc = Enclosure(
        id="enc-mixed",
        name="Mixed",
        enclosure_type=EnclosureType.MAMMAL,
        zoo_id="zoo-1",
        assigned_zookeeper_id="emp-zk-1",
        animals=[lion, penguin],
    )
    zk = Zookeeper(id="emp-zk-1", name="Jane", zoo_id="zoo-1")
    schedule = FeedingSchedule(
        id="sched-1",
        enclosure_id="enc-mixed",
        scheduled_time=time(9, 0, 0),
        diet="mixed",
    )
    repo.save(enc)
    repo.save(lion)
    repo.save(penguin)
    repo.save(zk)
    repo.save(schedule)

    use_case = ExecuteFeedingRoundUseCase(repo, repo, repo)
    req = FeedingRoundRequest(
        enclosure_id="enc-mixed",
        zookeeper_id="emp-zk-1",
        current_time=time(9, 0, 0),
    )
    response = use_case.execute(req)

    assert response.fed_count == 2
    assert "carnivore" in response.note and "piscivore" in response.note
    assert response.note == "Fed 2 animals (diets: carnivore, piscivore)"


def test_feeding_round_raises_feeding_not_due_when_time_mismatch() -> None:
    """Schedule at 09:00; request with current_time=10:00 -> FeedingNotDueError."""
    repo = InMemoryRepositories()
    schedule = FeedingSchedule(
        id="sched-1",
        enclosure_id="enc-mammal-1",
        scheduled_time=time(9, 0, 0),
        diet="meat",
    )
    repo.save(schedule)

    use_case = ExecuteFeedingRoundUseCase(repo, repo, repo)
    req = FeedingRoundRequest(
        enclosure_id="enc-mammal-1",
        zookeeper_id="emp-zk-1",
        current_time=time(10, 0, 0),
    )
    with pytest.raises(FeedingNotDueError):
        use_case.execute(req)


def test_feeding_round_raises_feeding_not_due_for_nonexistent_enclosure() -> None:
    """No schedule for enc-nonexistent -> FeedingNotDueError (ADR-029)."""
    repo = InMemoryRepositories()

    use_case = ExecuteFeedingRoundUseCase(repo, repo, repo)
    req = FeedingRoundRequest(
        enclosure_id="enc-nonexistent",
        zookeeper_id="emp-zk-1",
        current_time=time(9, 0, 0),
    )
    with pytest.raises(FeedingNotDueError):
        use_case.execute(req)


def test_feeding_round_raises_zookeeper_not_assigned() -> None:
    """Enclosure has zookeeper A; request from zookeeper B -> ZookeeperNotAssignedError."""
    repo = InMemoryRepositories()
    enc = Enclosure(
        id="enc-mammal-1",
        name="Mammal House",
        enclosure_type=EnclosureType.MAMMAL,
        zoo_id="zoo-1",
        assigned_zookeeper_id="emp-zk-other",
        animals=[],
    )
    zk_other = Zookeeper(id="emp-zk-other", name="Other", zoo_id="zoo-1")
    zk_1 = Zookeeper(id="emp-zk-1", name="Jane", zoo_id="zoo-1")
    schedule = FeedingSchedule(
        id="sched-1",
        enclosure_id="enc-mammal-1",
        scheduled_time=time(9, 0, 0),
        diet="meat",
    )
    repo.save(enc)
    repo.save(zk_other)
    repo.save(zk_1)
    repo.save(schedule)

    use_case = ExecuteFeedingRoundUseCase(repo, repo, repo)
    req = FeedingRoundRequest(
        enclosure_id="enc-mammal-1",
        zookeeper_id="emp-zk-1",
        current_time=time(9, 0, 0),
    )
    with pytest.raises(ZookeeperNotAssignedError):
        use_case.execute(req)


def test_feeding_round_raises_invalid_employee_role_for_non_zookeeper() -> None:
    """Pass Veterinarian id as zookeeper_id -> InvalidEmployeeRoleError."""
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
    req = FeedingRoundRequest(
        enclosure_id="enc-mammal-1",
        zookeeper_id="emp-vet-1",
        current_time=time(9, 0, 0),
    )
    with pytest.raises(InvalidEmployeeRoleError):
        use_case.execute(req)


def test_feeding_round_raises_entity_not_found_for_missing_employee() -> None:
    """Zookeeper id not in repo -> EntityNotFoundError (after schedule + enclosure checks)."""
    repo = InMemoryRepositories()
    enc = Enclosure(
        id="enc-mammal-1",
        name="Mammal House",
        enclosure_type=EnclosureType.MAMMAL,
        zoo_id="zoo-1",
        assigned_zookeeper_id="missing-emp",
        animals=[],
    )
    schedule = FeedingSchedule(
        id="sched-1",
        enclosure_id="enc-mammal-1",
        scheduled_time=time(9, 0, 0),
        diet="meat",
    )
    repo.save(enc)
    repo.save(schedule)

    use_case = ExecuteFeedingRoundUseCase(repo, repo, repo)
    req = FeedingRoundRequest(
        enclosure_id="enc-mammal-1",
        zookeeper_id="missing-emp",
        current_time=time(9, 0, 0),
    )
    with pytest.raises(EntityNotFoundError):
        use_case.execute(req)


def test_feeding_round_uses_client_supplied_time_not_system_time() -> None:
    """Use case uses req.current_time directly (ADR-019); deterministic time."""
    repo = InMemoryRepositories()
    enc = Enclosure(
        id="enc-mammal-1",
        name="Mammal House",
        enclosure_type=EnclosureType.MAMMAL,
        zoo_id="zoo-1",
        assigned_zookeeper_id="emp-zk-1",
        animals=[],
    )
    zk = Zookeeper(id="emp-zk-1", name="Jane", zoo_id="zoo-1")
    schedule = FeedingSchedule(
        id="sched-1",
        enclosure_id="enc-mammal-1",
        scheduled_time=time(14, 30, 0),
        diet="meat",
    )
    repo.save(enc)
    repo.save(zk)
    repo.save(schedule)

    use_case = ExecuteFeedingRoundUseCase(repo, repo, repo)
    req = FeedingRoundRequest(
        enclosure_id="enc-mammal-1",
        zookeeper_id="emp-zk-1",
        current_time=time(14, 30, 0),
    )
    response = use_case.execute(req)
    assert response.fed_count == 0
    assert response.note == "no animals to feed"
