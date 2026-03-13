"""Execute feeding round use case (Process 3, architecture C4.4, ADR-019/024/028/029)."""

import logging
from dataclasses import dataclass
from datetime import time

from zoo_management.domain.entities import Enclosure, Zookeeper
from zoo_management.domain.exceptions import (
    EntityNotFoundError,
    FeedingNotDueError,
    InvalidEmployeeRoleError,
    ZookeeperNotAssignedError,
)
from zoo_management.domain.interfaces import (
    EmployeeRepository,
    EnclosureRepository,
    FeedingScheduleRepository,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FeedingRoundRequest:
    """Request DTO for executing a feeding round."""

    enclosure_id: str
    zookeeper_id: str
    current_time: time


@dataclass(frozen=True)
class FeedingRoundResponse:
    """Response DTO for execute feeding round."""

    enclosure_id: str
    fed_count: int
    note: str


class ExecuteFeedingRoundUseCase:
    """Use case: execute feeding round (schedule match, zookeeper check, polymorphic diet)."""

    def __init__(
        self,
        enclosure_repo: EnclosureRepository,
        employee_repo: EmployeeRepository,
        schedule_repo: FeedingScheduleRepository,
    ) -> None:
        """Initialize use case with repository dependencies.

        Args:
            enclosure_repo: Enclosure persistence port.
            employee_repo: Employee persistence port.
            schedule_repo: Feeding schedule persistence port.
        """
        self._enclosure_repo = enclosure_repo
        self._employee_repo = employee_repo
        self._schedule_repo = schedule_repo

    def execute(self, req: FeedingRoundRequest) -> FeedingRoundResponse:
        """Execute feeding round; check order per ADR-024; use req.current_time (ADR-019)."""
        # 1. Schedule first — None → FeedingNotDueError (ADR-029)
        schedule = self._schedule_repo.get_by_enclosure_and_time(
            req.enclosure_id, req.current_time
        )
        if schedule is None:
            raise FeedingNotDueError(
                "No feeding schedule for this enclosure at the given time"
            )

        # 2. Enclosure — if missing, treat as FeedingNotDueError (ADR-029)
        try:
            enclosure = self._enclosure_repo.get_by_id(req.enclosure_id)
        except EntityNotFoundError:
            raise FeedingNotDueError(
                "No feeding schedule for this enclosure at the given time"
            ) from None
        if not isinstance(enclosure, Enclosure):
            raise FeedingNotDueError(
                "No feeding schedule for this enclosure at the given time"
            )

        # 3. Assignment check
        if enclosure.assigned_zookeeper_id != req.zookeeper_id:
            raise ZookeeperNotAssignedError(
                "Zookeeper is not assigned to this enclosure"
            )

        # 4. Employee and role
        raw_employee = self._employee_repo.get_by_id(req.zookeeper_id)
        if not isinstance(raw_employee, Zookeeper):
            raise InvalidEmployeeRoleError(
                f"Employee {raw_employee.id} is not a zookeeper"
            )

        # 5. Collect diet types in enclosure.animals order (polymorphic get_diet_type)
        diet_types = [animal.get_diet_type() for animal in enclosure.animals]
        fed_count = len(diet_types)

        # 6. Note format (ADR-028): always str, never None
        if fed_count == 0:
            note = "no animals to feed"
        else:
            note = f"Fed {fed_count} animals (diets: {', '.join(diet_types)})"

        logger.info(
            "Feeding round executed",
            extra={
                "enclosure_id": req.enclosure_id,
                "zookeeper_id": req.zookeeper_id,
                "fed_count": fed_count,
            },
        )
        return FeedingRoundResponse(
            enclosure_id=req.enclosure_id,
            fed_count=fed_count,
            note=note,
        )
