"""BDD step definitions for Animal Admission to Enclosure (Phase 4)."""

from typing import Any

import pytest
from pytest_bdd import given, parsers, scenario, then, when

from zoo_management.adapters.in_memory import InMemoryRepositories
from zoo_management.domain.entities import (
    Crocodile,
    Enclosure,
    EnclosureType,
    Lion,
    Origin,
    Penguin,
    Veterinarian,
)
from zoo_management.domain.exceptions import (
    AnimalAlreadyPlacedError,
    HealthCheckNotClearedError,
    NoSuitableEnclosureError,
)
from zoo_management.usecases.admit_animal import (
    AdmitAnimalRequest,
    AdmitAnimalUseCase,
)


@pytest.fixture
def repos() -> InMemoryRepositories:
    """Fresh in-memory repositories per scenario."""
    return InMemoryRepositories()


# --- Scenario bindings ---


@scenario(
    "animal_admission.feature",
    "Admit internal animal without health check",
)
def test_admit_internal_animal_without_health_check() -> None:
    pass


@scenario(
    "animal_admission.feature",
    "Admit external animal with health check — cleared",
)
def test_admit_external_animal_with_health_check_cleared() -> None:
    pass


@scenario(
    "animal_admission.feature",
    "Admit external animal fails — not cleared",
)
def test_admit_external_animal_fails_not_cleared() -> None:
    pass


@scenario(
    "animal_admission.feature",
    "Admission fails — no suitable enclosure",
)
def test_admission_fails_no_suitable_enclosure() -> None:
    pass


@scenario(
    "animal_admission.feature",
    "Admission fails — animal already placed (ADR-013)",
)
def test_admission_fails_animal_already_placed() -> None:
    pass


# --- Given steps ---


@given(
    parsers.parse('an internal lion "{animal_id}" exists but is not placed'),
)
def given_internal_lion_not_placed(
    animal_id: str, repos: InMemoryRepositories
) -> None:
    lion = Lion(id=animal_id, name="Leo", origin=Origin.INTERNAL, enclosure_id=None)
    repos.save(lion)


@given(
    parsers.parse('a mammal enclosure "{enclosure_id}" exists in zoo "{zoo_id}"'),
)
def given_mammal_enclosure_exists(
    enclosure_id: str, zoo_id: str, repos: InMemoryRepositories
) -> None:
    enc = Enclosure(
        id=enclosure_id,
        name="Mammal House",
        enclosure_type=EnclosureType.MAMMAL,
        zoo_id=zoo_id,
    )
    repos.save(enc)


@given(
    parsers.parse('an external penguin "{animal_id}" exists but is not placed'),
)
def given_external_penguin_not_placed(
    animal_id: str, repos: InMemoryRepositories
) -> None:
    penguin = Penguin(
        id=animal_id, name="Pingu", origin=Origin.EXTERNAL, enclosure_id=None
    )
    repos.save(penguin)


@given(
    parsers.parse('a bird enclosure "{enclosure_id}" exists in zoo "{zoo_id}"'),
)
def given_bird_enclosure_exists(
    enclosure_id: str, zoo_id: str, repos: InMemoryRepositories
) -> None:
    enc = Enclosure(
        id=enclosure_id,
        name="Bird House",
        enclosure_type=EnclosureType.BIRD,
        zoo_id=zoo_id,
    )
    repos.save(enc)


@given(parsers.parse('a veterinarian "{vet_id}" exists in zoo "{zoo_id}"'))
def given_veterinarian_exists(
    vet_id: str, zoo_id: str, repos: InMemoryRepositories
) -> None:
    vet = Veterinarian(id=vet_id, name="Dr. Bob", zoo_id=zoo_id)
    repos.save(vet)


@given(
    parsers.parse('an external lion "{animal_id}" exists but is not placed'),
)
def given_external_lion_not_placed(
    animal_id: str, repos: InMemoryRepositories
) -> None:
    lion = Lion(id=animal_id, name="Scar", origin=Origin.EXTERNAL, enclosure_id=None)
    repos.save(lion)


@given(
    parsers.parse('an internal crocodile "{animal_id}" exists but is not placed'),
)
def given_internal_crocodile_not_placed(
    animal_id: str, repos: InMemoryRepositories
) -> None:
    croc = Crocodile(
        id=animal_id, name="Snappy", origin=Origin.INTERNAL, enclosure_id=None
    )
    repos.save(croc)


@given(parsers.parse('no reptile enclosure exists in zoo "{zoo_id}"'))
def given_no_reptile_enclosure(zoo_id: str, repos: InMemoryRepositories) -> None:
    # No reptile enclosure saved for this zoo — get_by_zoo will return [] or only non-reptile
    pass


@given(
    parsers.parse('a lion "{animal_id}" already placed in enclosure "{enclosure_id}"'),
)
def given_lion_already_placed(
    animal_id: str, enclosure_id: str, repos: InMemoryRepositories
) -> None:
    lion = Lion(
        id=animal_id,
        name="Leo",
        origin=Origin.INTERNAL,
        enclosure_id=enclosure_id,
    )
    enc = Enclosure(
        id=enclosure_id,
        name="Mammal House",
        enclosure_type=EnclosureType.MAMMAL,
        zoo_id="zoo-1",
    )
    enc.animals.append(lion)
    repos.save(lion)
    repos.save(enc)


# --- When steps ---


@when(
    parsers.parse('the zoo admits animal "{animal_id}" to zoo "{zoo_id}"'),
    target_fixture="admission_result",
)
def when_admit_animal(
    animal_id: str, zoo_id: str, repos: InMemoryRepositories
) -> dict[str, Any]:
    use_case = AdmitAnimalUseCase(repos, repos, repos, repos, repos)
    req = AdmitAnimalRequest(animal_id=animal_id, zoo_id=zoo_id)
    try:
        response = use_case.execute(req)
        return {"response": response, "error": None}
    except Exception as e:
        return {"response": None, "error": e}


@when(
    parsers.parse(
        'the zoo admits animal "{animal_id}" to zoo "{zoo_id}" '
        'with vet "{vet_id}" result "{health_result}"'
    ),
    target_fixture="admission_result",
)
def when_admit_animal_with_vet(
    animal_id: str,
    zoo_id: str,
    vet_id: str,
    health_result: str,
    repos: InMemoryRepositories,
) -> dict[str, Any]:
    from zoo_management.domain.entities import HealthResult

    result_enum = HealthResult(health_result.lower())
    use_case = AdmitAnimalUseCase(repos, repos, repos, repos, repos)
    req = AdmitAnimalRequest(
        animal_id=animal_id,
        zoo_id=zoo_id,
        vet_id=vet_id,
        health_check_result=result_enum,
    )
    try:
        response = use_case.execute(req)
        return {"response": response, "error": None}
    except Exception as e:
        return {"response": None, "error": e}


@when(
    parsers.parse(
        'the zoo attempts to admit "{animal_id}" with vet "{vet_id}" result "{health_result}"'
    ),
    target_fixture="admission_result",
)
def when_attempt_admit_with_vet(
    animal_id: str,
    vet_id: str,
    health_result: str,
    repos: InMemoryRepositories,
) -> dict[str, Any]:
    from zoo_management.domain.entities import HealthResult

    result_enum = HealthResult(health_result.lower())
    use_case = AdmitAnimalUseCase(repos, repos, repos, repos, repos)
    req = AdmitAnimalRequest(
        animal_id=animal_id,
        zoo_id="zoo-1",
        vet_id=vet_id,
        health_check_result=result_enum,
    )
    try:
        response = use_case.execute(req)
        return {"response": response, "error": None}
    except Exception as e:
        return {"response": None, "error": e}


@when(
    parsers.parse('the zoo attempts to admit "{animal_id}" to zoo "{zoo_id}"'),
    target_fixture="admission_result",
)
def when_attempt_admit(
    animal_id: str, zoo_id: str, repos: InMemoryRepositories
) -> dict[str, Any]:
    use_case = AdmitAnimalUseCase(repos, repos, repos, repos, repos)
    req = AdmitAnimalRequest(animal_id=animal_id, zoo_id=zoo_id)
    try:
        response = use_case.execute(req)
        return {"response": response, "error": None}
    except Exception as e:
        return {"response": None, "error": e}


# --- Then steps ---


@then(
    parsers.parse('the animal is placed in enclosure "{enclosure_id}"'),
)
def then_animal_placed_in_enclosure(
    enclosure_id: str,
    repos: InMemoryRepositories,
    admission_result: dict[str, Any],
) -> None:
    assert admission_result["error"] is None
    assert admission_result["response"] is not None
    assert admission_result["response"].enclosure_id == enclosure_id


@then(parsers.parse("an admission record is created"))
def then_admission_record_created(
    repos: InMemoryRepositories,
    admission_result: dict[str, Any],
) -> None:
    assert admission_result["error"] is None
    assert admission_result["response"] is not None
    assert len(repos._admission_records) >= 1


@then(
    parsers.parse("an admission record is created with health_check_record_id"),
)
def then_admission_record_has_health_check_id(
    repos: InMemoryRepositories,
    admission_result: dict[str, Any],
) -> None:
    assert admission_result["error"] is None
    assert admission_result["response"] is not None
    records = list(repos._admission_records.values())
    assert any(r.health_check_record_id is not None for r in records)


@then(parsers.parse("a health check record is created"))
def then_health_check_record_created(
    repos: InMemoryRepositories,
    admission_result: dict[str, Any],
) -> None:
    assert admission_result["error"] is None
    assert len(repos._health_records) >= 1


@then(parsers.parse("the admission fails with HealthCheckNotClearedError"))
def then_fails_health_check_not_cleared(
    admission_result: dict[str, Any],
) -> None:
    assert admission_result["response"] is None
    assert admission_result["error"] is not None
    assert isinstance(admission_result["error"], HealthCheckNotClearedError)


@then(parsers.parse("the animal remains unplaced"))
def then_animal_remains_unplaced(
    admission_result: dict[str, Any],
) -> None:
    # Error was raised so no placement occurred
    assert admission_result["response"] is None


@then(parsers.parse("the admission fails with NoSuitableEnclosureError"))
def then_fails_no_suitable_enclosure(
    admission_result: dict[str, Any],
) -> None:
    assert admission_result["response"] is None
    assert admission_result["error"] is not None
    assert isinstance(admission_result["error"], NoSuitableEnclosureError)


@then(parsers.parse("the admission fails with AnimalAlreadyPlacedError"))
def then_fails_animal_already_placed(
    admission_result: dict[str, Any],
) -> None:
    assert admission_result["response"] is None
    assert admission_result["error"] is not None
    assert isinstance(admission_result["error"], AnimalAlreadyPlacedError)
