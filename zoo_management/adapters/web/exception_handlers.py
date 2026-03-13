"""FastAPI exception handlers — map domain exceptions to HTTP responses."""

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from zoo_management.domain.exceptions import (
    AnimalAlreadyPlacedError,
    EnclosureNotInZooError,
    EntityNotFoundError,
    FeedingNotDueError,
    GuideNotInZooError,
    HealthCheckNotClearedError,
    InvalidEmployeeRoleError,
    InvalidRequestError,
    NoGuideAvailableError,
    NoSuitableEnclosureError,
    ZookeeperNotAssignedError,
)


def register_exception_handlers(app: FastAPI) -> None:
    """Register domain exception handlers on the FastAPI app.

    Maps domain exceptions to HTTP status (404 for EntityNotFoundError,
    422 for business rule violations). All responses use {"detail": "<message>"}.

    Args:
        app: FastAPI application instance to register handlers on.
    """

    @app.exception_handler(EntityNotFoundError)
    def entity_not_found(
        _request: object, exc: EntityNotFoundError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={"detail": str(exc)},
        )

    @app.exception_handler(EnclosureNotInZooError)
    def enclosure_not_in_zoo(
        _request: object, exc: EnclosureNotInZooError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={"detail": str(exc)},
        )

    @app.exception_handler(InvalidEmployeeRoleError)
    def invalid_employee_role(
        _request: object, exc: InvalidEmployeeRoleError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={"detail": str(exc)},
        )

    @app.exception_handler(NoSuitableEnclosureError)
    def no_suitable_enclosure(
        _request: object, exc: NoSuitableEnclosureError
    ) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.exception_handler(HealthCheckNotClearedError)
    def health_check_not_cleared(
        _request: object, exc: HealthCheckNotClearedError
    ) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.exception_handler(AnimalAlreadyPlacedError)
    def animal_already_placed(
        _request: object, exc: AnimalAlreadyPlacedError
    ) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.exception_handler(InvalidRequestError)
    def invalid_request(
        _request: object, exc: InvalidRequestError
    ) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.exception_handler(FeedingNotDueError)
    def feeding_not_due(
        _request: object, exc: FeedingNotDueError
    ) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.exception_handler(ZookeeperNotAssignedError)
    def zookeeper_not_assigned(
        _request: object, exc: ZookeeperNotAssignedError
    ) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.exception_handler(NoGuideAvailableError)
    def no_guide_available(
        _request: object, exc: NoGuideAvailableError
    ) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.exception_handler(GuideNotInZooError)
    def guide_not_in_zoo(
        _request: object, exc: GuideNotInZooError
    ) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc)})
