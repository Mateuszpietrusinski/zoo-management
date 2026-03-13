"""In-memory repository adapter implementing all 8 port interfaces (ADR-025)."""

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
from zoo_management.domain.exceptions import EntityNotFoundError
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

# Type alias for save() argument (all entities that have save on their port)
_SavableEntity = (
    Enclosure
    | Animal
    | Employee
    | FeedingSchedule
    | AdmissionRecord
    | HealthCheckRecord
    | Tour
)


class InMemoryRepositories(
    ZooRepository,
    EnclosureRepository,
    AnimalRepository,
    EmployeeRepository,
    FeedingScheduleRepository,
    AdmissionRecordRepository,
    HealthCheckRecordRepository,
    TourRepository,
):
    """Single adapter implementing all 8 repository ports with dict storage."""

    def __init__(self) -> None:
        """Initialize empty in-memory stores for all entity types."""
        self._zoos: dict[str, Zoo] = {}
        self._enclosures: dict[str, Enclosure] = {}
        self._animals: dict[str, Animal] = {}
        self._employees: dict[str, Employee] = {}
        self._schedules: dict[tuple[str, time], FeedingSchedule] = {}
        self._admission_records: dict[str, AdmissionRecord] = {}
        self._health_records: dict[str, HealthCheckRecord] = {}
        self._tours: dict[str, Tour] = {}

    # Non-port method (ADR-025) — only called by seed_data()
    def seed_zoo(self, zoo: Zoo) -> None:
        """Store a zoo (no save on ZooRepository port). Only for bootstrap.

        Args:
            zoo: Zoo entity to store.
        """
        self._zoos[zoo.id] = zoo

    # get_by_id: search zoos, enclosures, animals, employees (first match)
    def get_by_id(  # type: ignore[override]
        self,
        id: str,  # noqa: A002 — matches port interface parameter name
    ) -> Zoo | Enclosure | Animal | Employee:
        """Get entity by id (zoo, enclosure, animal, or employee).

        Args:
            id: Entity identifier.

        Returns:
            The first matching entity (zoo, enclosure, animal, or employee).

        Raises:
            EntityNotFoundError: When no entity exists with the given id.
        """
        if id in self._zoos:
            return self._zoos[id]
        if id in self._enclosures:
            return self._enclosures[id]
        if id in self._animals:
            return self._animals[id]
        if id in self._employees:
            return self._employees[id]
        raise EntityNotFoundError(f"Entity not found: {id}")

    # EnclosureRepository
    def get_by_zoo(self, zoo_id: str) -> list[Enclosure]:
        """Get all enclosures for a zoo.

        Args:
            zoo_id: Zoo identifier.

        Returns:
            List of enclosures belonging to the zoo.
        """
        return [e for e in self._enclosures.values() if e.zoo_id == zoo_id]

    # EmployeeRepository
    def get_by_zoo_and_type(self, zoo_id: str, role: str) -> list[Employee]:
        """Get all employees of given role in a zoo.

        Args:
            zoo_id: Zoo identifier.
            role: Role name (e.g. 'Zookeeper', 'Veterinarian', 'Guide').

        Returns:
            List of employees of that role in the zoo.
        """
        return [
            e
            for e in self._employees.values()
            if e.zoo_id == zoo_id and e.role == role
        ]

    def save(
        self,
        entity: _SavableEntity,
    ) -> None:
        """Persist an entity (enclosure, animal, employee, schedule, or record).

        Args:
            entity: Entity to save (Enclosure, Animal, Employee, FeedingSchedule,
                AdmissionRecord, HealthCheckRecord, or Tour).

        Raises:
            TypeError: When entity type is not supported.
        """
        if isinstance(entity, Enclosure):
            self._enclosures[entity.id] = entity
        elif isinstance(entity, Animal):
            self._animals[entity.id] = entity
        elif isinstance(entity, Employee):
            self._employees[entity.id] = entity
        elif isinstance(entity, FeedingSchedule):
            key = (entity.enclosure_id, entity.scheduled_time)
            self._schedules[key] = entity
        elif isinstance(entity, AdmissionRecord):
            self._admission_records[entity.id] = entity
        elif isinstance(entity, HealthCheckRecord):
            self._health_records[entity.id] = entity
        elif isinstance(entity, Tour):
            self._tours[entity.id] = entity
        else:
            raise TypeError(f"Unsupported entity type: {type(entity)}")

    # HealthCheckRecordRepository
    def get_health_record_by_id(self, id: str) -> HealthCheckRecord | None:  # noqa: A002
        """Get health check record by id.

        Args:
            id: Health check record identifier.

        Returns:
            The record or None if not found.
        """
        return self._health_records.get(id)

    # FeedingScheduleRepository
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
        key = (enclosure_id, t)
        return self._schedules.get(key)
