"""Acceptance evidence, authority, and condition contract tests."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from pydantic import ValidationError
from sqlalchemy import ForeignKeyConstraint

from app.core.database import Base
from app.schemas.acceptance import AcceptanceDecisionCreate


def test_acceptance_schema_keeps_immutable_evidence_workspace_scoped() -> None:
    expected = {
        "acceptance_packages",
        "acceptance_package_items",
        "acceptance_decisions",
        "acceptance_conditions",
        "acceptance_condition_events",
        "acceptance_closures",
    }
    assert expected <= set(Base.metadata.tables)
    package_items = Base.metadata.tables["acceptance_package_items"]
    foreign_key_columns = {
        tuple(element.parent.name for element in constraint.elements)
        for constraint in package_items.constraints
        if isinstance(constraint, ForeignKeyConstraint)
    }
    assert ("acceptance_package_id", "workspace_id") in foreign_key_columns
    assert ("submission_id", "workspace_id") in foreign_key_columns
    assert ("deliverable_version_id", "workspace_id") in foreign_key_columns
    decision_constraints = {
        item.name for item in Base.metadata.tables["acceptance_decisions"].constraints
    }
    assert {
        "uq_acceptance_decisions_package",
        "ck_acceptance_decisions_kind",
    } <= decision_constraints


def test_conditional_acceptance_requires_conditions_and_other_decisions_reject_them() -> None:
    base = {"statement": "تصمیم کارفرما", "idempotency_key": "acceptance-decision-1"}
    with pytest.raises(ValidationError):
        AcceptanceDecisionCreate.model_validate({**base, "decision_kind": "CONDITIONAL_ACCEPT"})
    condition = {
        "description": "تکمیل پیوست",
        "responsible_id": uuid4(),
        "verifier_id": uuid4(),
        "due_at": datetime.now(UTC) + timedelta(days=1),
        "evidence_requirement": "نسخه نهایی سند",
    }
    with pytest.raises(ValidationError):
        AcceptanceDecisionCreate.model_validate(
            {**base, "decision_kind": "ACCEPT", "conditions": [condition]}
        )
    value = AcceptanceDecisionCreate.model_validate(
        {**base, "decision_kind": "CONDITIONAL_ACCEPT", "conditions": [condition]}
    )
    assert value.conditions[0].mandatory is True
