"""Admit animal to enclosure use case (Process 2, architecture C4.3 + C4.4)."""

import logging
import uuid
from dataclasses import dataclass
from datetime import date

from zoo_management.domain.entities import (
    AdmissionRecord,
    Animal,
    HealthCheckRecord,
    HealthResult,
    Veterinarian,
)
from zoo_management.domain.exceptions import (
    AnimalAlreadyPlacedError,
    EntityNotFoundError,
    HealthCheckNotClearedError,
    InvalidEmployeeRoleError,
    InvalidRequestError,
    NoSuitableEnclosureError,
)
from zoo_management.domain.interfaces import (
    AdmissionRecordRepository,
    AnimalRepository,
    EmployeeRepository,
    EnclosureRepository,
    HealthCheckRecordRepository,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AdmitAnimalRequest:
    """Request DTO for admitting an animal to a zoo enclosure."""

    animal_id: str
    zoo_id: str
    vet_id: str | None = None
    health_check_result: HealthResult | None = None
    health_check_notes: str | None = None


@dataclass(frozen=True)
class AdmitAnimalResponse:
    """Response DTO for admit animal."""

    animal_id: str
    enclosure_id: str
    admission_record_id: str


class AdmitAnimalUseCase:
    """Use case: admit an animal to a suitable enclosure (health check for external, ADR-002)."""

    def __init__(
        self,
        animal_repo: AnimalRepository,
        enclosure_repo: EnclosureRepository,
        employee_repo: EmployeeRepository,
        admission_repo: AdmissionRecordRepository,
        health_repo: HealthCheckRecordRepository,
    ) -> None:
        """Initialize use case with repository dependencies.

        Args:
            animal_repo: Animal persistence port.
            enclosure_repo: Enclosure persistence port.
            employee_repo: Employee persistence port.
            admission_repo: Admission record persistence port.
            health_repo: Health check record persistence port.
        """
        self._animal_repo = animal_repo
        self._enclosure_repo = enclosure_repo
        self._employee_repo = employee_repo
        self._admission_repo = admission_repo
        self._health_repo = health_repo

    def execute(self, req: AdmitAnimalRequest) -> AdmitAnimalResponse:
        """Admit animal to first matching enclosure; external needs health check (ADR-002)."""
        raw_animal = self._animal_repo.get_by_id(req.animal_id)
        if not isinstance(raw_animal, Animal):
            raise EntityNotFoundError(f"Animal not found: {req.animal_id}")
        animal = raw_animal

        if animal.is_placed:
            raise AnimalAlreadyPlacedError(
                f"Animal {animal.id} is already placed in enclosure {animal.enclosure_id}"
            )

        health_check_record_id: str | None = None
        vet_id_for_record: str | None = None

        if animal.origin.value == "external":
            if req.vet_id is None or req.health_check_result is None:
                raise InvalidRequestError(
                    "vet_id and health_check_result are required for external animals"
                )
            raw_employee = self._employee_repo.get_by_id(req.vet_id)
            if not isinstance(raw_employee, Veterinarian):
                raise InvalidEmployeeRoleError(
                    f"Employee {raw_employee.id} is not a veterinarian"
                )
            if req.health_check_result != HealthResult.HEALTHY:
                raise HealthCheckNotClearedError(
                    "External animal must be cleared healthy before admission"
                )
            health_record = HealthCheckRecord(
                id=f"health-{uuid.uuid4().hex[:12]}",
                date=date.today(),
                animal_id=animal.id,
                vet_id=req.vet_id,
                result=req.health_check_result,
                notes=req.health_check_notes,
            )
            self._health_repo.save(health_record)
            health_check_record_id = health_record.id
            vet_id_for_record = req.vet_id

        enclosures = self._enclosure_repo.get_by_zoo(req.zoo_id)
        matching = [
            e
            for e in enclosures
            if e.enclosure_type.value == animal.taxonomic_type
        ]
        if not matching:
            raise NoSuitableEnclosureError(
                f"No enclosure of type {animal.taxonomic_type} in zoo {req.zoo_id}"
            )
        enclosure = matching[0]

        animal.enclosure_id = enclosure.id
        enclosure.animals.append(animal)
        self._animal_repo.save(animal)
        self._enclosure_repo.save(enclosure)

        zookeeper_id = enclosure.assigned_zookeeper_id
        admission_record = AdmissionRecord(
            id=f"adm-{uuid.uuid4().hex[:12]}",
            date=date.today(),
            animal_id=animal.id,
            enclosure_id=enclosure.id,
            zookeeper_id=zookeeper_id,
            vet_id=vet_id_for_record,
            health_check_record_id=health_check_record_id,
        )
        self._admission_repo.save(admission_record)

        logger.info(
            "Animal admitted to enclosure",
            extra={
                "animal_id": animal.id,
                "enclosure_id": enclosure.id,
                "admission_record_id": admission_record.id,
            },
        )
        return AdmitAnimalResponse(
            animal_id=animal.id,
            enclosure_id=enclosure.id,
            admission_record_id=admission_record.id,
        )
