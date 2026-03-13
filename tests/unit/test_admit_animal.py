"""Unit tests for AdmitAnimalUseCase (Phase 4)."""

import pytest

from zoo_management.adapters.in_memory import InMemoryRepositories
from zoo_management.domain.entities import (
    Crocodile,
    Enclosure,
    EnclosureType,
    HealthResult,
    Lion,
    Origin,
    Penguin,
    Veterinarian,
    Zookeeper,
)
from zoo_management.domain.exceptions import (
    AnimalAlreadyPlacedError,
    EntityNotFoundError,
    HealthCheckNotClearedError,
    InvalidEmployeeRoleError,
    InvalidRequestError,
    NoSuitableEnclosureError,
)
from zoo_management.usecases.admit_animal import (
    AdmitAnimalRequest,
    AdmitAnimalUseCase,
)


def _make_use_case() -> AdmitAnimalUseCase:
    repo = InMemoryRepositories()
    return AdmitAnimalUseCase(repo, repo, repo, repo, repo)


def test_admit_internal_animal_happy_path() -> None:
    """Internal lion admitted to mammal enclosure; no health check."""
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

    use_case = AdmitAnimalUseCase(repo, repo, repo, repo, repo)
    req = AdmitAnimalRequest(animal_id="animal-lion-1", zoo_id="zoo-1")
    response = use_case.execute(req)

    assert response.animal_id == "animal-lion-1"
    assert response.enclosure_id == "enc-mammal-1"
    assert response.admission_record_id is not None
    stored_animal = repo.get_by_id("animal-lion-1")
    assert isinstance(stored_animal, Lion)
    assert stored_animal.enclosure_id == "enc-mammal-1"
    stored_enc = repo.get_by_id("enc-mammal-1")
    assert isinstance(stored_enc, Enclosure)
    assert len(stored_enc.animals) == 1
    assert stored_enc.animals[0].id == "animal-lion-1"
    assert len(repo._admission_records) == 1
    assert len(repo._health_records) == 0


def test_admit_internal_animal_ignores_health_fields() -> None:
    """Internal animal: vet_id and health_check_result passed but ignored (ADR-002)."""
    repo = InMemoryRepositories()
    lion = Lion(id="animal-lion-1", name="Leo", origin=Origin.INTERNAL, enclosure_id=None)
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

    use_case = AdmitAnimalUseCase(repo, repo, repo, repo, repo)
    req = AdmitAnimalRequest(
        animal_id="animal-lion-1",
        zoo_id="zoo-1",
        vet_id="emp-vet-1",
        health_check_result=HealthResult.CRITICAL,
        health_check_notes="ignored",
    )
    response = use_case.execute(req)

    assert response.enclosure_id == "enc-mammal-1"
    assert len(repo._health_records) == 0


def test_admit_external_animal_with_healthy_result() -> None:
    """External penguin with HEALTHY result: placed, health record and admission created."""
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

    use_case = AdmitAnimalUseCase(repo, repo, repo, repo, repo)
    req = AdmitAnimalRequest(
        animal_id="animal-penguin-ext",
        zoo_id="zoo-1",
        vet_id="emp-vet-1",
        health_check_result=HealthResult.HEALTHY,
        health_check_notes="Cleared",
    )
    response = use_case.execute(req)

    assert response.animal_id == "animal-penguin-ext"
    assert response.enclosure_id == "enc-bird-1"
    assert response.admission_record_id is not None
    assert len(repo._health_records) == 1
    hc = list(repo._health_records.values())[0]
    assert hc.animal_id == "animal-penguin-ext"
    assert hc.result == HealthResult.HEALTHY
    adm = list(repo._admission_records.values())[0]
    assert adm.health_check_record_id == hc.id


def test_admit_external_animal_raises_health_check_not_cleared_for_non_healthy() -> None:
    """External animal with CRITICAL result raises HealthCheckNotClearedError."""
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

    use_case = AdmitAnimalUseCase(repo, repo, repo, repo, repo)
    req = AdmitAnimalRequest(
        animal_id="animal-lion-ext",
        zoo_id="zoo-1",
        vet_id="emp-vet-1",
        health_check_result=HealthResult.CRITICAL,
    )
    with pytest.raises(HealthCheckNotClearedError):
        use_case.execute(req)
    assert repo.get_by_id("animal-lion-ext").enclosure_id is None


def test_admit_external_animal_raises_invalid_request_when_vet_id_missing() -> None:
    """External animal with vet_id=None raises InvalidRequestError."""
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
    repo.save(lion)
    repo.save(enc)

    use_case = AdmitAnimalUseCase(repo, repo, repo, repo, repo)
    req = AdmitAnimalRequest(
        animal_id="animal-lion-ext",
        zoo_id="zoo-1",
        vet_id=None,
        health_check_result=HealthResult.HEALTHY,
    )
    with pytest.raises(InvalidRequestError):
        use_case.execute(req)


def test_admit_external_animal_raises_invalid_request_when_result_missing() -> None:
    """External animal with health_check_result=None raises InvalidRequestError."""
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

    use_case = AdmitAnimalUseCase(repo, repo, repo, repo, repo)
    req = AdmitAnimalRequest(
        animal_id="animal-lion-ext",
        zoo_id="zoo-1",
        vet_id="emp-vet-1",
        health_check_result=None,
    )
    with pytest.raises(InvalidRequestError):
        use_case.execute(req)


def test_admit_external_animal_raises_invalid_employee_role_for_non_vet() -> None:
    """Passing a Zookeeper id as vet_id raises InvalidEmployeeRoleError."""
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
    zk = Zookeeper(id="emp-zk-1", name="Alice", zoo_id="zoo-1")
    repo.save(lion)
    repo.save(enc)
    repo.save(zk)

    use_case = AdmitAnimalUseCase(repo, repo, repo, repo, repo)
    req = AdmitAnimalRequest(
        animal_id="animal-lion-ext",
        zoo_id="zoo-1",
        vet_id="emp-zk-1",
        health_check_result=HealthResult.HEALTHY,
    )
    with pytest.raises(InvalidEmployeeRoleError):
        use_case.execute(req)


def test_admit_raises_entity_not_found_for_missing_animal() -> None:
    """Non-existent animal_id raises EntityNotFoundError."""
    repo = InMemoryRepositories()
    use_case = AdmitAnimalUseCase(repo, repo, repo, repo, repo)
    req = AdmitAnimalRequest(animal_id="nonexistent", zoo_id="zoo-1")
    with pytest.raises(EntityNotFoundError):
        use_case.execute(req)


def test_admit_raises_animal_already_placed_when_enclosure_set() -> None:
    """Animal with enclosure_id already set raises AnimalAlreadyPlacedError (ADR-013)."""
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

    use_case = AdmitAnimalUseCase(repo, repo, repo, repo, repo)
    req = AdmitAnimalRequest(animal_id="animal-lion-placed", zoo_id="zoo-1")
    with pytest.raises(AnimalAlreadyPlacedError):
        use_case.execute(req)


def test_admit_raises_no_suitable_enclosure_when_type_mismatch() -> None:
    """Crocodile (Reptile) with only MAMMAL enclosures raises NoSuitableEnclosureError (ADR-020)."""
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

    use_case = AdmitAnimalUseCase(repo, repo, repo, repo, repo)
    req = AdmitAnimalRequest(animal_id="animal-croc-1", zoo_id="zoo-1")
    with pytest.raises(NoSuitableEnclosureError):
        use_case.execute(req)


def test_admit_selects_first_matching_enclosure() -> None:
    """Two mammal enclosures: first in list order is selected (ADR-012)."""
    repo = InMemoryRepositories()
    lion = Lion(id="animal-lion-1", name="Leo", origin=Origin.INTERNAL, enclosure_id=None)
    enc1 = Enclosure(
        id="enc-mammal-first",
        name="First Mammal",
        enclosure_type=EnclosureType.MAMMAL,
        zoo_id="zoo-1",
    )
    enc2 = Enclosure(
        id="enc-mammal-second",
        name="Second Mammal",
        enclosure_type=EnclosureType.MAMMAL,
        zoo_id="zoo-1",
    )
    repo.save(lion)
    repo.save(enc1)
    repo.save(enc2)

    use_case = AdmitAnimalUseCase(repo, repo, repo, repo, repo)
    req = AdmitAnimalRequest(animal_id="animal-lion-1", zoo_id="zoo-1")
    response = use_case.execute(req)

    assert response.enclosure_id == "enc-mammal-first"


def test_admission_record_has_zookeeper_id_from_enclosure() -> None:
    """AdmissionRecord.zookeeper_id comes from enclosure.assigned_zookeeper_id (ADR-004)."""
    repo = InMemoryRepositories()
    lion = Lion(id="animal-lion-1", name="Leo", origin=Origin.INTERNAL, enclosure_id=None)
    zk = Zookeeper(id="emp-zk-1", name="Alice", zoo_id="zoo-1")
    enc = Enclosure(
        id="enc-mammal-1",
        name="Mammal House",
        enclosure_type=EnclosureType.MAMMAL,
        zoo_id="zoo-1",
        assigned_zookeeper_id="emp-zk-1",
    )
    repo.save(lion)
    repo.save(zk)
    repo.save(enc)

    use_case = AdmitAnimalUseCase(repo, repo, repo, repo, repo)
    req = AdmitAnimalRequest(animal_id="animal-lion-1", zoo_id="zoo-1")
    use_case.execute(req)

    adm = list(repo._admission_records.values())[0]
    assert adm.zookeeper_id == "emp-zk-1"


def test_admission_record_has_none_zookeeper_when_enclosure_unassigned() -> None:
    """Enclosure with no zookeeper -> AdmissionRecord.zookeeper_id is None (ADR-004)."""
    repo = InMemoryRepositories()
    lion = Lion(id="animal-lion-1", name="Leo", origin=Origin.INTERNAL, enclosure_id=None)
    enc = Enclosure(
        id="enc-mammal-1",
        name="Mammal House",
        enclosure_type=EnclosureType.MAMMAL,
        zoo_id="zoo-1",
        assigned_zookeeper_id=None,
    )
    repo.save(lion)
    repo.save(enc)

    use_case = AdmitAnimalUseCase(repo, repo, repo, repo, repo)
    req = AdmitAnimalRequest(animal_id="animal-lion-1", zoo_id="zoo-1")
    use_case.execute(req)

    adm = list(repo._admission_records.values())[0]
    assert adm.zookeeper_id is None
