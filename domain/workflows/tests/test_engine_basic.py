import dataclasses
import uuid
from datetime import datetime

import pytest
from domain.workflows.definitions import (Actor, Checkpoint, CheckpointSaved,
                                          CommandApplied, StateRestored,
                                          Transition, WorkflowDefinition,
                                          WorkflowInstance)
from domain.workflows.errors import (DomainException, NoAvailableCheckpoint,
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
    assert instance.active_checkpoint_id == checkpoint.id

    assert len(instance.history) == 1
    history_event = instance.history[0]
    assert isinstance(history_event, CheckpointSaved)
    assert history_event.checkpoint == checkpoint
    assert history_event.actor == actor_bob


@pytest.fixture
def basic_instance() -> WorkflowInstance:
    """Returns a clean workflow instance."""
    return WorkflowInstance(
        id=str(uuid.uuid4()),
        name="test instance",
        definition=TEST_FLOW,
        current_step="initial_request",
        data={"requester": "Colin Requester"},
        history=[],
        checkpoints=[],
    )


def test_rollback_and_rollforward(basic_instance: WorkflowInstance) -> None:
    instance = basic_instance
    actor = Actor("test_actor")

    # 1. Initial state, save first checkpoint
    cp1 = instance.save_checkpoint(label="CP1", actor=actor)
    assert instance.current_step == "initial_request"
    assert instance.active_checkpoint_id == cp1.id
    assert instance.data["requester"] == "Colin Requester"

    # 2. Apply command, state becomes "live"
    instance.apply_command("start_triage", {"notes": "Step 2"}, actor=actor)
    assert instance.current_step == "triage"
    assert instance.active_checkpoint_id is None

    # 3. Save second checkpoint
    cp2 = instance.save_checkpoint(label="CP2", actor=actor)
    assert instance.current_step == "triage"
    assert instance.data["notes"] == "Step 2"
    assert instance.active_checkpoint_id == cp2.id

    # 4. Rollback from active checkpoint CP2 to CP1
    instance.rollback(actor=actor)
    assert instance.current_step == "initial_request"
    assert "notes" not in instance.data  # data is restored from CP1
    assert instance.active_checkpoint_id == cp1.id
    # Check history event
    last_event = instance.history[3]
    assert isinstance(last_event, StateRestored)
    assert last_event.checkpoint_id == cp1.id
    assert last_event.direction == "rollback"

    # 5. Rollforward to second checkpoint
    instance.rollforward(actor=actor)
    assert instance.current_step == "triage"
    assert instance.data["notes"] == "Step 2"
    assert instance.active_checkpoint_id == cp2.id
    last_event = instance.history[-1]
    assert isinstance(last_event, StateRestored)
    assert last_event.checkpoint_id == cp2.id
    assert last_event.direction == "rollforward"


def test_rollback_edge_cases(basic_instance: WorkflowInstance) -> None:
    instance = basic_instance
    actor = Actor("test_actor")

    # Can't rollback with no checkpoints
    with pytest.raises(NoAvailableCheckpoint, match="no checkpoints exist"):
        instance.rollback(actor=actor)

    # Save one checkpoint
    instance.save_checkpoint(label="CP1", actor=actor)

    # Can't rollback when at the only checkpoint
    with pytest.raises(NoAvailableCheckpoint, match="already at the earliest"):
        instance.rollback(actor=actor)


def test_rollforward_edge_cases(basic_instance: WorkflowInstance) -> None:
    instance = basic_instance
    actor = Actor("test_actor")

    # Can't rollforward when instance is live and has no checkpoints
    with pytest.raises(NoAvailableCheckpoint, match="current state is live"):
        instance.rollforward(actor=actor)

    instance.save_checkpoint(label="CP1", actor=actor)

    # Can't rollforward when at the latest checkpoint
    with pytest.raises(NoAvailableCheckpoint, match="already at the latest"):
        instance.rollforward(actor=actor)
