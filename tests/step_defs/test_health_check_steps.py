"""BDD step definitions for Conduct Health Check (Phase 6)."""

from typing import Any

import pytest
from pytest_bdd import given, parsers, scenario, then, when

from zoo_management.adapters.in_memory import InMemoryRepositories
from zoo_management.domain.entities import (
    Animal,
    HealthResult,
    Lion,
    Origin,
    Penguin,
    Veterinarian,
    Zookeeper,
)
from zoo_management.domain.exceptions import InvalidEmployeeRoleError
from zoo_management.usecases.conduct_health_check import (
    ConductHealthCheckUseCase,
    HealthCheckRequest,
)


@pytest.fixture
def repos() -> InMemoryRepositories:
    """Fresh in-memory repositories per scenario."""
    return InMemoryRepositories()


# --- Scenario bindings ---


@scenario(
    "health_check.feature",
    "Health check result is Healthy",
)
def test_health_check_result_healthy() -> None:
    pass


@scenario(
    "health_check.feature",
    "Health check result is Need Follow-Up",
)
def test_health_check_result_need_follow_up() -> None:
    pass


@scenario(
    "health_check.feature",
    "Health check result is Critical",
)
def test_health_check_result_critical() -> None:
    pass


@scenario(
    "health_check.feature",
    "Health check fails — employee is not a veterinarian",
)
def test_health_check_fails_non_vet() -> None:
    pass


# --- Given steps ---


@given(parsers.parse('an animal "{animal_id}" exists in the system'))
def given_animal_exists(
    animal_id: str, repos: InMemoryRepositories
) -> None:
    """Create a lion or penguin based on animal_id (e.g. animal-penguin-1 -> Penguin)."""
    animal: Animal
    if "penguin" in animal_id:
        animal = Penguin(
            id=animal_id,
            name="Pingu",
            origin=Origin.INTERNAL,
            enclosure_id=None,
        )
    else:
        animal = Lion(
            id=animal_id,
            name="Leo",
            origin=Origin.INTERNAL,
            enclosure_id=None,
        )
    repos.save(animal)


@given(parsers.parse('a veterinarian "{vet_id}" exists in the system'))
def given_veterinarian_exists(
    vet_id: str, repos: InMemoryRepositories
) -> None:
    vet = Veterinarian(id=vet_id, name="Dr. Bob", zoo_id="zoo-1")
    repos.save(vet)


@given(parsers.parse('a zookeeper "{zk_id}" exists in the system'))
def given_zookeeper_exists(
    zk_id: str, repos: InMemoryRepositories
) -> None:
    zk = Zookeeper(id=zk_id, name="Jane", zoo_id="zoo-1")
    repos.save(zk)


# --- When steps ---


@when(
    parsers.parse(
        'veterinarian "{vet_id}" conducts a health check on "{animal_id}" with result "{result}"'
    ),
    target_fixture="health_check_result",
)
def when_vet_conducts_health_check(
    vet_id: str,
    animal_id: str,
    result: str,
    repos: InMemoryRepositories,
) -> dict[str, Any]:
    result_enum = HealthResult(result.lower())
    use_case = ConductHealthCheckUseCase(repos, repos, repos)
    req = HealthCheckRequest(
        animal_id=animal_id,
        vet_id=vet_id,
        result=result_enum,
        notes=None,
    )
    try:
        response = use_case.execute(req)
        return {"response": response, "error": None}
    except Exception as e:
        return {"response": None, "error": e}


@when(
    parsers.parse(
        'zookeeper "{zk_id}" attempts to conduct a health check on "{animal_id}"'
    ),
    target_fixture="health_check_result",
)
def when_zookeeper_attempts_health_check(
    zk_id: str,
    animal_id: str,
    repos: InMemoryRepositories,
) -> dict[str, Any]:
    """Zookeeper attempts health check (expect InvalidEmployeeRoleError)."""
    use_case = ConductHealthCheckUseCase(repos, repos, repos)
    req = HealthCheckRequest(
        animal_id=animal_id,
        vet_id=zk_id,  # passing zookeeper id as vet_id
        result=HealthResult.HEALTHY,
        notes=None,
    )
    try:
        response = use_case.execute(req)
        return {"response": response, "error": None}
    except Exception as e:
        return {"response": None, "error": e}


# --- Then steps ---


@then(
    parsers.parse('a health check record is created with result "{result}"'),
)
def then_health_check_record_created_with_result(
    result: str,
    repos: InMemoryRepositories,
    health_check_result: dict[str, Any],
) -> None:
    assert health_check_result["error"] is None
    assert health_check_result["response"] is not None
    assert len(repos._health_records) >= 1
    record = next(iter(repos._health_records.values()))
    assert record.result.value == result


@then(parsers.parse("the health check fails with InvalidEmployeeRoleError"))
def then_health_check_fails_invalid_role(
    health_check_result: dict[str, Any],
) -> None:
    assert health_check_result["response"] is None
    assert health_check_result["error"] is not None
    assert isinstance(health_check_result["error"], InvalidEmployeeRoleError)
