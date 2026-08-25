"""Phase schema and lock-state contract tests."""

from typing import cast

from sqlalchemy import Table

from app.models.phase import Phase, PhaseDeliverable


def test_phase_model_preserves_workspace_order_and_lock_state() -> None:
    table = cast(Table, Phase.__table__)
    assert set(table.columns.keys()) == {
        "id",
        "workspace_id",
        "key",
        "name",
        "description",
        "sequence_number",
        "status",
        "is_locked",
        "locked_by",
        "locked_at",
        "created_at",
        "updated_at",
        "version",
    }
    assert next(iter(table.c.workspace_id.foreign_keys)).ondelete == "CASCADE"
    assert next(iter(table.c.locked_by.foreign_keys)).ondelete == "SET NULL"
    names = {constraint.name for constraint in table.constraints}
    assert "uq_phases_workspace_key" in names
    assert "uq_phases_workspace_sequence" in names
    assert "ck_phases_status" in names


def test_phase_deliverable_requires_one_supported_resource() -> None:
    table = cast(Table, PhaseDeliverable.__table__)
    names = {constraint.name for constraint in table.constraints}
    assert "ck_phase_deliverables_single_resource" in names
    assert "ck_phase_deliverables_status" in names
    assert next(iter(table.c.phase_id.foreign_keys)).ondelete == "CASCADE"
