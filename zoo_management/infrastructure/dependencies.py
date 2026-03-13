"""Dependency injection for FastAPI (use cases and repository singleton)."""

from zoo_management.adapters.in_memory import InMemoryRepositories
from zoo_management.usecases.admit_animal import AdmitAnimalUseCase
from zoo_management.usecases.assign_zookeeper import AssignZookeeperUseCase
from zoo_management.usecases.conduct_guided_tour import ConductGuidedTourUseCase
from zoo_management.usecases.conduct_health_check import ConductHealthCheckUseCase
from zoo_management.usecases.execute_feeding_round import ExecuteFeedingRoundUseCase

# Singleton repo instance — created once, reused across requests
_repo: InMemoryRepositories | None = None


def get_repository() -> InMemoryRepositories:
    """Return the singleton InMemoryRepositories instance (lazy init).

    Returns:
        The shared repository instance.
    """
    global _repo
    if _repo is None:
        _repo = InMemoryRepositories()
    return _repo


def set_repository(repo: InMemoryRepositories) -> None:
    """Set the repository instance (used by main.py after seeding).

    Args:
        repo: Seeded InMemoryRepositories instance.
    """
    global _repo
    _repo = repo


def get_repositories() -> InMemoryRepositories:
    """Alias for get_repository for backward compatibility with routers.

    Returns:
        The shared repository instance.
    """
    return get_repository()


def get_assign_zookeeper_use_case() -> AssignZookeeperUseCase:
    """Provide AssignZookeeperUseCase with repository dependencies.

    Returns:
        Configured AssignZookeeperUseCase instance.
    """
    repo = get_repository()
    return AssignZookeeperUseCase(enclosure_repo=repo, employee_repo=repo)


def get_admit_animal_use_case() -> AdmitAnimalUseCase:
    """Provide AdmitAnimalUseCase with repository dependencies.

    Returns:
        Configured AdmitAnimalUseCase instance.
    """
    repo = get_repository()
    return AdmitAnimalUseCase(
        animal_repo=repo,
        enclosure_repo=repo,
        employee_repo=repo,
        admission_repo=repo,
        health_repo=repo,
    )


def get_execute_feeding_round_use_case() -> ExecuteFeedingRoundUseCase:
    """Provide ExecuteFeedingRoundUseCase with repository dependencies.

    Returns:
        Configured ExecuteFeedingRoundUseCase instance.
    """
    repo = get_repository()
    return ExecuteFeedingRoundUseCase(
        enclosure_repo=repo,
        employee_repo=repo,
        schedule_repo=repo,
    )


def get_conduct_health_check_use_case() -> ConductHealthCheckUseCase:
    """Provide ConductHealthCheckUseCase with repository dependencies.

    Returns:
        Configured ConductHealthCheckUseCase instance.
    """
    repo = get_repository()
    return ConductHealthCheckUseCase(
        animal_repo=repo,
        employee_repo=repo,
        health_repo=repo,
    )


def get_conduct_guided_tour_use_case() -> ConductGuidedTourUseCase:
    """Provide ConductGuidedTourUseCase with repository dependencies.

    Returns:
        Configured ConductGuidedTourUseCase instance.
    """
    repo = get_repository()
    return ConductGuidedTourUseCase(
        zoo_repo=repo,
        enclosure_repo=repo,
        employee_repo=repo,
        tour_repo=repo,
    )
