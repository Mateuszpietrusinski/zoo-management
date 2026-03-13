"""Conduct health check use case (Process 4, architecture C4.4)."""

import logging
import uuid
from dataclasses import dataclass
from datetime import date

from zoo_management.domain.entities import (
    Animal,
    HealthCheckRecord,
    HealthResult,
    Veterinarian,
)
from zoo_management.domain.exceptions import (
    EntityNotFoundError,
    InvalidEmployeeRoleError,
)
from zoo_management.domain.interfaces import (
    AnimalRepository,
    EmployeeRepository,
    HealthCheckRecordRepository,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class HealthCheckRequest:
    """Request DTO for conducting a health check."""

    animal_id: str
    vet_id: str
    result: HealthResult
    notes: str | None = None


@dataclass(frozen=True)
class HealthCheckResponse:
    """Response DTO for conduct health check."""

    health_check_record_id: str
    result: HealthResult


class ConductHealthCheckUseCase:
    """Use case: veterinarian conducts a health check and the result is recorded."""

    def __init__(
        self,
        animal_repo: AnimalRepository,
        employee_repo: EmployeeRepository,
        health_repo: HealthCheckRecordRepository,
    ) -> None:
        """Initialize use case with repository dependencies.

        Args:
            animal_repo: Animal persistence port.
            employee_repo: Employee persistence port.
            health_repo: Health check record persistence port.
        """
        self._animal_repo = animal_repo
        self._employee_repo = employee_repo
        self._health_repo = health_repo

    def execute(self, req: HealthCheckRequest) -> HealthCheckResponse:
        """Conduct health check: validate animal and vet, create record, return response."""
        raw_animal = self._animal_repo.get_by_id(req.animal_id)
        if not isinstance(raw_animal, Animal):
            raise EntityNotFoundError(f"Animal not found: {req.animal_id}")

        raw_employee = self._employee_repo.get_by_id(req.vet_id)
        if not isinstance(raw_employee, Veterinarian):
            raise InvalidEmployeeRoleError(
                f"Employee {req.vet_id} is not a veterinarian"
            )

        record = HealthCheckRecord(
            id=f"health-{uuid.uuid4().hex[:12]}",
            date=date.today(),
            animal_id=req.animal_id,
            vet_id=req.vet_id,
            result=req.result,
            notes=req.notes,
        )
        self._health_repo.save(record)

        logger.info(
            "Health check conducted",
            extra={
                "animal_id": req.animal_id,
                "vet_id": req.vet_id,
                "result": req.result.value,
            },
        )
        return HealthCheckResponse(
            health_check_record_id=record.id,
            result=record.result,
        )
