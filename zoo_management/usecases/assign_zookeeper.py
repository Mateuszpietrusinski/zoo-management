"""Assign zookeeper to enclosure use case (Process 1, architecture C4.3 + C4.4)."""

import logging
from dataclasses import dataclass

from zoo_management.domain.entities import Enclosure, Zookeeper
from zoo_management.domain.exceptions import (
    EnclosureNotInZooError,
    EntityNotFoundError,
    InvalidEmployeeRoleError,
)
from zoo_management.domain.interfaces import EmployeeRepository, EnclosureRepository

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AssignZookeeperRequest:
    """Request DTO for assigning a zookeeper to an enclosure."""

    zoo_id: str
    enclosure_id: str
    zookeeper_id: str


@dataclass(frozen=True)
class AssignZookeeperResponse:
    """Response DTO for assign zookeeper."""

    enclosure_id: str
    zookeeper_id: str


class AssignZookeeperUseCase:
    """Use case: assign a zookeeper to an enclosure (three-way zoo check, ADR-016)."""

    def __init__(
        self,
        enclosure_repo: EnclosureRepository,
        employee_repo: EmployeeRepository,
    ) -> None:
        """Initialize use case with repository dependencies.

        Args:
            enclosure_repo: Enclosure persistence port.
            employee_repo: Employee persistence port.
        """
        self._enclosure_repo = enclosure_repo
        self._employee_repo = employee_repo

    def execute(self, req: AssignZookeeperRequest) -> AssignZookeeperResponse:
        """Assign zookeeper to enclosure; idempotent if same zookeeper (ADR-031)."""
        raw_enclosure = self._enclosure_repo.get_by_id(req.enclosure_id)
        if not isinstance(raw_enclosure, Enclosure):
            raise EntityNotFoundError(f"Enclosure not found: {req.enclosure_id}")
        enclosure = raw_enclosure

        raw_employee = self._employee_repo.get_by_id(req.zookeeper_id)
        if not isinstance(raw_employee, Zookeeper):
            raise InvalidEmployeeRoleError(
                f"Employee {raw_employee.id} is not a zookeeper"
            )
        zookeeper = raw_employee

        if enclosure.zoo_id != req.zoo_id or zookeeper.zoo_id != req.zoo_id:
            raise EnclosureNotInZooError(
                "Enclosure or zookeeper does not belong to the requested zoo"
            )

        enclosure.assigned_zookeeper_id = zookeeper.id
        self._enclosure_repo.save(enclosure)

        logger.info(
            "Zookeeper assigned to enclosure",
            extra={"enclosure_id": enclosure.id, "zookeeper_id": zookeeper.id},
        )
        return AssignZookeeperResponse(
            enclosure_id=enclosure.id,
            zookeeper_id=zookeeper.id,
        )
