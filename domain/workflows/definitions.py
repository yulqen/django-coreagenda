import copy
import uuid
from abc import ABC
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable

from .errors import (DomainException, NoAvailableCheckpoint,
                     WorkflowDefinitionValidationError)


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

    def commands(self) -> list[str]:
        """
        Returns a list of all commands from the transitions.

        Returns:
            list[str]: A list of command strings.
        """
        return [t.command for t in self.transitions]

    def commands_pretty(self) -> str:
        """
        Generates a pretty string representation of all commands and their transitions.

        Returns:
            str: A multi-line string where each line represents a command and
            its associated from- and to-steps, formatted as "command:
            from_step -> to_step".
        """
        command_strs = []
        for t in self.transitions:
            command_strs.append(f"{t.command}: {t.from_step} -> {t.to_step}")
        return "\n".join(command_strs)

    def find_transition(self, step: str, command: str) -> Transition | None:
        """
        Finds a transition from a given step for a specific command.

        Args:
            step: The current step.
            command: The command to apply.

        Returns:
            The matching Transition object, or None if no such transition exists.

        """
        for t in self.transitions:
            if t.from_step == step and t.command == command:
                return t
        return None

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


@dataclass(frozen=True)
class BaseEvent(ABC):
    """Abstract base class for all workflow history events."""

    timestamp: datetime = field(default_factory=datetime.utcnow, init=False)


@dataclass(frozen=True)
class CommandApplied(BaseEvent):
    """Records that a command was successfully applied, causing a state transition."""

    from_step: str
    to_step: str
    command: str
    actor: Actor
    payload: dict


@dataclass(frozen=True)
class CheckpointSaved(BaseEvent):
    """Records that a snapshot of the workflow state was saved."""

    checkpoint: Checkpoint
    actor: Actor


@dataclass(frozen=True)
class StateRestored(BaseEvent):
    """Records that the workflow state was restored from a checkpoint."""

    checkpoint_id: str
    actor: Actor
    direction: str  # "rollback" or "rollforward"


@dataclass
class WorkflowInstance:
    """
    A single execution of the workflow for a specific subject .e.g an AgendaItem.
    Holds the live state:
    - which step currently on
    - what data has been collected so far
    - a history of what has happened (as a list of event objects)
    - any checkpoints saved

    Lives in memory in pure Python code. Allows for testing domain logic without
    Django or a database.
    """

    # TODO: the id should be UUID and generated on creation
    id: str
    name: str
    definition: WorkflowDefinition
    current_step: str
    data: dict
    history: list[BaseEvent]
    checkpoints: list[Checkpoint]
    active_checkpoint_id: str | None = None

    def apply_command(self, command: str, payload: dict, actor: Actor) -> None:
        """
        Applies a command to the workflow instance, potentially changing its state
        and current step.

        Args:
            command: The name of the command to apply (e.g., "approve", "reject").
            payload: A dictionary of data to be updated in the workflow instance's data.
            actor: The actor (user or system) initiating the command.

        Raises:
            DomainException: If the command is invalid for the current step of
            the workflow.
        """
        transition = self.definition.find_transition(self.current_step, command)
        if transition is None:
            raise DomainException(
                f"Invalid command '{command}' for step '{self.current_step}'"
            )
        # TODO implement guard

        from_step = self.current_step
        self.data.update(payload)
        self.current_step = transition.to_step

        self.history.append(
            CommandApplied(
                from_step=from_step,
                to_step=transition.to_step,
                command=command,
                actor=actor,
                payload=payload,
            )
        )

        # Any command moves the instance to a "live" state, not matching any checkpoint.
        self.active_checkpoint_id = None

    def save_checkpoint(self, label: str, actor: Actor) -> Checkpoint:
        """
        Saves a snapshot of the workflow's current state (step and data).

        Args:
            label: A user-friendly name for this checkpoint.
            actor: The actor saving the checkpoint.

        Returns:
            The created Checkpoint object.
        """
        cp = Checkpoint(
            id=str(uuid.uuid4()),
            label=label,
            step=self.current_step,
            data=copy.deepcopy(self.data),
            created_at=datetime.utcnow(),
        )
        self.checkpoints.append(cp)
        self.active_checkpoint_id = cp.id

        # Record the creation of the checkpoint in the history log.
        self.history.append(CheckpointSaved(checkpoint=cp, actor=actor))
        return cp

    def _get_sorted_checkpoints(self) -> list[Checkpoint]:
        """Returns checkpoints sorted by creation time."""
        return sorted(self.checkpoints, key=lambda cp: cp.created_at)

    def rollback(self, actor: Actor) -> None:
        """
        Rolls back the workflow's state to the previous checkpoint in its history.

        Args:
            actor: The actor (user or system) initiating the rollback.

        Raises:
            NoAvailableCheckpoint: If no checkpoints exist or if the workflow is
                already at the earliest available checkpoint.
            DomainException: If the `active_checkpoint_id` points to a checkpoint
                that cannot be found in the instance's `checkpoints` list, indicating
                an internal consistency error.
        """
        sorted_cps = self._get_sorted_checkpoints()
        if not sorted_cps:
            raise NoAvailableCheckpoint("Cannot rollback: no checkpoints exist.")

        if self.active_checkpoint_id:
            try:
                # Find the index of the currently active checkpoint
                current_index = [cp.id for cp in sorted_cps].index(
                    self.active_checkpoint_id
                )
            except ValueError:
                raise DomainException(
                    f"Active checkpoint ID '{self.active_checkpoint_id}' not found."
                )
        else:
            # If state is live, it's conceptually after the last checkpoint.
            # So, rolling back goes to the last one.
            current_index = len(sorted_cps)

        if current_index == 0:
            raise NoAvailableCheckpoint(
                "Cannot rollback: already at the earliest checkpoint."
            )

        target_checkpoint = sorted_cps[current_index - 1]

        # Restore state from the target checkpoint
        self.current_step = target_checkpoint.step
        self.data = copy.deepcopy(target_checkpoint.data)
        self.active_checkpoint_id = target_checkpoint.id

        self.history.append(
            StateRestored(
                checkpoint_id=target_checkpoint.id, actor=actor, direction="rollback"
            )
        )

    def rollforward(self, actor: Actor) -> None:
        """
        Rolls forward the workflow's state to the next checkpoint in its history.
        This operation is only possible if a rollback has occurred, meaning the
        `active_checkpoint_id` points to a checkpoint that is not the latest one.

        Args:
            actor: The actor (user or system) initiating the rollforward.

        Raises:
            NoAvailableCheckpoint: If the current state is "live" (not at any
                saved checkpoint), if no checkpoints exist, or if the workflow
                is already at the latest available checkpoint.
            DomainException: If the `active_checkpoint_id` points to a checkpoint
                that cannot be found in the instance's `checkpoints` list, indicating
                an internal consistency error.
        """
        if self.active_checkpoint_id is None:
            raise NoAvailableCheckpoint(
                "Cannot rollforward: current state is live, not at a checkpoint."
            )

        sorted_cps = self._get_sorted_checkpoints()
        if not sorted_cps:
            raise NoAvailableCheckpoint("Cannot rollforward: no checkpoints exist.")

        try:
            current_index = [cp.id for cp in sorted_cps].index(
                self.active_checkpoint_id
            )
        except ValueError:
            raise DomainException(
                f"Active checkpoint ID '{self.active_checkpoint_id}' not found."
            )

        if current_index >= len(sorted_cps) - 1:
            raise NoAvailableCheckpoint(
                "Cannot rollforward: already at the latest checkpoint."
            )

        target_checkpoint = sorted_cps[current_index + 1]

        # Restore state from the target checkpoint
        self.current_step = target_checkpoint.step
        self.data = copy.deepcopy(target_checkpoint.data)
        self.active_checkpoint_id = target_checkpoint.id

        self.history.append(
            StateRestored(
                checkpoint_id=target_checkpoint.id,
                actor=actor,
                direction="rollforward",
            )
        )
