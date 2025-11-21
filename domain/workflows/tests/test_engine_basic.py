import dataclasses

import pytest
from domain.workflows.definitions import (Transition, WorkflowDefinition,
                                          WorkflowInstance)


def test_workflow_definition():
    flow = WorkflowDefinition(
        name="test definition",
        initial_step="initial request",
        steps={"initial_request", "triage", "allocation"},
        transitions=[Transition("initial_step", "triage", "start")],
    )
    assert flow
    with pytest.raises(dataclasses.FrozenInstanceError):
        # we cannot mutate the flow object
        flow.name = "Cedric"


def test_workflow_instance_exists():
    instance = WorkflowInstance(id="1", name="test instance")
    assert instance
