"""
User takes an action -> engine applies a command.

You can define workflows for:
- AgendaItems
- Meetings
- ActionItems
- ExternalRequests

whatever!

WorkflowInstance.apply_command("submit", data, user) is called, for example.

The engine:

- looks up the allowed transition (from current step: details -> triage)
- executes any guards (e.g. must have description filled in)
- updates the instance data (e.g. address presenter emails, descriptions, etc)
- moves the current_step forward
- appends history events (e.g. "submitted at 12:03 by Tommy")

This is the heart of the engine: commands -> transitions -> new state.

---

Later, when we add Django adapter layers:

The engine doesn't talk to Django at all.

We will create a Respository layer that adapts between:
- Pure domain object (WorkflowInstance)
- Django ORM model (WorkflowInstanceModel)

The adapter:
- loads from the DB and builds a domain instance
- saves the domain instance -> writes JSON back to DB

Django views and forms just ask the engine what to do; views are thin
- load the correct WorkflowInstance via the Repository
- determine the current step
- render the form for the next step
- When POST comes in:
    - If "continue", call .apply_command()
    - if "save for later, call .save_checkpoint()
    - save it back to the DB
    - redirect to the next page
The viewer never hard-codes:
- step names
- allowed transitions
- business rules
- workflow branching

Workflow definition drives everything.
"""

import dataclasses
from datetime import datetime

import pytest
from domain.workflows.definitions import (Checkpoint, Transition,
                                          WorkflowDefinition,
                                          WorkflowDefinitionValidationError,
                                          WorkflowInstance)


TEST_FLOW = WorkflowDefinition(
    name="test definition",
    initial_step="initial request",
    steps={"initial request", "triage", "allocation"},
    # the first arg of each Transition (from_step) should match declared steps
    transitions=[
        Transition("initial_step", "triage", "start"),
        Transition("triage", "compltion", "basic_checks"),
    ],
)


def test_checkpoint_exists() -> None:
    checkpoint = Checkpoint(
        id="1",
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


def test_worflow_definition_basic_validity() -> None:
    with pytest.raises(WorkflowDefinitionValidationError):
        WorkflowDefinition(
            name="bad definition",
            initial_step="initial request",
            steps=set(),  # steps are mandatory
            transitions=[],  # transitions are mandatory
        ).is_valid()
    with pytest.raises(WorkflowDefinitionValidationError):
        WorkflowDefinition(
            name="bad definition",
            initial_step="initial request",
            steps={"initial_request"},  # steps are mandatory
            transitions=[],  # transitions are mandatory
        ).is_valid()
    with pytest.raises(WorkflowDefinitionValidationError):
        WorkflowDefinition(
            name="bad definition",
            initial_step="initial request",
            steps={"first request", "second request"},  # steps are mandatory
            transitions=[],  # transitions are mandatory
        ).is_valid()
    with pytest.raises(WorkflowDefinitionValidationError):
        WorkflowDefinition(
            name="bad definition",
            initial_step="",
            steps={"first request", "second request"},  # steps are mandatory
            transitions=[],  # transitions are mandatory
        ).is_valid()
    with pytest.raises(WorkflowDefinitionValidationError):
        WorkflowDefinition(
            name="bad definition",
            initial_step="",
            steps={"first request", "second request"},  # steps are mandatory
            transitions=[],  # transitions are mandatory
        ).is_valid()


def test_workflow_instance_exists() -> None:
    instance = WorkflowInstance(
        id="1",
        name="test instance",
        definition=TEST_FLOW,
        current_step="initial request",
        data={},
        history=[],
        checkpoints=[],
    )
    assert instance.definition.name == "test definition"
