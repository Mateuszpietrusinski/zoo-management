"""Domain repository port interfaces (architecture.md C4.2)."""

import abc
from datetime import time

from zoo_management.domain.entities import (
    AdmissionRecord,
    Animal,
    Employee,
    Enclosure,
    FeedingSchedule,
    HealthCheckRecord,
    Tour,
    Zoo,
)


class ZooRepository(abc.ABC):
    """Port for Zoo access. No save (ADR-025)."""

    @abc.abstractmethod
    def get_by_id(self, id: str) -> Zoo:
        """Get zoo by id.

        Args:
            id: Zoo identifier.

        Returns:
            The zoo entity.

        Raises:
            EntityNotFoundError: When no zoo exists with the given id.
        """
        ...


class EnclosureRepository(abc.ABC):
    """Port for Enclosure persistence."""

    @abc.abstractmethod
    def get_by_id(self, id: str) -> Enclosure:
        """Get enclosure by id.

        Args:
            id: Enclosure identifier.

        Returns:
            The enclosure entity.

        Raises:
            EntityNotFoundError: When no enclosure exists with the given id.
        """
        ...

    @abc.abstractmethod
    def get_by_zoo(self, zoo_id: str) -> list[Enclosure]:
        """Get all enclosures for a zoo.

        Args:
            zoo_id: Zoo identifier.

        Returns:
            List of enclosures belonging to the zoo.
        """
        ...

    @abc.abstractmethod
    def save(self, enclosure: Enclosure) -> None:
        """Persist enclosure.

        Args:
            enclosure: Enclosure entity to save.
        """
        ...


class AnimalRepository(abc.ABC):
    """Port for Animal persistence."""

    @abc.abstractmethod
    def get_by_id(self, id: str) -> Animal:
        """Get animal by id.

        Args:
            id: Animal identifier.

        Returns:
            The animal entity.

        Raises:
            EntityNotFoundError: When no animal exists with the given id.
        """
        ...

    @abc.abstractmethod
    def save(self, animal: Animal) -> None:
        """Persist animal.

        Args:
            animal: Animal entity to save.
        """
        ...


class EmployeeRepository(abc.ABC):
    """Port for Employee persistence."""

    @abc.abstractmethod
    def get_by_id(self, id: str) -> Employee:
        """Get employee by id.

        Args:
            id: Employee identifier.

        Returns:
            The employee entity.

        Raises:
            EntityNotFoundError: When no employee exists with the given id.
        """
        ...

    @abc.abstractmethod
    def get_by_zoo_and_type(self, zoo_id: str, role: str) -> list[Employee]:
        """Get all employees of given role in a zoo.

        Args:
            zoo_id: Zoo identifier.
            role: Role name (e.g. 'Zookeeper', 'Veterinarian', 'Guide').

        Returns:
            List of employees of that role in the zoo.
        """
        ...

    @abc.abstractmethod
    def save(self, employee: Employee) -> None:
        """Persist employee.

        Args:
            employee: Employee entity to save.
        """
        ...


class FeedingScheduleRepository(abc.ABC):
    """Port for FeedingSchedule persistence."""

    @abc.abstractmethod
    def get_by_enclosure_and_time(
        self, enclosure_id: str, t: time
    ) -> FeedingSchedule | None:
        """Get schedule for enclosure at time.

        Args:
            enclosure_id: Enclosure identifier.
            t: Time of day.

        Returns:
            The feeding schedule or None if not found.
        """
        ...

    @abc.abstractmethod
    def save(self, schedule: FeedingSchedule) -> None:
        """Persist feeding schedule.

        Args:
            schedule: FeedingSchedule entity to save.
        """
        ...


class AdmissionRecordRepository(abc.ABC):
    """Port for AdmissionRecord persistence."""

    @abc.abstractmethod
    def save(self, record: AdmissionRecord) -> None:
        """Persist admission record.

        Args:
            record: AdmissionRecord entity to save.
        """
        ...


class HealthCheckRecordRepository(abc.ABC):
    """Port for HealthCheckRecord persistence."""

    @abc.abstractmethod
    def save(self, record: HealthCheckRecord) -> None:
        """Persist health check record.

        Args:
            record: HealthCheckRecord entity to save.
        """
        ...

    @abc.abstractmethod
    def get_health_record_by_id(self, id: str) -> HealthCheckRecord | None:  # noqa: A002
        """Get health check record by id.

        Args:
            id: Health check record identifier.

        Returns:
            The record or None if not found.
        """
        ...


class TourRepository(abc.ABC):
    """Port for Tour persistence."""

    @abc.abstractmethod
    def save(self, tour: Tour) -> None:
        """Persist tour.

        Args:
            tour: Tour entity to save.
        """
        ...
