"""Unit tests for ConductGuidedTourUseCase (Phase 7)."""

from datetime import datetime
from unittest.mock import patch

import pytest

from zoo_management.adapters.in_memory import InMemoryRepositories
from zoo_management.domain.entities import (
    Enclosure,
    EnclosureType,
    Guide,
    Tour,
    Zoo,
    Zookeeper,
)
from zoo_management.domain.exceptions import (
    EntityNotFoundError,
    GuideNotInZooError,
    InvalidEmployeeRoleError,
    NoGuideAvailableError,
)
from zoo_management.usecases.conduct_guided_tour import (
    ConductGuidedTourUseCase,
    GuidedTourRequest,
)


def test_guided_tour_happy_path() -> None:
    """Guide available, zoo with route, enclosures exist; tour created, guide unavailable."""
    repo = InMemoryRepositories()
    guide = Guide(
        id="emp-guide-1",
        name="Eve",
        zoo_id="zoo-1",
        is_available=True,
    )
    zoo = Zoo(
        id="zoo-1",
        name="Main Zoo",
        tour_route=["enc-1", "enc-2"],
    )
    repo.seed_zoo(zoo)
    repo.save(guide)
    repo.save(
        Enclosure(
            id="enc-1",
            name="Mammal",
            enclosure_type=EnclosureType.MAMMAL,
            zoo_id="zoo-1",
        )
    )
    repo.save(
        Enclosure(
            id="enc-2",
            name="Bird",
            enclosure_type=EnclosureType.BIRD,
            zoo_id="zoo-1",
        )
    )

    use_case = ConductGuidedTourUseCase(repo, repo, repo, repo)
    req = GuidedTourRequest(guide_id="emp-guide-1", zoo_id="zoo-1")
    with patch("zoo_management.usecases.conduct_guided_tour.datetime") as m_dt:
        m_dt.now.return_value = datetime(2025, 3, 10, 14, 0, 0)
        response = use_case.execute(req)

    assert response.tour_id
    assert response.route == ["enc-1", "enc-2"]
    assert response.start_time == datetime(2025, 3, 10, 14, 0, 0)
    assert response.end_time == datetime(2025, 3, 10, 14, 0, 0)
    saved_tour = repo._tours.get(response.tour_id)
    assert saved_tour is not None
    assert saved_tour.guide_id == "emp-guide-1"
    assert saved_tour.route == ["enc-1", "enc-2"]
    updated_guide = repo.get_by_id("emp-guide-1")
    assert isinstance(updated_guide, Guide)
    assert updated_guide.is_available is False


def test_guided_tour_start_time_equals_end_time() -> None:
    """ADR-011: response.start_time == response.end_time."""
    repo = InMemoryRepositories()
    guide = Guide(id="g1", name="Eve", zoo_id="zoo-1", is_available=True)
    zoo = Zoo(id="zoo-1", name="Z", tour_route=["enc-1"])
    repo.seed_zoo(zoo)
    repo.save(guide)
    repo.save(
        Enclosure(id="enc-1", name="M", enclosure_type=EnclosureType.MAMMAL, zoo_id="zoo-1")
    )

    use_case = ConductGuidedTourUseCase(repo, repo, repo, repo)
    req = GuidedTourRequest(guide_id="g1", zoo_id="zoo-1")
    response = use_case.execute(req)

    assert response.start_time == response.end_time


def test_guided_tour_guide_becomes_unavailable_after_tour() -> None:
    """ADR-003: After execute, employee_repo.get_by_id(guide_id).is_available is False."""
    repo = InMemoryRepositories()
    guide = Guide(id="g1", name="Eve", zoo_id="zoo-1", is_available=True)
    zoo = Zoo(id="zoo-1", name="Z", tour_route=["enc-1"])
    repo.seed_zoo(zoo)
    repo.save(guide)
    repo.save(
        Enclosure(id="enc-1", name="M", enclosure_type=EnclosureType.MAMMAL, zoo_id="zoo-1")
    )

    use_case = ConductGuidedTourUseCase(repo, repo, repo, repo)
    use_case.execute(GuidedTourRequest(guide_id="g1", zoo_id="zoo-1"))

    emp = repo.get_by_id("g1")
    assert isinstance(emp, Guide)
    assert emp.is_available is False


def test_guided_tour_raises_no_guide_available_when_not_available() -> None:
    """Guide is_available=False -> NoGuideAvailableError."""
    repo = InMemoryRepositories()
    guide = Guide(id="g1", name="Eve", zoo_id="zoo-1", is_available=False)
    zoo = Zoo(id="zoo-1", name="Z", tour_route=["enc-1"])
    repo.seed_zoo(zoo)
    repo.save(guide)
    repo.save(
        Enclosure(id="enc-1", name="M", enclosure_type=EnclosureType.MAMMAL, zoo_id="zoo-1")
    )

    use_case = ConductGuidedTourUseCase(repo, repo, repo, repo)
    req = GuidedTourRequest(guide_id="g1", zoo_id="zoo-1")

    with pytest.raises(NoGuideAvailableError):
        use_case.execute(req)


def test_guided_tour_raises_guide_not_in_zoo_when_zoo_mismatch() -> None:
    """Guide zoo_id != request zoo_id -> GuideNotInZooError (ADR-026)."""
    repo = InMemoryRepositories()
    guide = Guide(id="g1", name="Eve", zoo_id="zoo-other", is_available=True)
    zoo = Zoo(id="zoo-1", name="Z", tour_route=["enc-1"])
    repo.seed_zoo(zoo)
    repo.save(guide)
    repo.save(
        Enclosure(id="enc-1", name="M", enclosure_type=EnclosureType.MAMMAL, zoo_id="zoo-1")
    )

    use_case = ConductGuidedTourUseCase(repo, repo, repo, repo)
    req = GuidedTourRequest(guide_id="g1", zoo_id="zoo-1")

    with pytest.raises(GuideNotInZooError):
        use_case.execute(req)


def test_guided_tour_raises_invalid_employee_role_for_non_guide() -> None:
    """Zookeeper id as guide_id -> InvalidEmployeeRoleError."""
    repo = InMemoryRepositories()
    zk = Zookeeper(id="emp-zk-1", name="Jane", zoo_id="zoo-1")
    zoo = Zoo(id="zoo-1", name="Z", tour_route=["enc-1"])
    repo.seed_zoo(zoo)
    repo.save(zk)
    repo.save(
        Enclosure(id="enc-1", name="M", enclosure_type=EnclosureType.MAMMAL, zoo_id="zoo-1")
    )

    use_case = ConductGuidedTourUseCase(repo, repo, repo, repo)
    req = GuidedTourRequest(guide_id="emp-zk-1", zoo_id="zoo-1")

    with pytest.raises(InvalidEmployeeRoleError):
        use_case.execute(req)


def test_guided_tour_raises_entity_not_found_for_missing_guide() -> None:
    """Guide id not in repo -> EntityNotFoundError."""
    repo = InMemoryRepositories()
    zoo = Zoo(id="zoo-1", name="Z", tour_route=[])
    repo.seed_zoo(zoo)

    use_case = ConductGuidedTourUseCase(repo, repo, repo, repo)
    req = GuidedTourRequest(guide_id="missing-guide", zoo_id="zoo-1")

    with pytest.raises(EntityNotFoundError):
        use_case.execute(req)


def test_guided_tour_raises_entity_not_found_for_missing_zoo() -> None:
    """Zoo id not in repo -> EntityNotFoundError (guide exists, zoo not seeded)."""
    repo = InMemoryRepositories()
    guide = Guide(id="g1", name="Eve", zoo_id="missing-zoo", is_available=True)
    repo.save(guide)
    # Zoo "missing-zoo" not in repo so zoo_repo.get_by_id raises

    use_case = ConductGuidedTourUseCase(repo, repo, repo, repo)
    req = GuidedTourRequest(guide_id="g1", zoo_id="missing-zoo")

    with pytest.raises(EntityNotFoundError):
        use_case.execute(req)


def test_guided_tour_raises_entity_not_found_for_missing_enclosure_in_route() -> None:
    """Zoo tour_route contains enclosure id not in repo -> EntityNotFoundError."""
    repo = InMemoryRepositories()
    guide = Guide(id="g1", name="Eve", zoo_id="zoo-1", is_available=True)
    zoo = Zoo(id="zoo-1", name="Z", tour_route=["enc-nonexistent"])
    repo.seed_zoo(zoo)
    repo.save(guide)

    use_case = ConductGuidedTourUseCase(repo, repo, repo, repo)
    req = GuidedTourRequest(guide_id="g1", zoo_id="zoo-1")

    with pytest.raises(EntityNotFoundError):
        use_case.execute(req)


def test_guided_tour_bdd_isolation_no_guide_available_uses_fresh_state() -> None:
    """Test with Guide(is_available=False) is independent of other tests (fresh repo)."""
    repo = InMemoryRepositories()
    guide = Guide(id="emp-guide-busy", name="Busy", zoo_id="zoo-1", is_available=False)
    zoo = Zoo(id="zoo-1", name="Z", tour_route=["enc-1"])
    repo.seed_zoo(zoo)
    repo.save(guide)
    repo.save(
        Enclosure(id="enc-1", name="M", enclosure_type=EnclosureType.MAMMAL, zoo_id="zoo-1")
    )

    use_case = ConductGuidedTourUseCase(repo, repo, repo, repo)
    req = GuidedTourRequest(guide_id="emp-guide-busy", zoo_id="zoo-1")

    with pytest.raises(NoGuideAvailableError):
        use_case.execute(req)

    # State is isolated: only this scenario's guide, no other test toggled it
    emp = repo.get_by_id("emp-guide-busy")
    assert isinstance(emp, Guide)
    assert emp.is_available is False
