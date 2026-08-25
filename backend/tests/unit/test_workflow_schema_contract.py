"""Versioned workflow persistence and request-graph contract tests."""

from uuid import uuid4

import pytest
from pydantic import ValidationError
from sqlalchemy import ForeignKeyConstraint

from app.core.database import Base
from app.models import workflow as _workflow_models  # noqa: F401
from app.schemas.workflow import WorkflowDefinitionCreate


def valid_definition() -> dict[str, object]:
    return {
        "name": "چرخه تحویل",
        "states": [
            {"key": "draft", "label": "پیش‌نویس", "sequence_number": 1, "is_initial": True},
            {"key": "submitted", "label": "ارسال‌شده", "sequence_number": 2},
        ],
        "transitions": [
            {
                "key": "submit",
                "label": "ارسال رسمی",
                "from_state_key": "draft",
                "to_state_key": "submitted",
                "required_permission": "SUBMISSION_CREATE",
                "authority_kind": "FORMAL_SUBMISSION",
                "assignment_kind": "SUBMITTER",
            }
        ],
    }


def test_workflow_schema_has_workspace_and_version_integrity() -> None:
    expected = {
        "workflow_definitions",
        "workflow_definition_versions",
        "workflow_state_definitions",
        "workflow_transition_definitions",
        "workflow_instances",
        "workflow_assignments",
        "workflow_transition_events",
    }
    assert expected <= set(Base.metadata.tables)
    event = Base.metadata.tables["workflow_transition_events"]
    composite_foreign_keys = {
        tuple(element.parent.name for element in constraint.elements)
        for constraint in event.constraints
        if isinstance(constraint, ForeignKeyConstraint)
    }
    assert ("instance_id", "workspace_id") in composite_foreign_keys
    assert ("transition_id", "definition_version_id", "workspace_id") in composite_foreign_keys
    assert ("resulting_state_id", "definition_version_id", "workspace_id") in composite_foreign_keys


def test_workflow_graph_requires_one_initial_state_and_known_permissions() -> None:
    payload = valid_definition()
    assert WorkflowDefinitionCreate.model_validate(payload).states[0].label == "پیش‌نویس"

    no_initial = valid_definition()
    states = no_initial["states"]
    assert isinstance(states, list)
    states[0]["is_initial"] = False
    with pytest.raises(ValidationError):
        WorkflowDefinitionCreate.model_validate(no_initial)

    unknown_permission = valid_definition()
    transitions = unknown_permission["transitions"]
    assert isinstance(transitions, list)
    transitions[0]["required_permission"] = f"UNKNOWN_{uuid4().hex}"
    with pytest.raises(ValidationError):
        WorkflowDefinitionCreate.model_validate(unknown_permission)
