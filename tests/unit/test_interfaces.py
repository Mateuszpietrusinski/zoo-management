"""Unit tests for repository port interfaces."""

import pytest

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


def test_zoo_repository_is_abstract() -> None:
    """ZooRepository is an abstract class."""
    with pytest.raises(TypeError):
        ZooRepository()  # type: ignore[abstract]


def test_enclosure_repository_is_abstract() -> None:
    """EnclosureRepository is an abstract class."""
    with pytest.raises(TypeError):
        EnclosureRepository()  # type: ignore[abstract]


def test_animal_repository_is_abstract() -> None:
    """AnimalRepository is an abstract class."""
    with pytest.raises(TypeError):
        AnimalRepository()  # type: ignore[abstract]


def test_employee_repository_is_abstract() -> None:
    """EmployeeRepository is an abstract class."""
    with pytest.raises(TypeError):
        EmployeeRepository()  # type: ignore[abstract]


def test_feeding_schedule_repository_is_abstract() -> None:
    """FeedingScheduleRepository is an abstract class."""
    with pytest.raises(TypeError):
        FeedingScheduleRepository()  # type: ignore[abstract]


def test_admission_record_repository_is_abstract() -> None:
    """AdmissionRecordRepository is an abstract class."""
    with pytest.raises(TypeError):
        AdmissionRecordRepository()  # type: ignore[abstract]


def test_health_check_record_repository_is_abstract() -> None:
    """HealthCheckRecordRepository is an abstract class."""
    with pytest.raises(TypeError):
        HealthCheckRecordRepository()  # type: ignore[abstract]


def test_tour_repository_is_abstract() -> None:
    """TourRepository is an abstract class."""
    with pytest.raises(TypeError):
        TourRepository()  # type: ignore[abstract]


def test_cannot_instantiate_any_repository_directly() -> None:
    """None of the repository ports can be instantiated."""
    repos = [
        ZooRepository,
        EnclosureRepository,
        AnimalRepository,
        EmployeeRepository,
        FeedingScheduleRepository,
        AdmissionRecordRepository,
        HealthCheckRecordRepository,
        TourRepository,
    ]
    for repo_cls in repos:
        with pytest.raises(TypeError):
            repo_cls()  # type: ignore[abstract]
