"""Domain entities: enums, Animal/Employee hierarchies, Zoo, Enclosure, records."""

import abc
import enum
from datetime import date, datetime, time
from typing import Optional



class Origin(enum.Enum):
    """Origin of an animal (internal transfer vs external)."""

    INTERNAL = "internal"
    EXTERNAL = "external"


class EnclosureType(enum.Enum):
    """Type of enclosure; values match Animal.taxonomic_type (ADR-020)."""

    MAMMAL = "Mammal"
    BIRD = "Bird"
    REPTILE = "Reptile"


class HealthResult(enum.Enum):
    """Result of a health check."""

    HEALTHY = "healthy"
    NEED_FOLLOW_UP = "need_follow_up"
    CRITICAL = "critical"


# ---------------------------------------------------------------------------
# Animal hierarchy (ABC → Mammal/Bird/Reptile → concrete)
# ---------------------------------------------------------------------------


class Animal(abc.ABC):
    """Abstract base for all animals. Do not instantiate directly."""

    def __init__(
        self,
        id: str,
        name: str,
        origin: Origin,
        enclosure_id: Optional[str] = None,
    ) -> None:
        """Initialize an animal.

        Args:
            id: Unique identifier.
            name: Display name.
            origin: INTERNAL or EXTERNAL.
            enclosure_id: Optional enclosure assignment (None if not yet placed).
        """
        self.id = id
        self.name = name
        self.origin = origin
        self.enclosure_id = enclosure_id

    @property
    def type_name(self) -> str:
        """Concrete class name (e.g. 'Lion', 'Penguin')."""
        return type(self).__name__

    @property
    def taxonomic_type(self) -> str:
        """Mid-tier ABC name: 'Mammal', 'Bird', or 'Reptile'.
        Assumes exactly three inheritance levels: Animal → Mammal/Bird/Reptile → concrete.
        Do not subclass the concrete classes — MRO index [1] will silently return the wrong tier.
        """
        return type(self).__mro__[1].__name__

    @property
    def is_placed(self) -> bool:
        """True if the animal has been assigned to an enclosure."""
        return self.enclosure_id is not None

    @abc.abstractmethod
    def get_diet_type(self) -> str:
        """Return diet type: 'carnivore', 'herbivore', 'omnivore', or 'piscivore'."""
        ...

    def __repr__(self) -> str:
        return f"{type(self).__name__}(id={self.id!r}, name={self.name!r})"

    def __str__(self) -> str:
        return self.name

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Animal):
            return NotImplemented
        return self.id == other.id


class Mammal(Animal):
    """Abstract base for mammal species."""

    @abc.abstractmethod
    def get_diet_type(self) -> str:
        """Return diet type (implemented by concrete species).

        Returns:
            'carnivore', 'herbivore', or 'omnivore'.
        """
        ...


class Bird(Animal):
    """Abstract base for bird species."""

    @abc.abstractmethod
    def get_diet_type(self) -> str:
        """Return diet type (implemented by concrete species).

        Returns:
            'carnivore' or 'piscivore'.
        """
        ...


class Reptile(Animal):
    """Abstract base for reptile species."""

    @abc.abstractmethod
    def get_diet_type(self) -> str:
        """Return diet type (implemented by concrete species).

        Returns:
            'carnivore'.
        """
        ...


class Lion(Mammal):
    """Concrete mammal: lion (carnivore)."""

    def get_diet_type(self) -> str:
        """Return diet type.

        Returns:
            'carnivore'.
        """
        return "carnivore"


class Elephant(Mammal):
    """Concrete mammal: elephant (herbivore)."""

    def get_diet_type(self) -> str:
        """Return diet type.

        Returns:
            'herbivore'.
        """
        return "herbivore"


class Monkey(Mammal):
    """Concrete mammal: monkey (omnivore)."""

    def get_diet_type(self) -> str:
        """Return diet type.

        Returns:
            'omnivore'.
        """
        return "omnivore"


class Eagle(Bird):
    """Concrete bird: eagle (carnivore)."""

    def get_diet_type(self) -> str:
        """Return diet type.

        Returns:
            'carnivore'.
        """
        return "carnivore"


class Penguin(Bird):
    """Concrete bird: penguin (piscivore)."""

    def get_diet_type(self) -> str:
        """Return diet type.

        Returns:
            'piscivore'.
        """
        return "piscivore"


class Crocodile(Reptile):
    """Concrete reptile: crocodile (carnivore)."""

    def get_diet_type(self) -> str:
        """Return diet type.

        Returns:
            'carnivore'.
        """
        return "carnivore"


# ---------------------------------------------------------------------------
# Employee hierarchy (ABC → concrete)
# ---------------------------------------------------------------------------


class Employee(abc.ABC):
    """Abstract base for zoo employees. Do not instantiate directly."""

    def __init__(self, id: str, name: str, zoo_id: str) -> None:
        """Initialize an employee.

        Args:
            id: Unique identifier.
            name: Display name.
            zoo_id: ID of the zoo this employee belongs to.
        """
        self.id = id
        self.name = name
        self.zoo_id = zoo_id

    @property
    @abc.abstractmethod
    def role(self) -> str:
        """Concrete class name (e.g. 'Zookeeper', 'Veterinarian', 'Guide')."""
        ...

    def __repr__(self) -> str:
        return f"{type(self).__name__}(id={self.id!r}, name={self.name!r})"

    def __str__(self) -> str:
        return self.name

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Employee):
            return NotImplemented
        return self.id == other.id


class Zookeeper(Employee):
    """Zookeeper assigned to enclosures."""

    @property
    def role(self) -> str:
        return "Zookeeper"


class Veterinarian(Employee):
    """Veterinarian conducting health checks."""

    @property
    def role(self) -> str:
        return "Veterinarian"


class Guide(Employee):
    """Guide for guided tours. Has availability flag (ADR-003)."""

    @property
    def role(self) -> str:
        return "Guide"

    def __init__(
        self,
        id: str,
        name: str,
        zoo_id: str,
        is_available: bool = True,
    ) -> None:
        """Initialize a guide.

        Args:
            id: Unique identifier.
            name: Display name.
            zoo_id: ID of the zoo this guide belongs to.
            is_available: Whether the guide is available for tours (default True).
        """
        super().__init__(id, name, zoo_id)
        self.is_available = is_available


# ---------------------------------------------------------------------------
# Zoo, Enclosure, FeedingSchedule
# ---------------------------------------------------------------------------


class Zoo:
    """Zoo aggregate: name and tour route (list of enclosure ids)."""

    def __init__(self, id: str, name: str, tour_route: list[str]) -> None:
        """Initialize a zoo.

        Args:
            id: Unique identifier.
            name: Display name.
            tour_route: Ordered list of enclosure IDs for guided tours.
        """
        self.id = id
        self.name = name
        self.tour_route = tour_route

    def __repr__(self) -> str:
        return f"Zoo(id={self.id!r}, name={self.name!r})"

    def __str__(self) -> str:
        return self.name

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Zoo):
            return NotImplemented
        return self.id == other.id


class Enclosure:
    """Enclosure: type, zoo, optional zookeeper, list of animals (ADR-001)."""

    def __init__(
        self,
        id: str,
        name: str,
        enclosure_type: EnclosureType,
        zoo_id: str,
        assigned_zookeeper_id: Optional[str] = None,
        animals: Optional[list[Animal]] = None,
    ) -> None:
        """Initialize an enclosure.

        Args:
            id: Unique identifier.
            name: Display name.
            enclosure_type: MAMMAL, BIRD, or REPTILE.
            zoo_id: ID of the zoo this enclosure belongs to.
            assigned_zookeeper_id: Optional zookeeper ID for daily care.
            animals: Optional list of animals (default empty).
        """
        self.id = id
        self.name = name
        self.enclosure_type = enclosure_type
        self.zoo_id = zoo_id
        self.assigned_zookeeper_id = assigned_zookeeper_id
        self.animals = animals if animals is not None else []

    @property
    def is_occupied(self) -> bool:
        """True if at least one animal is in the enclosure."""
        return len(self.animals) > 0

    @property
    def animal_count(self) -> int:
        """Number of animals in the enclosure."""
        return len(self.animals)

    def __repr__(self) -> str:
        return f"Enclosure(id={self.id!r}, name={self.name!r})"

    def __str__(self) -> str:
        return self.name

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Enclosure):
            return NotImplemented
        return self.id == other.id


class FeedingSchedule:
    """Feeding schedule for an enclosure at a given time."""

    def __init__(
        self,
        id: str,
        enclosure_id: str,
        scheduled_time: time,
        diet: str,
    ) -> None:
        """Initialize a feeding schedule.

        Args:
            id: Unique identifier.
            enclosure_id: Enclosure this schedule applies to.
            scheduled_time: Time of day for feeding.
            diet: Diet description (e.g. 'meat', 'fish').
        """
        self.id = id
        self.enclosure_id = enclosure_id
        self.scheduled_time = scheduled_time
        self.diet = diet

    @property
    def schedule_info(self) -> str:
        """Formatted summary of the schedule."""
        return f"Enclosure {self.enclosure_id} at {self.scheduled_time!s}: {self.diet}"

    def __repr__(self) -> str:
        return f"FeedingSchedule(id={self.id!r}, enclosure_id={self.enclosure_id!r})"

    def __str__(self) -> str:
        return self.schedule_info


# ---------------------------------------------------------------------------
# Record entities
# ---------------------------------------------------------------------------


class AdmissionRecord:
    """Record of an animal admission to the zoo."""

    def __init__(
        self,
        id: str,
        date: date,
        animal_id: str,
        enclosure_id: str,
        zookeeper_id: Optional[str],
        vet_id: Optional[str],
        health_check_record_id: Optional[str],
    ) -> None:
        """Initialize an admission record.

        Args:
            id: Unique identifier.
            date: Date of admission.
            animal_id: Admitted animal ID.
            enclosure_id: Enclosure the animal was placed in.
            zookeeper_id: Optional assigned zookeeper ID.
            vet_id: Optional vet ID (for external-origin clearance).
            health_check_record_id: Optional health check record ID.
        """
        self.id = id
        self.date = date
        self.animal_id = animal_id
        self.enclosure_id = enclosure_id
        self.zookeeper_id = zookeeper_id
        self.vet_id = vet_id
        self.health_check_record_id = health_check_record_id

    def __repr__(self) -> str:
        return f"AdmissionRecord(id={self.id!r}, animal_id={self.animal_id!r})"

    def __str__(self) -> str:
        return f"AdmissionRecord {self.id} (animal={self.animal_id})"


class HealthCheckRecord:
    """Record of a health check performed by a vet."""

    def __init__(
        self,
        id: str,
        date: date,
        animal_id: str,
        vet_id: str,
        result: HealthResult,
        notes: Optional[str],
    ) -> None:
        """Initialize a health check record.

        Args:
            id: Unique identifier.
            date: Date of the check.
            animal_id: Animal that was checked.
            vet_id: Veterinarian who performed the check.
            result: HEALTHY, NEED_FOLLOW_UP, or CRITICAL.
            notes: Optional notes.
        """
        self.id = id
        self.date = date
        self.animal_id = animal_id
        self.vet_id = vet_id
        self.result = result
        self.notes = notes

    def __repr__(self) -> str:
        return f"HealthCheckRecord(id={self.id!r}, animal_id={self.animal_id!r})"

    def __str__(self) -> str:
        return f"HealthCheckRecord {self.id} (animal={self.animal_id})"


class Tour:
    """A guided tour with route and times."""

    def __init__(
        self,
        id: str,
        guide_id: str,
        route: list[str],
        start_time: datetime,
        end_time: datetime,
    ) -> None:
        """Initialize a tour.

        Args:
            id: Unique identifier.
            guide_id: Guide leading the tour.
            route: Ordered list of enclosure IDs.
            start_time: Tour start time.
            end_time: Tour end time.
        """
        self.id = id
        self.guide_id = guide_id
        self.route = route
        self.start_time = start_time
        self.end_time = end_time

    @property
    def is_completed(self) -> bool:
        """True when the tour has an end time set."""
        return self.end_time is not None

    def __repr__(self) -> str:
        return f"Tour(id={self.id!r}, guide_id={self.guide_id!r})"

    def __str__(self) -> str:
        return f"Tour {self.id} (guide={self.guide_id})"
