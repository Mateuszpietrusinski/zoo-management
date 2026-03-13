"""BDD step definitions for Execute Feeding Round (Phase 5)."""

from datetime import time
from typing import Any

import pytest
from pytest_bdd import given, parsers, scenario, then, when

from zoo_management.adapters.in_memory import InMemoryRepositories
from zoo_management.domain.entities import (
    Enclosure,
    EnclosureType,
    FeedingSchedule,
    Lion,
    Origin,
    Zookeeper,
)
from zoo_management.domain.exceptions import (
    FeedingNotDueError,
    ZookeeperNotAssignedError,
)
from zoo_management.usecases.execute_feeding_round import (
    ExecuteFeedingRoundUseCase,
    FeedingRoundRequest,
)


def _parse_time(s: str) -> time:
    """Parse time string HH:MM or HH:MM:SS to time."""
    parts = s.strip().split(":")
    h, m = int(parts[0]), int(parts[1])
    sec = int(parts[2]) if len(parts) > 2 else 0
    return time(h, m, sec)


@pytest.fixture
def repos() -> InMemoryRepositories:
    """Fresh in-memory repositories per scenario."""
    return InMemoryRepositories()


# --- Scenario bindings ---


@scenario(
    "feeding_round.feature",
    "Successfully execute feeding round with animals",
)
def test_feeding_round_success_with_animals() -> None:
    pass


@scenario(
    "feeding_round.feature",
    "Feeding round for empty enclosure",
)
def test_feeding_round_empty_enclosure() -> None:
    pass


@scenario(
    "feeding_round.feature",
    "Feeding fails — not due (time mismatch)",
)
def test_feeding_round_fails_not_due() -> None:
    pass


@scenario(
    "feeding_round.feature",
    "Feeding fails — zookeeper not assigned",
)
def test_feeding_round_fails_zookeeper_not_assigned() -> None:
    pass


# --- Given steps ---


@given(
    parsers.parse(
        'enclosure "{enclosure_id}" in zoo "{zoo_id}" has lion "{animal_id}"'
    ),
)
def given_enclosure_with_lion(
    enclosure_id: str,
    zoo_id: str,
    animal_id: str,
    repos: InMemoryRepositories,
) -> None:
    lion = Lion(
        id=animal_id,
        name="Leo",
        origin=Origin.INTERNAL,
        enclosure_id=enclosure_id,
    )
    enc = Enclosure(
        id=enclosure_id,
        name="Enclosure",
        enclosure_type=EnclosureType.MAMMAL,
        zoo_id=zoo_id,
        animals=[lion],
    )
    repos.save(lion)
    repos.save(enc)


@given(
    parsers.parse(
        'enclosure "{enclosure_id}" in zoo "{zoo_id}" has no animals'
    ),
)
def given_enclosure_empty(
    enclosure_id: str,
    zoo_id: str,
    repos: InMemoryRepositories,
) -> None:
    enc = Enclosure(
        id=enclosure_id,
        name="Enclosure",
        enclosure_type=EnclosureType.BIRD,
        zoo_id=zoo_id,
        animals=[],
    )
    repos.save(enc)


@given(
    parsers.parse(
        'zookeeper "{zookeeper_id}" is assigned to enclosure "{enclosure_id}"'
    ),
)
def given_zookeeper_assigned_to_enclosure(
    zookeeper_id: str,
    enclosure_id: str,
    repos: InMemoryRepositories,
) -> None:
    zk = Zookeeper(id=zookeeper_id, name="Zookeeper", zoo_id="zoo-1")
    repos.save(zk)
    enc = repos.get_by_id(enclosure_id)
    assert isinstance(enc, Enclosure)
    enc.assigned_zookeeper_id = zookeeper_id
    repos.save(enc)


@given(
    parsers.parse(
        'enclosure "{enclosure_id}" has zookeeper "{zookeeper_id}" assigned'
    ),
)
def given_enclosure_has_zookeeper_assigned(
    enclosure_id: str,
    zookeeper_id: str,
    repos: InMemoryRepositories,
) -> None:
    zk = Zookeeper(id=zookeeper_id, name="Other", zoo_id="zoo-1")
    enc = Enclosure(
        id=enclosure_id,
        name="Enclosure",
        enclosure_type=EnclosureType.MAMMAL,
        zoo_id="zoo-1",
        assigned_zookeeper_id=zookeeper_id,
        animals=[],
    )
    repos.save(zk)
    repos.save(enc)


@given(
    parsers.parse(
        'a feeding schedule exists for "{enclosure_id}" at "{time_str}" with diet "{diet}"'
    ),
)
def given_feeding_schedule_exists(
    enclosure_id: str,
    time_str: str,
    diet: str,
    repos: InMemoryRepositories,
) -> None:
    t = _parse_time(time_str)
    schedule = FeedingSchedule(
        id=f"sched-{enclosure_id}-{t!s}",
        enclosure_id=enclosure_id,
        scheduled_time=t,
        diet=diet,
    )
    repos.save(schedule)


@given(
    parsers.parse('a feeding schedule exists for "{enclosure_id}" at "{time_str}"'),
)
def given_feeding_schedule_exists_no_diet(
    enclosure_id: str,
    time_str: str,
    repos: InMemoryRepositories,
) -> None:
    t = _parse_time(time_str)
    schedule = FeedingSchedule(
        id=f"sched-{enclosure_id}-{t!s}",
        enclosure_id=enclosure_id,
        scheduled_time=t,
        diet="meat",
    )
    repos.save(schedule)


# --- When steps ---


@when(
    parsers.parse(
        'zookeeper "{zookeeper_id}" executes feeding round for "{enclosure_id}" at "{time_str}"'
    ),
    target_fixture="feeding_result",
)
def when_execute_feeding_round(
    zookeeper_id: str,
    enclosure_id: str,
    time_str: str,
    repos: InMemoryRepositories,
) -> dict[str, Any]:
    use_case = ExecuteFeedingRoundUseCase(repos, repos, repos)
    req = FeedingRoundRequest(
        enclosure_id=enclosure_id,
        zookeeper_id=zookeeper_id,
        current_time=_parse_time(time_str),
    )
    try:
        response = use_case.execute(req)
        return {"response": response, "error": None}
    except Exception as e:
        return {"response": None, "error": e}


@when(
    parsers.parse(
        'zookeeper "{zookeeper_id}" attempts feeding for "{enclosure_id}" at "{time_str}"'
    ),
    target_fixture="feeding_result",
)
def when_attempt_feeding(
    zookeeper_id: str,
    enclosure_id: str,
    time_str: str,
    repos: InMemoryRepositories,
) -> dict[str, Any]:
    use_case = ExecuteFeedingRoundUseCase(repos, repos, repos)
    req = FeedingRoundRequest(
        enclosure_id=enclosure_id,
        zookeeper_id=zookeeper_id,
        current_time=_parse_time(time_str),
    )
    try:
        response = use_case.execute(req)
        return {"response": response, "error": None}
    except Exception as e:
        return {"response": None, "error": e}


# --- Then steps ---


@then(
    parsers.parse(
        "the feeding round succeeds with fed_count {fed_count:d}"
    ),
)
def then_feeding_round_succeeds_with_count(
    fed_count: int,
    feeding_result: dict[str, Any],
) -> None:
    assert feeding_result["error"] is None
    assert feeding_result["response"] is not None
    assert feeding_result["response"].fed_count == fed_count


@then(
    parsers.parse('the note contains "{text}"'),
)
def then_note_contains(
    text: str,
    feeding_result: dict[str, Any],
) -> None:
    assert feeding_result["response"] is not None
    assert text in feeding_result["response"].note


@then(
    parsers.parse('the note is "{text}"'),
)
def then_note_equals(
    text: str,
    feeding_result: dict[str, Any],
) -> None:
    assert feeding_result["response"] is not None
    assert feeding_result["response"].note == text


@then(parsers.parse("the feeding fails with FeedingNotDueError"))
def then_fails_feeding_not_due(
    feeding_result: dict[str, Any],
) -> None:
    assert feeding_result["response"] is None
    assert feeding_result["error"] is not None
    assert isinstance(feeding_result["error"], FeedingNotDueError)


@then(parsers.parse("the feeding fails with ZookeeperNotAssignedError"))
def then_fails_zookeeper_not_assigned(
    feeding_result: dict[str, Any],
) -> None:
    assert feeding_result["response"] is None
    assert feeding_result["error"] is not None
    assert isinstance(feeding_result["error"], ZookeeperNotAssignedError)
