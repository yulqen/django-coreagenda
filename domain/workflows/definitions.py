from dataclasses import dataclass


@dataclass(frozen=True)
class Transition:
    from_step: str
    to_step: str
    command: str


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
