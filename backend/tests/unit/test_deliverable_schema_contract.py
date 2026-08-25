"""Deliverable evidence integrity and readiness contract tests."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from pydantic import ValidationError
from sqlalchemy import ForeignKeyConstraint

from app.core.database import Base
from app.core.deliverable_workflow import DELIVERABLE_STATES, DELIVERABLE_TRANSITIONS
from app.models.deliverable import Deliverable, DeliverablePackageItem
from app.schemas.deliverable import DeliverableCreate
from app.services.deliverable import DeliverableService


def test_deliverable_schema_preserves_workspace_and_immutable_evidence_scope() -> None:
    expected = {
        "deliverables",
        "deliverable_assignments",
        "deliverable_versions",
        "deliverable_package_items",
        "submissions",
        "submission_recipients",
        "submission_withdrawals",
    }
    assert expected <= set(Base.metadata.tables)
    submissions = Base.metadata.tables["submissions"]
    composite_foreign_keys = {
        tuple(element.parent.name for element in constraint.elements)
        for constraint in submissions.constraints
        if isinstance(constraint, ForeignKeyConstraint)
    }
    assert ("deliverable_id", "workspace_id") in composite_foreign_keys
    assert ("deliverable_version_id", "workspace_id") in composite_foreign_keys
    assert ("prior_submission_id", "workspace_id") in composite_foreign_keys
    assert {constraint.name for constraint in submissions.constraints} >= {
        "uq_submissions_sequence",
        "uq_submissions_idempotency",
    }


def test_create_contract_rejects_reversed_dates_and_duplicate_requirements() -> None:
    now = datetime.now(UTC)
    base = {
        "name": "خروجی مرحله",
        "owner_id": uuid4(),
        "internal_reviewer_id": uuid4(),
        "internal_due_at": now + timedelta(days=2),
        "official_due_at": now + timedelta(days=1),
    }
    with pytest.raises(ValidationError):
        DeliverableCreate.model_validate(base)

    with pytest.raises(ValidationError):
        DeliverableCreate.model_validate(
            {
                "name": "خروجی مرحله",
                "owner_id": uuid4(),
                "internal_reviewer_id": uuid4(),
                "requirements": [
                    {"key": "spec", "label": "مشخصات", "resource_kind": "FORM_INSTANCE"},
                    {"key": "spec", "label": "سند", "resource_kind": "DOCUMENT_VERSION"},
                ],
            }
        )


def test_readiness_reports_named_missing_requirements() -> None:
    deliverable = Deliverable(
        id=uuid4(),
        workspace_id=uuid4(),
        phase_id=uuid4(),
        key="deliverable_test",
        name="Demo",
        requirements=[
            {
                "key": "form",
                "label": "فرم مشخصات",
                "resource_kind": "FORM_INSTANCE",
                "required": True,
            },
            {
                "key": "file",
                "label": "سند پیوست",
                "resource_kind": "DOCUMENT_VERSION",
                "required": True,
            },
        ],
        version=1,
    )
    item = DeliverablePackageItem(
        id=uuid4(),
        workspace_id=deliverable.workspace_id,
        deliverable_version_id=uuid4(),
        resource_kind="FORM_INSTANCE",
        resource_id=uuid4(),
        label_snapshot="فرم مشخصات",
        is_required=True,
        metadata_snapshot={"requirement_key": "form"},
    )
    readiness = DeliverableService._readiness(deliverable, (item,))
    assert readiness.ready is False
    assert readiness.completed_required == 1
    assert readiness.missing == ["سند پیوست"]


def test_baseline_lifecycle_keeps_authority_lanes_and_policy_as_metadata() -> None:
    state_keys = {state[0] for state in DELIVERABLE_STATES}
    assert state_keys == {"preparation", "internal_review", "ready", "submitted"}
    transitions = {transition[0]: transition for transition in DELIVERABLE_TRANSITIONS}
    assert transitions["request_internal_review"][4:7] == (
        "DELIVERABLE_CONTRIBUTE",
        "CONTRIBUTION",
        "CONTRIBUTOR",
    )
    assert transitions["mark_ready"][4:7] == (
        "DELIVERABLE_INTERNAL_REVIEW",
        "INTERNAL_REVIEW",
        "INTERNAL_REVIEWER",
    )
    assert transitions["formal_submit"][4:7] == (
        "SUBMISSION_CREATE",
        "FORMAL_SUBMISSION",
        "OWNER",
    )
    assert transitions["formal_submit"][8] == {"requires_active_submission": True}
