class PlannerError(Exception):
    """Base class for all planner errors; the message is shown to the user."""


class ValidationError(PlannerError):
    """User input is not acceptable."""


class StorageError(PlannerError):
    """Data files cannot be read or written."""
