"""Unit tests for ConductHealthCheckUseCase (Phase 6)."""

from datetime import date

import pytest

from zoo_management.adapters.in_memory import InMemoryRepositories
from zoo_management.domain.entities import (
    HealthResult,
    Lion,
    Origin,
    Penguin,
    Veterinarian,
    Zookeeper,
)
from zoo_management.domain.exceptions import (
    EntityNotFoundError,
    InvalidEmployeeRoleError,
)
from zoo_management.usecases.conduct_health_check import (
    ConductHealthCheckUseCase,
    HealthCheckRequest,
)


def test_health_check_healthy_creates_record() -> None:
    """Lion and vet in repo; execute with result=HEALTHY; record saved with correct fields."""
    repo = InMemoryRepositories()
    lion = Lion(
        id="animal-lion-1",
        name="Leo",
        origin=Origin.INTERNAL,
        enclosure_id=None,
    )
    vet = Veterinarian(id="emp-vet-1", name="Dr. Bob", zoo_id="zoo-1")
    repo.save(lion)
    repo.save(vet)

    use_case = ConductHealthCheckUseCase(repo, repo, repo)
    req = HealthCheckRequest(
        animal_id="animal-lion-1",
        vet_id="emp-vet-1",
        result=HealthResult.HEALTHY,
        notes=None,
    )
    response = use_case.execute(req)

    assert response.health_check_record_id
    assert response.result == HealthResult.HEALTHY
    saved = repo.get_health_record_by_id(response.health_check_record_id)
    assert saved is not None
    assert saved.animal_id == "animal-lion-1"
    assert saved.vet_id == "emp-vet-1"
    assert saved.result == HealthResult.HEALTHY
    assert saved.notes is None


def test_health_check_need_follow_up_creates_record() -> None:
    """Assert result == NEED_FOLLOW_UP."""
    repo = InMemoryRepositories()
    lion = Lion(
        id="animal-lion-1",
        name="Leo",
        origin=Origin.INTERNAL,
        enclosure_id=None,
    )
    vet = Veterinarian(id="emp-vet-1", name="Dr. Bob", zoo_id="zoo-1")
    repo.save(lion)
    repo.save(vet)

    use_case = ConductHealthCheckUseCase(repo, repo, repo)
    req = HealthCheckRequest(
        animal_id="animal-lion-1",
        vet_id="emp-vet-1",
        result=HealthResult.NEED_FOLLOW_UP,
        notes=None,
    )
    response = use_case.execute(req)

    assert response.result == HealthResult.NEED_FOLLOW_UP
    saved = repo.get_health_record_by_id(response.health_check_record_id)
    assert saved is not None
    assert saved.result == HealthResult.NEED_FOLLOW_UP


def test_health_check_critical_creates_record() -> None:
    """Assert result == CRITICAL."""
    repo = InMemoryRepositories()
    lion = Lion(
        id="animal-lion-1",
        name="Leo",
        origin=Origin.INTERNAL,
        enclosure_id=None,
    )
    vet = Veterinarian(id="emp-vet-1", name="Dr. Bob", zoo_id="zoo-1")
    repo.save(lion)
    repo.save(vet)

    use_case = ConductHealthCheckUseCase(repo, repo, repo)
    req = HealthCheckRequest(
        animal_id="animal-lion-1",
        vet_id="emp-vet-1",
        result=HealthResult.CRITICAL,
        notes=None,
    )
    response = use_case.execute(req)

    assert response.result == HealthResult.CRITICAL
    saved = repo.get_health_record_by_id(response.health_check_record_id)
    assert saved is not None
    assert saved.result == HealthResult.CRITICAL


def test_health_check_with_notes() -> None:
    """Execute with notes='Slight limp observed'; HealthCheckRecord.notes matches."""
    repo = InMemoryRepositories()
    lion = Lion(
        id="animal-lion-1",
        name="Leo",
        origin=Origin.INTERNAL,
        enclosure_id=None,
    )
    vet = Veterinarian(id="emp-vet-1", name="Dr. Bob", zoo_id="zoo-1")
    repo.save(lion)
    repo.save(vet)

    use_case = ConductHealthCheckUseCase(repo, repo, repo)
    req = HealthCheckRequest(
        animal_id="animal-lion-1",
        vet_id="emp-vet-1",
        result=HealthResult.HEALTHY,
        notes="Slight limp observed",
    )
    response = use_case.execute(req)

    saved = repo.get_health_record_by_id(response.health_check_record_id)
    assert saved is not None
    assert saved.notes == "Slight limp observed"


def test_health_check_notes_default_none() -> None:
    """Execute without notes; HealthCheckRecord.notes is None."""
    repo = InMemoryRepositories()
    lion = Lion(
        id="animal-lion-1",
        name="Leo",
        origin=Origin.INTERNAL,
        enclosure_id=None,
    )
    vet = Veterinarian(id="emp-vet-1", name="Dr. Bob", zoo_id="zoo-1")
    repo.save(lion)
    repo.save(vet)

    use_case = ConductHealthCheckUseCase(repo, repo, repo)
    req = HealthCheckRequest(
        animal_id="animal-lion-1",
        vet_id="emp-vet-1",
        result=HealthResult.HEALTHY,
        notes=None,
    )
    response = use_case.execute(req)

    saved = repo.get_health_record_by_id(response.health_check_record_id)
    assert saved is not None
    assert saved.notes is None


def test_health_check_raises_entity_not_found_for_missing_animal() -> None:
    """Animal not in repo -> EntityNotFoundError."""
    repo = InMemoryRepositories()
    vet = Veterinarian(id="emp-vet-1", name="Dr. Bob", zoo_id="zoo-1")
    repo.save(vet)

    use_case = ConductHealthCheckUseCase(repo, repo, repo)
    req = HealthCheckRequest(
        animal_id="missing-animal",
        vet_id="emp-vet-1",
        result=HealthResult.HEALTHY,
        notes=None,
    )

    with pytest.raises(EntityNotFoundError):
        use_case.execute(req)


def test_health_check_raises_entity_not_found_for_missing_employee() -> None:
    """Employee not in repo -> EntityNotFoundError."""
    repo = InMemoryRepositories()
    lion = Lion(
        id="animal-lion-1",
        name="Leo",
        origin=Origin.INTERNAL,
        enclosure_id=None,
    )
    repo.save(lion)

    use_case = ConductHealthCheckUseCase(repo, repo, repo)
    req = HealthCheckRequest(
        animal_id="animal-lion-1",
        vet_id="missing-vet",
        result=HealthResult.HEALTHY,
        notes=None,
    )

    with pytest.raises(EntityNotFoundError):
        use_case.execute(req)


def test_health_check_raises_invalid_employee_role_for_non_vet() -> None:
    """Pass a Zookeeper id -> InvalidEmployeeRoleError."""
    repo = InMemoryRepositories()
    lion = Lion(
        id="animal-lion-1",
        name="Leo",
        origin=Origin.INTERNAL,
        enclosure_id=None,
    )
    zk = Zookeeper(id="emp-zk-1", name="Jane", zoo_id="zoo-1")
    repo.save(lion)
    repo.save(zk)

    use_case = ConductHealthCheckUseCase(repo, repo, repo)
    req = HealthCheckRequest(
        animal_id="animal-lion-1",
        vet_id="emp-zk-1",
        result=HealthResult.HEALTHY,
        notes=None,
    )

    with pytest.raises(InvalidEmployeeRoleError):
        use_case.execute(req)


def test_health_check_record_date_is_today() -> None:
    """HealthCheckRecord.date == date.today()."""
    repo = InMemoryRepositories()
    penguin = Penguin(
        id="animal-penguin-1",
        name="Pingu",
        origin=Origin.INTERNAL,
        enclosure_id=None,
    )
    vet = Veterinarian(id="emp-vet-1", name="Dr. Bob", zoo_id="zoo-1")
    repo.save(penguin)
    repo.save(vet)

    use_case = ConductHealthCheckUseCase(repo, repo, repo)
    req = HealthCheckRequest(
        animal_id="animal-penguin-1",
        vet_id="emp-vet-1",
        result=HealthResult.HEALTHY,
        notes=None,
    )
    response = use_case.execute(req)

    saved = repo.get_health_record_by_id(response.health_check_record_id)
    assert saved is not None
    assert saved.date == date.today()
