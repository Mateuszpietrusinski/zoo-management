"""Port compliance tests: InMemoryRepositories satisfies all 8 repository ports."""

from zoo_management.adapters.in_memory import InMemoryRepositories
from zoo_management.domain.interfaces import (
    AdmissionRecordRepository,
    AnimalRepository,
    EmployeeRepository,
    EnclosureRepository,
    FeedingScheduleRepository,
    HealthCheckRecordRepository,
    TourRepository,
    ZooRepository,
)


def test_in_memory_repositories_is_instance_of_zoo_repository() -> None:
    assert isinstance(InMemoryRepositories(), ZooRepository)


def test_in_memory_repositories_is_instance_of_enclosure_repository() -> None:
    assert isinstance(InMemoryRepositories(), EnclosureRepository)


def test_in_memory_repositories_is_instance_of_animal_repository() -> None:
    assert isinstance(InMemoryRepositories(), AnimalRepository)


def test_in_memory_repositories_is_instance_of_employee_repository() -> None:
    assert isinstance(InMemoryRepositories(), EmployeeRepository)


def test_in_memory_repositories_is_instance_of_feeding_schedule_repository() -> None:
    assert isinstance(InMemoryRepositories(), FeedingScheduleRepository)


def test_in_memory_repositories_is_instance_of_admission_record_repository() -> None:
    assert isinstance(InMemoryRepositories(), AdmissionRecordRepository)


def test_in_memory_repositories_is_instance_of_health_check_record_repository() -> None:
    assert isinstance(InMemoryRepositories(), HealthCheckRecordRepository)


def test_in_memory_repositories_is_instance_of_tour_repository() -> None:
    assert isinstance(InMemoryRepositories(), TourRepository)
