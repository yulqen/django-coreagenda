class WorkflowDefinitionValidationError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message


class DomainException(Exception):
    def __init__(self, message: str) -> None:
        self.message = message


class NoAvailableCheckpoint(DomainException):
    """Raised when a rollback or rollforward action is not possible."""

    pass
