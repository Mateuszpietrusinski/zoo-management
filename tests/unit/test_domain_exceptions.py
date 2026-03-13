"""Unit tests for domain exceptions."""


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


def test_entity_not_found_error_is_exception() -> None:
    """EntityNotFoundError is a subclass of Exception."""
    assert issubclass(EntityNotFoundError, Exception)


def test_entity_not_found_error_carries_message() -> None:
    """EntityNotFoundError carries the provided message."""
    err = EntityNotFoundError("Animal x not found")
    assert str(err) == "Animal x not found"


def test_all_domain_exceptions_are_subclasses_of_exception() -> None:
    """All domain exception classes are subclasses of Exception."""
    domain_exceptions = [
        EntityNotFoundError,
        NoSuitableEnclosureError,
        HealthCheckNotClearedError,
        ZookeeperNotAssignedError,
        FeedingNotDueError,
        EnclosureNotInZooError,
        NoGuideAvailableError,
        InvalidEmployeeRoleError,
        InvalidRequestError,
        AnimalAlreadyPlacedError,
        GuideNotInZooError,
    ]
    for exc_cls in domain_exceptions:
        assert issubclass(exc_cls, Exception), f"{exc_cls.__name__} is not a subclass of Exception"
