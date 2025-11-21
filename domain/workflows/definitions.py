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
    name: str
    initial_step: str
    steps: list[str]
    transitions: list[Transition]


@dataclass
class WorkflowInstance:
    id: str
    name: str
