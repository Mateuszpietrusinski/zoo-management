"""FastAPI routers — thin layer: validate, call use case, map response."""

from datetime import datetime, time

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict

from zoo_management.adapters.in_memory import InMemoryRepositories
from zoo_management.domain.entities import Animal, Enclosure, HealthResult
from zoo_management.domain.exceptions import EntityNotFoundError
from zoo_management.infrastructure.dependencies import (
    get_admit_animal_use_case,
    get_assign_zookeeper_use_case,
    get_conduct_guided_tour_use_case,
    get_conduct_health_check_use_case,
    get_execute_feeding_round_use_case,
    get_repositories,
)
from zoo_management.usecases.admit_animal import (
    AdmitAnimalRequest,
    AdmitAnimalUseCase,
)
from zoo_management.usecases.assign_zookeeper import (
    AssignZookeeperRequest,
    AssignZookeeperUseCase,
)
from zoo_management.usecases.conduct_guided_tour import (
    ConductGuidedTourUseCase,
    GuidedTourRequest,
)
from zoo_management.usecases.conduct_health_check import (
    ConductHealthCheckUseCase,
    HealthCheckRequest,
)
from zoo_management.usecases.execute_feeding_round import (
    ExecuteFeedingRoundUseCase,
    FeedingRoundRequest,
)


class AssignZookeeperRequestSchema(BaseModel):
    """Request body for POST /enclosures/{enclosure_id}/zookeeper."""

    zookeeper_id: str
    zoo_id: str


class AssignZookeeperResponseSchema(BaseModel):
    """Response body for assign zookeeper."""

    enclosure_id: str
    zookeeper_id: str


class AdmitAnimalRequestSchema(BaseModel):
    """Request body for POST /animals/{animal_id}/admit."""

    zoo_id: str
    vet_id: str | None = None
    health_check_result: str | None = None
    health_check_notes: str | None = None


class AdmitAnimalResponseSchema(BaseModel):
    """Response body for admit animal."""

    animal_id: str
    enclosure_id: str
    admission_record_id: str


class AnimalResponseSchema(BaseModel):
    """Response for GET /animals/{id} (ADR-021 M-3)."""

    id: str
    name: str
    origin: str
    enclosure_id: str | None
    type_name: str
    taxonomic_type: str
    diet_type: str


class EnclosureResponseSchema(BaseModel):
    """Response for GET /enclosures/{id} (ADR-021 M-3)."""

    id: str
    name: str
    enclosure_type: str
    zoo_id: str
    assigned_zookeeper_id: str | None
    animal_count: int
    animal_ids: list[str]


class FeedingRoundRequestSchema(BaseModel):
    """Request body for POST /enclosures/{enclosure_id}/feeding-rounds."""

    zookeeper_id: str
    current_time: time

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "enclosure_id": "enc-mammal-1",
                "zookeeper_id": "emp-zk-1",
                "current_time": "09:00:00",
            }
        }
    )


class FeedingRoundResponseSchema(BaseModel):
    """Response body for execute feeding round."""

    enclosure_id: str
    fed_count: int
    note: str


class GuidedTourRequestSchema(BaseModel):
    """Request body for POST /tours."""

    guide_id: str
    zoo_id: str


class GuidedTourResponseSchema(BaseModel):
    """Response body for conduct guided tour (ADR-030: end_time in response)."""

    tour_id: str
    route: list[str]
    start_time: datetime
    end_time: datetime


class HealthCheckRequestSchema(BaseModel):
    """Request body for POST /animals/{animal_id}/health-checks."""

    vet_id: str
    result: str  # maps to HealthResult enum
    notes: str | None = None


class HealthCheckResponseSchema(BaseModel):
    """Response body for conduct health check."""

    health_check_record_id: str
    result: str


router = APIRouter()


@router.post(
    "/enclosures/{enclosure_id}/zookeeper",
    status_code=200,
    response_model=AssignZookeeperResponseSchema,
)
def assign_zookeeper(
    enclosure_id: str,
    body: AssignZookeeperRequestSchema,
    use_case: AssignZookeeperUseCase = Depends(get_assign_zookeeper_use_case),  # noqa: B008
) -> AssignZookeeperResponseSchema:
    """Assign a zookeeper to an enclosure.

    Args:
        enclosure_id: Enclosure identifier (path).
        body: Request body with zookeeper_id and zoo_id.
        use_case: Injected use case.

    Returns:
        AssignZookeeperResponseSchema with enclosure_id and zookeeper_id.
    """
    req = AssignZookeeperRequest(
        zoo_id=body.zoo_id,
        enclosure_id=enclosure_id,
        zookeeper_id=body.zookeeper_id,
    )
    result = use_case.execute(req)
    return AssignZookeeperResponseSchema(
        enclosure_id=result.enclosure_id,
        zookeeper_id=result.zookeeper_id,
    )


def _parse_health_result(value: str | None) -> HealthResult | None:
    if value is None:
        return None
    return HealthResult(value.lower())


@router.post(
    "/animals/{animal_id}/admit",
    status_code=201,
    response_model=AdmitAnimalResponseSchema,
)
def admit_animal(
    animal_id: str,
    body: AdmitAnimalRequestSchema,
    use_case: AdmitAnimalUseCase = Depends(get_admit_animal_use_case),  # noqa: B008
) -> AdmitAnimalResponseSchema:
    """Admit an animal to a suitable enclosure in the zoo.

    Args:
        animal_id: Animal identifier (path).
        body: Request body with zoo_id and optional vet/health for external animals.
        use_case: Injected use case.

    Returns:
        AdmitAnimalResponseSchema with animal_id, enclosure_id, admission_record_id.
    """
    req = AdmitAnimalRequest(
        animal_id=animal_id,
        zoo_id=body.zoo_id,
        vet_id=body.vet_id,
        health_check_result=_parse_health_result(body.health_check_result),
        health_check_notes=body.health_check_notes,
    )
    result = use_case.execute(req)
    return AdmitAnimalResponseSchema(
        animal_id=result.animal_id,
        enclosure_id=result.enclosure_id,
        admission_record_id=result.admission_record_id,
    )


@router.get(
    "/animals/{animal_id}",
    status_code=200,
    response_model=AnimalResponseSchema,
)
def get_animal(
    animal_id: str,
    repo: InMemoryRepositories = Depends(get_repositories),  # noqa: B008
) -> AnimalResponseSchema:
    """Get animal by id (ADR-021).

    Args:
        animal_id: Animal identifier (path).
        repo: Injected repository.

    Returns:
        AnimalResponseSchema with id, name, origin, enclosure_id, type_name,
        taxonomic_type, diet_type.
    """
    entity = repo.get_by_id(animal_id)
    if not isinstance(entity, Animal):
        raise EntityNotFoundError(f"Animal not found: {animal_id}")
    return AnimalResponseSchema(
        id=entity.id,
        name=entity.name,
        origin=entity.origin.value,
        enclosure_id=entity.enclosure_id,
        type_name=entity.type_name,
        taxonomic_type=entity.taxonomic_type,
        diet_type=entity.get_diet_type(),
    )


@router.post(
    "/animals/{animal_id}/health-checks",
    status_code=201,
    response_model=HealthCheckResponseSchema,
)
def conduct_health_check(
    animal_id: str,
    body: HealthCheckRequestSchema,
    use_case: ConductHealthCheckUseCase = Depends(get_conduct_health_check_use_case),  # noqa: B008
) -> HealthCheckResponseSchema:
    """Conduct a health check on an animal (veterinarian records result).

    Args:
        animal_id: Animal identifier (path).
        body: Request body with vet_id, result, optional notes.
        use_case: Injected use case.

    Returns:
        HealthCheckResponseSchema with health_check_record_id and result.
    """
    try:
        result_enum = HealthResult(body.result.lower())
    except ValueError as err:
        raise HTTPException(
            422,
            detail="Invalid result; use healthy, need_follow_up, or critical",
        ) from err
    req = HealthCheckRequest(
        animal_id=animal_id,
        vet_id=body.vet_id,
        result=result_enum,
        notes=body.notes,
    )
    response = use_case.execute(req)
    return HealthCheckResponseSchema(
        health_check_record_id=response.health_check_record_id,
        result=response.result.value,
    )


@router.post(
    "/enclosures/{enclosure_id}/feeding-rounds",
    status_code=200,
    response_model=FeedingRoundResponseSchema,
)
def execute_feeding_round(
    enclosure_id: str,
    body: FeedingRoundRequestSchema,
    use_case: ExecuteFeedingRoundUseCase = Depends(get_execute_feeding_round_use_case),  # noqa: B008
) -> FeedingRoundResponseSchema:
    """Execute a feeding round for the enclosure at the given time.

    Args:
        enclosure_id: Enclosure identifier (path).
        body: Request body with zookeeper_id and current_time.
        use_case: Injected use case.

    Returns:
        FeedingRoundResponseSchema with enclosure_id, fed_count, note.
    """
    req = FeedingRoundRequest(
        enclosure_id=enclosure_id,
        zookeeper_id=body.zookeeper_id,
        current_time=body.current_time,
    )
    result = use_case.execute(req)
    return FeedingRoundResponseSchema(
        enclosure_id=result.enclosure_id,
        fed_count=result.fed_count,
        note=result.note,
    )


@router.post(
    "/tours",
    status_code=201,
    response_model=GuidedTourResponseSchema,
)
def conduct_guided_tour(
    body: GuidedTourRequestSchema,
    use_case: ConductGuidedTourUseCase = Depends(get_conduct_guided_tour_use_case),  # noqa: B008
) -> GuidedTourResponseSchema:
    """Conduct a guided tour; guide becomes unavailable (ADR-003).

    Args:
        body: Request body with guide_id and zoo_id.
        use_case: Injected use case.

    Returns:
        GuidedTourResponseSchema with tour_id, route, start_time, end_time.
    """
    req = GuidedTourRequest(guide_id=body.guide_id, zoo_id=body.zoo_id)
    result = use_case.execute(req)
    return GuidedTourResponseSchema(
        tour_id=result.tour_id,
        route=result.route,
        start_time=result.start_time,
        end_time=result.end_time,
    )


@router.get(
    "/enclosures/{enclosure_id}",
    status_code=200,
    response_model=EnclosureResponseSchema,
)
def get_enclosure(
    enclosure_id: str,
    repo: InMemoryRepositories = Depends(get_repositories),  # noqa: B008
) -> EnclosureResponseSchema:
    """Get enclosure by id (ADR-021).

    Args:
        enclosure_id: Enclosure identifier (path).
        repo: Injected repository.

    Returns:
        EnclosureResponseSchema with id, name, enclosure_type, zoo_id,
        assigned_zookeeper_id, animal_count, animal_ids.
    """
    entity = repo.get_by_id(enclosure_id)
    if not isinstance(entity, Enclosure):
        raise EntityNotFoundError(f"Enclosure not found: {enclosure_id}")
    return EnclosureResponseSchema(
        id=entity.id,
        name=entity.name,
        enclosure_type=entity.enclosure_type.value,
        zoo_id=entity.zoo_id,
        assigned_zookeeper_id=entity.assigned_zookeeper_id,
        animal_count=entity.animal_count,
        animal_ids=[a.id for a in entity.animals],
    )
