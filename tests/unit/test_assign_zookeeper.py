"""Unit tests for AssignZookeeperUseCase (Phase 3)."""

import pytest

from zoo_management.adapters.in_memory import InMemoryRepositories
from zoo_management.domain.entities import (
    Enclosure,
    EnclosureType,
    Guide,
    Zookeeper,
)
from zoo_management.domain.exceptions import (
    EnclosureNotInZooError,
    EntityNotFoundError,
    InvalidEmployeeRoleError,
)
from zoo_management.usecases.assign_zookeeper import (
    AssignZookeeperRequest,
    AssignZookeeperUseCase,
)


def test_assign_zookeeper_happy_path() -> None:
    """Assign zookeeper to enclosure: success and repo updated."""
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
    req = AssignZookeeperRequest(
        zoo_id="zoo-1",
        enclosure_id="enc-mammal-1",
        zookeeper_id="emp-zk-1",
    )
    response = use_case.execute(req)

    assert response.enclosure_id == "enc-mammal-1"
    assert response.zookeeper_id == "emp-zk-1"
    stored = repo.get_by_id("enc-mammal-1")
    assert isinstance(stored, Enclosure)
    assert stored.assigned_zookeeper_id == "emp-zk-1"


def test_assign_zookeeper_idempotent_same_zookeeper() -> None:
    """Re-assigning same zookeeper is idempotent (ADR-031)."""
    repo = InMemoryRepositories()
    enc = Enclosure(
        id="enc-mammal-1",
        name="Mammal House",
        enclosure_type=EnclosureType.MAMMAL,
        zoo_id="zoo-1",
        assigned_zookeeper_id="emp-zk-1",
    )
    zk = Zookeeper(id="emp-zk-1", name="Jane", zoo_id="zoo-1")
    repo.save(enc)
    repo.save(zk)

    use_case = AssignZookeeperUseCase(repo, repo)
    req = AssignZookeeperRequest(
        zoo_id="zoo-1",
        enclosure_id="enc-mammal-1",
        zookeeper_id="emp-zk-1",
    )
    response = use_case.execute(req)

    assert response.zookeeper_id == "emp-zk-1"
    stored = repo.get_by_id("enc-mammal-1")
    assert isinstance(stored, Enclosure)
    assert stored.assigned_zookeeper_id == "emp-zk-1"


def test_assign_zookeeper_replaces_previous() -> None:
    """Assigning a different zookeeper replaces the previous one."""
    repo = InMemoryRepositories()
    enc = Enclosure(
        id="enc-mammal-1",
        name="Mammal House",
        enclosure_type=EnclosureType.MAMMAL,
        zoo_id="zoo-1",
        assigned_zookeeper_id="emp-zk-1",
    )
    zk_a = Zookeeper(id="emp-zk-1", name="Jane", zoo_id="zoo-1")
    zk_b = Zookeeper(id="emp-zk-2", name="Joe", zoo_id="zoo-1")
    repo.save(enc)
    repo.save(zk_a)
    repo.save(zk_b)

    use_case = AssignZookeeperUseCase(repo, repo)
    req = AssignZookeeperRequest(
        zoo_id="zoo-1",
        enclosure_id="enc-mammal-1",
        zookeeper_id="emp-zk-2",
    )
    response = use_case.execute(req)

    assert response.zookeeper_id == "emp-zk-2"
    stored = repo.get_by_id("enc-mammal-1")
    assert isinstance(stored, Enclosure)
    assert stored.assigned_zookeeper_id == "emp-zk-2"


def test_assign_zookeeper_raises_entity_not_found_for_missing_enclosure() -> None:
    """Missing enclosure_id raises EntityNotFoundError."""
    repo = InMemoryRepositories()
    zk = Zookeeper(id="emp-zk-1", name="Jane", zoo_id="zoo-1")
    repo.save(zk)

    use_case = AssignZookeeperUseCase(repo, repo)
    req = AssignZookeeperRequest(
        zoo_id="zoo-1",
        enclosure_id="missing-enc",
        zookeeper_id="emp-zk-1",
    )
    with pytest.raises(EntityNotFoundError):
        use_case.execute(req)


def test_assign_zookeeper_raises_entity_not_found_for_missing_employee() -> None:
    """Missing zookeeper_id raises EntityNotFoundError."""
    repo = InMemoryRepositories()
    enc = Enclosure(
        id="enc-mammal-1",
        name="Mammal House",
        enclosure_type=EnclosureType.MAMMAL,
        zoo_id="zoo-1",
    )
    repo.save(enc)

    use_case = AssignZookeeperUseCase(repo, repo)
    req = AssignZookeeperRequest(
        zoo_id="zoo-1",
        enclosure_id="enc-mammal-1",
        zookeeper_id="missing-emp",
    )
    with pytest.raises(EntityNotFoundError):
        use_case.execute(req)


def test_assign_zookeeper_raises_invalid_employee_role_for_non_zookeeper() -> None:
    """Assigning a Guide as zookeeper raises InvalidEmployeeRoleError."""
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

    use_case = AssignZookeeperUseCase(repo, repo)
    req = AssignZookeeperRequest(
        zoo_id="zoo-1",
        enclosure_id="enc-mammal-1",
        zookeeper_id="emp-guide-1",
    )
    with pytest.raises(InvalidEmployeeRoleError):
        use_case.execute(req)


def test_assign_zookeeper_raises_enclosure_not_in_zoo_when_zoo_ids_mismatch() -> None:
    """Enclosure in zoo-1, zookeeper in zoo-2, request zoo-1 -> EnclosureNotInZooError."""
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

    use_case = AssignZookeeperUseCase(repo, repo)
    req = AssignZookeeperRequest(
        zoo_id="zoo-1",
        enclosure_id="enc-mammal-1",
        zookeeper_id="emp-zk-1",
    )
    with pytest.raises(EnclosureNotInZooError):
        use_case.execute(req)


def test_assign_zookeeper_raises_enclosure_not_in_zoo_when_request_zoo_mismatch() -> None:
    """Enclosure in zoo-1, request with zoo-2 -> EnclosureNotInZooError (three-way check)."""
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
    req = AssignZookeeperRequest(
        zoo_id="zoo-2",
        enclosure_id="enc-mammal-1",
        zookeeper_id="emp-zk-1",
    )
    with pytest.raises(EnclosureNotInZooError):
        use_case.execute(req)
