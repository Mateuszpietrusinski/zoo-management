"""Conduct guided tour use case (Process 5, architecture C4.4)."""

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime

from zoo_management.domain.entities import Enclosure, Guide, Tour, Zoo
from zoo_management.domain.exceptions import (
    EntityNotFoundError,
    GuideNotInZooError,
    InvalidEmployeeRoleError,
    NoGuideAvailableError,
)
from zoo_management.domain.interfaces import (
    EmployeeRepository,
    EnclosureRepository,
    TourRepository,
    ZooRepository,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GuidedTourRequest:
    """Request DTO for conducting a guided tour."""

    guide_id: str
    zoo_id: str


@dataclass(frozen=True)
class GuidedTourResponse:
    """Response DTO for conduct guided tour (ADR-030: end_time in response)."""

    tour_id: str
    route: list[str]
    start_time: datetime
    end_time: datetime


class ConductGuidedTourUseCase:
    """Use case: guide conducts a tour through zoo's tour route; guide becomes unavailable."""

    def __init__(
        self,
        zoo_repo: ZooRepository,
        enclosure_repo: EnclosureRepository,
        employee_repo: EmployeeRepository,
        tour_repo: TourRepository,
    ) -> None:
        """Initialize use case with repository dependencies.

        Args:
            zoo_repo: Zoo persistence port.
            enclosure_repo: Enclosure persistence port.
            employee_repo: Employee persistence port.
            tour_repo: Tour persistence port.
        """
        self._zoo_repo = zoo_repo
        self._enclosure_repo = enclosure_repo
        self._employee_repo = employee_repo
        self._tour_repo = tour_repo

    def execute(self, req: GuidedTourRequest) -> GuidedTourResponse:
        """Conduct tour: validate guide (role, zoo, availability), validate route, create tour."""
        # 1. employee_repo.get_by_id(guide_id) — raises EntityNotFoundError
        raw_employee = self._employee_repo.get_by_id(req.guide_id)
        if not isinstance(raw_employee, Guide):
            raise InvalidEmployeeRoleError(
                f"Employee {req.guide_id} is not a guide"
            )
        guide = raw_employee

        # 3. Validate guide.zoo_id == request.zoo_id — raises GuideNotInZooError (ADR-026)
        if guide.zoo_id != req.zoo_id:
            raise GuideNotInZooError(
                "Guide does not belong to the requested zoo"
            )

        # 4. Validate guide.is_available == True — raises NoGuideAvailableError (ADR-003)
        if not guide.is_available:
            raise NoGuideAvailableError("No available guide to start the tour")

        # 5. zoo_repo.get_by_id(zoo_id) — raises EntityNotFoundError
        zoo = self._zoo_repo.get_by_id(req.zoo_id)

        # 6. route = zoo.tour_route
        route = zoo.tour_route

        # 7. For each enclosure_id in route: enclosure_repo.get_by_id — raises EntityNotFoundError
        for enclosure_id in route:
            self._enclosure_repo.get_by_id(enclosure_id)

        # 8. now = datetime.now()
        now = datetime.now()

        # 9. Create Tour (ADR-011: start_time == end_time == now())
        tour = Tour(
            id=f"tour-{uuid.uuid4().hex[:12]}",
            guide_id=req.guide_id,
            route=route,
            start_time=now,
            end_time=now,
        )

        # 10. guide.is_available = False (ADR-003)
        guide.is_available = False

        # 11. employee_repo.save(guide)
        self._employee_repo.save(guide)

        # 12. tour_repo.save(tour)
        self._tour_repo.save(tour)

        # 13. Return GuidedTourResponse
        logger.info(
            "Guided tour conducted",
            extra={"tour_id": tour.id, "guide_id": guide.id, "zoo_id": req.zoo_id},
        )
        return GuidedTourResponse(
            tour_id=tour.id,
            route=tour.route,
            start_time=tour.start_time,
            end_time=tour.end_time,
        )
