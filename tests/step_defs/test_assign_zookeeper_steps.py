"""BDD step definitions for Assign Zookeeper to Enclosure (Phase 3)."""

from typing import Any

import pytest
from pytest_bdd import given, parsers, scenario, then, when

from zoo_management.adapters.in_memory import InMemoryRepositories
from zoo_management.domain.entities import (
    Enclosure,
    EnclosureType,
    Guide,
    Zookeeper,
)
from zoo_management.domain.exceptions import (
    EnclosureNotInZooError,
    InvalidEmployeeRoleError,
)
from zoo_management.usecases.assign_zookeeper import (
    AssignZookeeperRequest,
    AssignZookeeperUseCase,
)


@pytest.fixture
def repos() -> InMemoryRepositories:
    """Fresh in-memory repositories per scenario."""
    return InMemoryRepositories()


# --- Scenario bindings ---


@scenario(
    "assign_zookeeper.feature",
    "Successfully assign zookeeper to enclosure",
)
def test_assign_zookeeper_success() -> None:
    pass


@scenario(
    "assign_zookeeper.feature",
    "Reassign enclosure to different zookeeper (idempotent, ADR-031)",
)
def test_assign_zookeeper_reassign() -> None:
    pass


@scenario("assign_zookeeper.feature", "Assignment fails — enclosure not in zoo")
def test_assign_zookeeper_fails_enclosure_not_in_zoo() -> None:
    pass


@scenario(
    "assign_zookeeper.feature",
    "Assignment fails — employee is not a zookeeper",
)
def test_assign_zookeeper_fails_invalid_role() -> None:
    pass


# --- Given steps ---


@given(parsers.parse('an enclosure "{enclosure_id}" exists in zoo "{zoo_id}"'))
def given_enclosure_exists(
    enclosure_id: str, zoo_id: str, repos: InMemoryRepositories
) -> None:
    enc = Enclosure(
        id=enclosure_id,
        name="Enclosure",
        enclosure_type=EnclosureType.MAMMAL,
        zoo_id=zoo_id,
    )
    repos.save(enc)


@given(
    parsers.parse(
        'an enclosure "{enclosure_id}" exists in zoo "{zoo_id}" '
        'with zookeeper "{zookeeper_id}" assigned'
    ),
)
def given_enclosure_with_zookeeper(
    enclosure_id: str,
    zoo_id: str,
    zookeeper_id: str,
    repos: InMemoryRepositories,
) -> None:
    enc = Enclosure(
        id=enclosure_id,
        name="Enclosure",
        enclosure_type=EnclosureType.MAMMAL,
        zoo_id=zoo_id,
        assigned_zookeeper_id=zookeeper_id,
    )
    zk = Zookeeper(id=zookeeper_id, name="Zookeeper", zoo_id=zoo_id)
    repos.save(enc)
    repos.save(zk)


@given(parsers.parse('a zookeeper "{zookeeper_id}" exists in zoo "{zoo_id}"'))
def given_zookeeper_exists(
    zookeeper_id: str, zoo_id: str, repos: InMemoryRepositories
) -> None:
    zk = Zookeeper(id=zookeeper_id, name="Zookeeper", zoo_id=zoo_id)
    repos.save(zk)


@given(parsers.parse('a guide "{guide_id}" exists in zoo "{zoo_id}"'))
def given_guide_exists(
    guide_id: str, zoo_id: str, repos: InMemoryRepositories
) -> None:
    guide = Guide(id=guide_id, name="Guide", zoo_id=zoo_id)
    repos.save(guide)


# --- When steps ---


@when(
    parsers.parse(
        'the zoo assigns zookeeper "{zookeeper_id}" to enclosure "{enclosure_id}" in zoo "{zoo_id}"'
    ),
    target_fixture="assignment_result",
)
def when_assign(
    zookeeper_id: str,
    enclosure_id: str,
    zoo_id: str,
    repos: InMemoryRepositories,
) -> dict[str, Any]:
    use_case = AssignZookeeperUseCase(repos, repos)
    req = AssignZookeeperRequest(
        zoo_id=zoo_id,
        enclosure_id=enclosure_id,
        zookeeper_id=zookeeper_id,
    )
    try:
        response = use_case.execute(req)
        return {"response": response, "error": None}
    except Exception as e:
        return {"response": None, "error": e}


@when(
    parsers.parse(
        'the zoo attempts to assign zookeeper "{zookeeper_id}" '
        'to enclosure "{enclosure_id}" in zoo "{zoo_id}"'
    ),
    target_fixture="assignment_result",
)
def when_attempt_assign_zookeeper(
    zookeeper_id: str,
    enclosure_id: str,
    zoo_id: str,
    repos: InMemoryRepositories,
) -> dict[str, Any]:
    use_case = AssignZookeeperUseCase(repos, repos)
    req = AssignZookeeperRequest(
        zoo_id=zoo_id,
        enclosure_id=enclosure_id,
        zookeeper_id=zookeeper_id,
    )
    try:
        response = use_case.execute(req)
        return {"response": response, "error": None}
    except Exception as e:
        return {"response": None, "error": e}


@when(
    parsers.parse(
        'the zoo attempts to assign employee "{employee_id}" as zookeeper '
        'to enclosure "{enclosure_id}" in zoo "{zoo_id}"'
    ),
    target_fixture="assignment_result",
)
def when_attempt_assign_employee(
    employee_id: str,
    enclosure_id: str,
    zoo_id: str,
    repos: InMemoryRepositories,
) -> dict[str, Any]:
    use_case = AssignZookeeperUseCase(repos, repos)
    req = AssignZookeeperRequest(
        zoo_id=zoo_id,
        enclosure_id=enclosure_id,
        zookeeper_id=employee_id,
    )
    try:
        response = use_case.execute(req)
        return {"response": response, "error": None}
    except Exception as e:
        return {"response": None, "error": e}


# --- Then steps ---


@then(
    parsers.parse(
        'enclosure "{enclosure_id}" has zookeeper "{zookeeper_id}" assigned'
    ),
)
def then_enclosure_has_zookeeper(
    enclosure_id: str,
    zookeeper_id: str,
    repos: InMemoryRepositories,
    assignment_result: dict[str, Any],
) -> None:
    assert assignment_result["error"] is None
    assert assignment_result["response"] is not None
    assert assignment_result["response"].enclosure_id == enclosure_id
    assert assignment_result["response"].zookeeper_id == zookeeper_id
    stored = repos.get_by_id(enclosure_id)
    assert isinstance(stored, Enclosure)
    assert stored.assigned_zookeeper_id == zookeeper_id


@then(parsers.parse("the assignment fails with EnclosureNotInZooError"))
def then_fails_enclosure_not_in_zoo(
    assignment_result: dict[str, Any],
) -> None:
    assert assignment_result["response"] is None
    assert assignment_result["error"] is not None
    assert isinstance(assignment_result["error"], EnclosureNotInZooError)


@then(parsers.parse("the assignment fails with InvalidEmployeeRoleError"))
def then_fails_invalid_employee_role(
    assignment_result: dict[str, Any],
) -> None:
    assert assignment_result["response"] is None
    assert assignment_result["error"] is not None
    assert isinstance(assignment_result["error"], InvalidEmployeeRoleError)
