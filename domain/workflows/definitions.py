from dataclasses import dataclass
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


@dataclass(frozen=True)
class Actor:
    name: str


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

    pass
