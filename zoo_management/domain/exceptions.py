"""Domain exceptions (architecture.md C3)."""


class EntityNotFoundError(Exception):
    """Entity not found in the store."""


class NoSuitableEnclosureError(Exception):
    """No enclosure type matches animal's taxonomic type."""


class HealthCheckNotClearedError(Exception):
    """Animal not cleared by vet (external origin)."""


class ZookeeperNotAssignedError(Exception):
    """Feeding attempted by unassigned zookeeper."""


class FeedingNotDueError(Exception):
    """Current time does not exactly match scheduled time."""


class EnclosureNotInZooError(Exception):
    """Enclosure or zookeeper does not belong to the same zoo."""


class NoGuideAvailableError(Exception):
    """No available guide to start the tour."""


class InvalidEmployeeRoleError(Exception):
    """Employee found but is the wrong subtype."""


class InvalidRequestError(Exception):
    """Required field absent for the given operation."""


class AnimalAlreadyPlacedError(Exception):
    """Attempt to admit an animal that already has an assigned enclosure."""


class GuideNotInZooError(Exception):
    """Guide does not belong to the requested zoo."""
