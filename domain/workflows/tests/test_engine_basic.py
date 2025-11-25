import dataclasses
import uuid
from datetime import datetime

import pytest
from domain.workflows.definitions import (Actor, Checkpoint, CheckpointSaved,
                                          CommandApplied, Transition,
                                          WorkflowDefinition, WorkflowInstance)
from domain.workflows.errors import (DomainException,
                                     WorkflowDefinitionValidationError)


TEST_FLOW = WorkflowDefinition(
    name="test definition",
    initial_step="initial request",
    steps={"initial_request", "triage", "completed"},
    # the first arg of each Transition (from_step) should match declared steps
    transitions=[
        Transition("initial_request", "triage", "start_triage"),
        Transition("triage", "completed", "complete"),
    ],
)


def test_checkpoint_exists() -> None:
    checkpoint = Checkpoint(
        id=str(uuid.uuid4()),
        label="test checkpoint",
        step="initial_request",
        data={},
        created_at=datetime.now(),
    )
    assert checkpoint


def test_workflow_definition() -> None:
    with pytest.raises(dataclasses.FrozenInstanceError):
        # we cannot mutate the flow object
        TEST_FLOW.name = "Cedric"  # type: ignore
    assert len(TEST_FLOW.steps) == 3
    assert len(TEST_FLOW.transitions) == 2


def test_workflow_definition_basic_validity() -> None:
    with pytest.raises(WorkflowDefinitionValidationError):
        WorkflowDefinition(
            name="bad definition",
            initial_step="initial_request",
            steps=set(),  # steps are mandatory
            transitions=[],  # transitions are mandatory
        ).is_valid()
    with pytest.raises(WorkflowDefinitionValidationError):
        WorkflowDefinition(
            name="bad definition",
            initial_step="initial_request",
            steps={"initial_request"},  # steps are mandatory
            transitions=[],  # transitions are mandatory
        ).is_valid()
    with pytest.raises(WorkflowDefinitionValidationError):
        WorkflowDefinition(
            name="bad definition",
            initial_step="initial_request",
            steps={"first request", "second request"},  # steps are mandatory
            transitions=[],  # transitions are mandatory
        ).is_valid()
    with pytest.raises(WorkflowDefinitionValidationError):
        WorkflowDefinition(
            name="bad definition",
            initial_step="",
            steps={"first_request", "second_request"},  # steps are mandatory
            transitions=[],  # transitions are mandatory
        ).is_valid()
    with pytest.raises(WorkflowDefinitionValidationError):
        WorkflowDefinition(
            name="bad definition",
            initial_step="",
            steps={"first_request", "second_request"},  # steps are mandatory
            transitions=[],  # transitions are mandatory
        ).is_valid()


def test_workflow_instance_exists() -> None:
    instance = WorkflowInstance(
        id=str(uuid.uuid4()),
        name="test instance",
        definition=TEST_FLOW,
        current_step="initial_request",
        data={},
        history=[],
        checkpoints=[],
    )
    assert instance.definition.name == "test definition"


def test_workflow_can_move_from_first_step_to_second() -> None:
    instance = WorkflowInstance(
        id=str(uuid.uuid4()),
        name="test instance",
        definition=TEST_FLOW,
        current_step="initial_request",
        data={"requester": "Colin Requester"},
        history=[],
        checkpoints=[],
    )
    instance.apply_command(
        "start_triage", {"notes": "Moved it on one step"}, actor=Actor("alice")
    )
    assert instance.current_step == "triage"
    assert "Moved it on one step" == instance.data["notes"]


def test_workflow_can_move_all_steps() -> None:
    instance = WorkflowInstance(
        id=str(uuid.uuid4()),
        name="test instance",
        definition=TEST_FLOW,
        current_step="initial_request",
        data={"requester": "Colin Requester"},
        history=[],
        checkpoints=[],
    )
    actor_alice = Actor("alice")
    instance.apply_command(
        "start_triage", {"notes": "Moved it on one step"}, actor=actor_alice
    )
    assert instance.current_step == "triage"
    assert "Moved it on one step" == instance.data["notes"]
    assert len(instance.history) == 1

    # Check the first history event is a CommandApplied event with correct data
    history_event_1 = instance.history[0]
    assert isinstance(history_event_1, CommandApplied)
    assert history_event_1.from_step == "initial_request"
    assert history_event_1.to_step == "triage"
    assert history_event_1.command == "start_triage"
    assert history_event_1.actor == actor_alice
    assert history_event_1.payload == {"notes": "Moved it on one step"}

    instance.apply_command(
        "complete",
        {"notes_on_completion": "Completed this task."},
        actor=actor_alice,
    )
    assert instance.current_step == "completed"
    assert len(instance.history) == 2

    # Check the second history event
    history_event_2 = instance.history[1]
    assert isinstance(history_event_2, CommandApplied)
    assert history_event_2.from_step == "triage"
    assert history_event_2.to_step == "completed"
    assert history_event_2.command == "complete"
    assert history_event_2.actor == actor_alice


def test_workflow_invalid_transition_raises_exception() -> None:
    instance = WorkflowInstance(
        id=str(uuid.uuid4()),
        name="test instance",
        definition=TEST_FLOW,
        current_step="initial_request",
        data={"requester": "Colin Requester"},
        history=[],
        checkpoints=[],
    )
    with pytest.raises(DomainException):
        instance.apply_command(
            "disallowed_command",
            {"notes": "Moved it on one step"},
            actor=Actor("alice"),
        )


def test_workflow_reveals_available_commands() -> None:
    instance = WorkflowInstance(
        id=str(uuid.uuid4()),
        name="test instance",
        definition=TEST_FLOW,
        current_step="initial_request",
        data={"requester": "Colin Requester"},
        history=[],
        checkpoints=[],
    )
    assert (
        "start_triage" in instance.definition.commands()
        and "complete" in instance.definition.commands()
    )


def test_workflow_reveals_available_commands_pretty() -> None:
    instance = WorkflowInstance(
        id=str(uuid.uuid4()),
        name="test instance",
        definition=TEST_FLOW,
        current_step="initial_request",
        data={"requester": "Colin Requester"},
        history=[],
        checkpoints=[],
    )
    assert (
        instance.definition.commands_pretty()
        == """start_triage: initial_request -> triage
complete: triage -> completed"""
    )


def test_checkpoint() -> None:
    "A checkpoint is a committed history object that allows for later retrieval."
    instance = WorkflowInstance(
        id=str(uuid.uuid4()),
        name="test instance",
        definition=TEST_FLOW,
        current_step="initial_request",
        data={"requester": "Colin Requester"},
        history=[],
        checkpoints=[],
    )
    actor_bob = Actor("bob")

    checkpoint = instance.save_checkpoint(label="Test Checkpoint", actor=actor_bob)
    assert checkpoint
    assert len(instance.checkpoints) == 1
    assert instance.checkpoints[0] == checkpoint
    assert instance.checkpoints[0].data["requester"] == "Colin Requester"

    assert len(instance.history) == 1
    history_event = instance.history[0]
    assert isinstance(history_event, CheckpointSaved)
    assert history_event.checkpoint == checkpoint
    assert history_event.actor == actor_bob
