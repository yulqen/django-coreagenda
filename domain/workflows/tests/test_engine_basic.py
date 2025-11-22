import dataclasses

import pytest
from domain.workflows.definitions import (Transition, WorkflowDefinition,
                                          WorkflowInstance)


def test_workflow_definition() -> None:
    flow = WorkflowDefinition(
        name="test definition",
        initial_step="initial request",
        steps={"initial_request", "triage", "allocation"},
        transitions=[
            Transition("initial_step", "triage", "start"),
            Transition("triage", "compltion", "basic_checks"),
        ],
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        # we cannot mutate the flow object
        flow.name = "Cedric"  # type: ignore
    assert len(flow.steps) == 3
    assert len(flow.transitions) == 2


def test_workflow_instance_exists() -> None:
    instance = WorkflowInstance(id="1", name="test instance")
    assert instance
