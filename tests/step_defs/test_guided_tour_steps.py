"""BDD step definitions for Conduct Guided Tour (Phase 7)."""

import ast
from typing import Any

import pytest
from pytest_bdd import given, parsers, scenario, then, when

from zoo_management.adapters.in_memory import InMemoryRepositories
from zoo_management.domain.entities import (
    Enclosure,
    EnclosureType,
    Guide,
    Zoo,
    Zookeeper,
)
from zoo_management.domain.exceptions import (
    GuideNotInZooError,
    InvalidEmployeeRoleError,
    NoGuideAvailableError,
)
from zoo_management.usecases.conduct_guided_tour import (
    ConductGuidedTourUseCase,
    GuidedTourRequest,
)


@pytest.fixture
def repos() -> InMemoryRepositories:
    """Fresh in-memory repositories per scenario (ADR-003 test isolation)."""
    return InMemoryRepositories()


# --- Scenario bindings ---


@scenario(
    "guided_tour.feature",
    "Guide successfully conducts tour through all enclosures",
)
def test_guide_conducts_tour_success() -> None:
    pass


@scenario(
    "guided_tour.feature",
    "Tour fails — guide not available",
)
def test_tour_fails_guide_not_available() -> None:
    pass


@scenario(
    "guided_tour.feature",
    "Tour fails — guide not in zoo (ADR-026)",
)
def test_tour_fails_guide_not_in_zoo() -> None:
    pass


@scenario(
    "guided_tour.feature",
    "Tour fails — employee is not a guide",
)
def test_tour_fails_employee_not_guide() -> None:
    pass


# --- Given steps ---


@given(parsers.parse('a guide "{guide_id}" is available in zoo "{zoo_id}"'))
def given_guide_available_in_zoo(
    guide_id: str, zoo_id: str, repos: InMemoryRepositories
) -> None:
    """Create guide (is_available=True) and zoo with empty route; use fresh repos."""
    guide = Guide(id=guide_id, name="Eve", zoo_id=zoo_id, is_available=True)
    zoo = Zoo(id=zoo_id, name="Main Zoo", tour_route=[])
    repos.seed_zoo(zoo)
    repos.save(guide)


@given(
    parsers.parse('zoo "{zoo_id}" has tour route {route}'),
    target_fixture="tour_route",
)
def given_zoo_has_tour_route(
    zoo_id: str, route: str, repos: InMemoryRepositories
) -> list[str]:
    """Set zoo tour_route to the parsed list (e.g. ["enc-1", "enc-2"])."""
    route_list = ast.literal_eval(route)
    zoo = repos._zoos[zoo_id]
    zoo.tour_route.clear()
    zoo.tour_route.extend(route_list)
    return route_list


@given(parsers.parse("all enclosures in the route exist"))
def given_all_enclosures_in_route_exist(
    repos: InMemoryRepositories, tour_route: list[str]
) -> None:
    """Create an Enclosure for each id in tour_route (same zoo as guide)."""
    # Zoo id from repos: use first zoo we have
    zoos = list(repos._zoos.values())
    zoo_id = zoos[0].id if zoos else "zoo-1"
    for enc_id in tour_route:
        repos.save(
            Enclosure(
                id=enc_id,
                name=enc_id.replace("-", " ").title(),
                enclosure_type=EnclosureType.MAMMAL,
                zoo_id=zoo_id,
            )
        )


@given(
    parsers.parse('a guide "{guide_id}" exists in zoo "{zoo_id}" but is not available')
)
def given_guide_exists_not_available(
    guide_id: str, zoo_id: str, repos: InMemoryRepositories
) -> None:
    """Create guide with is_available=False in fresh repos (ADR-003 isolation)."""
    guide = Guide(id=guide_id, name="Busy", zoo_id=zoo_id, is_available=False)
    zoo = Zoo(id=zoo_id, name="Z", tour_route=["enc-1"])
    repos.seed_zoo(zoo)
    repos.save(guide)
    repos.save(
        Enclosure(id="enc-1", name="M", enclosure_type=EnclosureType.MAMMAL, zoo_id=zoo_id)
    )


@given(parsers.parse('a guide "{guide_id}" exists in zoo "{zoo_id}"'))
def given_guide_exists_in_zoo(
    guide_id: str, zoo_id: str, repos: InMemoryRepositories
) -> None:
    """Create guide in given zoo (for guide-not-in-zoo scenario: other zoo)."""
    guide = Guide(id=guide_id, name="Other", zoo_id=zoo_id, is_available=True)
    zoo = Zoo(id=zoo_id, name="Other Zoo", tour_route=[])
    repos.seed_zoo(zoo)
    repos.save(guide)


@given(parsers.parse('a zookeeper "{zk_id}" exists in zoo "{zoo_id}"'))
def given_zookeeper_exists_in_zoo(
    zk_id: str, zoo_id: str, repos: InMemoryRepositories
) -> None:
    """Create zookeeper (for invalid-role scenario)."""
    zk = Zookeeper(id=zk_id, name="Jane", zoo_id=zoo_id)
    zoo = Zoo(id=zoo_id, name="Z", tour_route=["enc-1"])
    repos.seed_zoo(zoo)
    repos.save(zk)
    repos.save(
        Enclosure(id="enc-1", name="M", enclosure_type=EnclosureType.MAMMAL, zoo_id=zoo_id)
    )


# --- When steps ---


@when(
    parsers.parse('guide "{guide_id}" conducts a tour of zoo "{zoo_id}"'),
    target_fixture="tour_result",
)
def when_guide_conducts_tour(
    guide_id: str, zoo_id: str, repos: InMemoryRepositories
) -> dict[str, Any]:
    """Execute use case; capture response or error."""
    use_case = ConductGuidedTourUseCase(repos, repos, repos, repos)
    req = GuidedTourRequest(guide_id=guide_id, zoo_id=zoo_id)
    try:
        response = use_case.execute(req)
        return {"response": response, "error": None}
    except Exception as e:
        return {"response": None, "error": e}


@when(
    parsers.parse('guide "{guide_id}" attempts to conduct a tour of zoo "{zoo_id}"'),
    target_fixture="tour_result",
)
def when_guide_attempts_tour(
    guide_id: str, zoo_id: str, repos: InMemoryRepositories
) -> dict[str, Any]:
    """Attempt tour; capture error (e.g. NoGuideAvailableError)."""
    use_case = ConductGuidedTourUseCase(repos, repos, repos, repos)
    req = GuidedTourRequest(guide_id=guide_id, zoo_id=zoo_id)
    try:
        response = use_case.execute(req)
        return {"response": response, "error": None}
    except Exception as e:
        return {"response": None, "error": e}


@when(
    parsers.parse('zookeeper "{zk_id}" attempts to conduct a tour of zoo "{zoo_id}"'),
    target_fixture="tour_result",
)
def when_zookeeper_attempts_tour(
    zk_id: str, zoo_id: str, repos: InMemoryRepositories
) -> dict[str, Any]:
    """Zookeeper attempts tour (expect InvalidEmployeeRoleError)."""
    use_case = ConductGuidedTourUseCase(repos, repos, repos, repos)
    req = GuidedTourRequest(guide_id=zk_id, zoo_id=zoo_id)
    try:
        response = use_case.execute(req)
        return {"response": response, "error": None}
    except Exception as e:
        return {"response": None, "error": e}


# --- Then steps ---


@then(parsers.parse("a tour record is created with the full route"))
def then_tour_record_created_with_route(
    tour_result: dict[str, Any],
    repos: InMemoryRepositories,
    tour_route: list[str],
) -> None:
    """Assert tour saved and route matches (tour_route from Given step)."""
    assert tour_result["error"] is None
    assert tour_result["response"] is not None
    assert tour_result["response"].route == tour_route
    assert len(repos._tours) >= 1
    saved = next(iter(repos._tours.values()))
    assert saved.route == tour_route


@then(parsers.parse('the guide "{guide_id}" is no longer available'))
def then_guide_no_longer_available(
    guide_id: str, repos: InMemoryRepositories
) -> None:
    """Assert guide.is_available is False after tour."""
    emp = repos.get_by_id(guide_id)
    assert isinstance(emp, Guide)
    assert emp.is_available is False


@then(parsers.parse("the tour fails with NoGuideAvailableError"))
def then_tour_fails_no_guide_available(tour_result: dict[str, Any]) -> None:
    """Assert NoGuideAvailableError raised."""
    assert tour_result["response"] is None
    assert tour_result["error"] is not None
    assert isinstance(tour_result["error"], NoGuideAvailableError)


@then(parsers.parse("the tour fails with GuideNotInZooError"))
def then_tour_fails_guide_not_in_zoo(tour_result: dict[str, Any]) -> None:
    """Assert GuideNotInZooError raised (ADR-026)."""
    assert tour_result["response"] is None
    assert tour_result["error"] is not None
    assert isinstance(tour_result["error"], GuideNotInZooError)


@then(parsers.parse("the tour fails with InvalidEmployeeRoleError"))
def then_tour_fails_invalid_employee_role(tour_result: dict[str, Any]) -> None:
    """Assert InvalidEmployeeRoleError raised."""
    assert tour_result["response"] is None
    assert tour_result["error"] is not None
    assert isinstance(tour_result["error"], InvalidEmployeeRoleError)
