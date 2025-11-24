from dataclasses import dataclass
from datetime import datetime
from typing import Callable


@dataclass(frozen=True)
class Transition:
    from_step: str
    to_step: str
    command: str
    guard: Callable[["WorkflowInstance", dict, "Actor"], bool] | None = None
    # this is interesting! adding a function to a dataclass...
    # dict is the payload of data here - whatever that is
    # see https://docs.python.org/3/library/typing.html#annotating-callable-objects


@dataclass
class Checkpoint:
    """
    Allow save-and-resume + reversability.

    Any any point, the engine can save a snapshot of the current step + data (Checkpoint).
    Also, restore a previous Checkpoint (rollback_to).

    Enables:
    - save and resume later functionality
    - undo accidental step
    - "chair has rejected changes" - go back two steps.
    """

    id: str
    label: str
    step: str
    data: dict
    created_at: datetime


@dataclass(frozen=True)
class Actor:
    name: str


class WorkflowDefinitionValidationError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message


@dataclass(frozen=True)
class WorkflowDefinition:
    """
    A static blueprint for a process. Describes what commands move it forward and
    how the steps connect. Also, what guards or rules must be satisfied prior to the move.

    Contains no data - just structure.
    """

    name: str
    initial_step: str
    steps: set[str]
    transitions: list[Transition]

    def is_valid(self) -> bool | WorkflowDefinitionValidationError:
        """
        Validates that a definition is correct.

        Raises WorkflowDefinitionValidationError if the definition is invalid.

        This method should be called in a try... except block to handle potential
        validation errors.
        """
        if not self.transitions:
            raise WorkflowDefinitionValidationError(
                "A definition requires a list of Transition objects."
            )
        elif not self.steps:
            raise WorkflowDefinitionValidationError(
                "A definition requires a list of steps."
            )
        elif self.initial_step not in self.steps:
            raise WorkflowDefinitionValidationError(
                "The initial_step must existing in the list of steps."
            )
        else:
            return True


@dataclass
class WorkflowInstance:
    """
    A single execution of the workflow for a specific subject .e.g an AgendaItem.
    Holds the live state:
    - which step currently on
    - what data has been collected so far
    - a history of what has happened
    - any checkpoints saved

    Lives in memory in pure Python code. Allows for testing domain logic without
    Django or a database.
    """

    id: str
    name: str
    definition: WorkflowDefinition
    current_step: str
    data: dict
    history: list[dict]
    checkpoints: list[Checkpoint]
