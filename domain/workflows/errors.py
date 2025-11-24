class WorkflowDefinitionValidationError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message


class DomainException(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
