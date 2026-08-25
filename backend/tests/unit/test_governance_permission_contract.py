"""DG-09 governance permission and authority-matrix contract tests."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import ModuleType
from typing import Any, cast

import yaml

from app.core.permissions import PermissionCode


def load_revision() -> ModuleType:
    path = Path(__file__).parents[2] / "alembic" / "versions" / "0014_governance_permissions.py"
    spec = spec_from_file_location("governance_permission_revision", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load governance migration: {path}")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def contract() -> dict[str, Any]:
    path = Path(__file__).parents[3] / "contracts" / "permissions.yaml"
    return cast(dict[str, Any], yaml.safe_load(path.read_text(encoding="utf-8")))


def test_governance_migration_matches_permission_contract() -> None:
    revision = load_revision()
    canonical = contract()
    definitions = {item["code"]: item for item in canonical["permissions"]}
    enum_codes = {permission.value for permission in PermissionCode}
    for code, resource, action, description in revision.PERMISSION_SEEDS:
        assert code in enum_codes
        assert definitions[code] == {
            "code": code,
            "resource": resource,
            "action": action,
            "description": description,
        }
    for role_code, grants in revision.ROLE_GRANTS.items():
        assert list(grants) == [
            code for code in canonical["roles"][role_code]["grants"] if code in grants
        ]


def test_authority_lanes_remain_distinct() -> None:
    roles = contract()["roles"]
    team = set(roles["CONTRACTOR_TEAM_MEMBER"]["grants"])
    leader = set(roles["CONTRACTOR_PROJECT_LEADER"]["grants"])
    officer = set(roles["PROJECT_OFFICER"]["grants"])
    manager = set(roles["PROJECT_MANAGER"]["grants"])
    technical = set(roles["TECHNICAL_REVIEWER"]["grants"])
    employer = set(roles["EMPLOYER_REPRESENTATIVE"]["grants"])

    assert "DELIVERABLE_CONTRIBUTE" in team
    assert "SUBMISSION_CREATE" not in team
    assert {"DELIVERABLE_INTERNAL_REVIEW", "SUBMISSION_CREATE"} <= leader
    assert "PROJECT_MONITOR" in officer
    assert {"PROJECT_REVIEW", "PROJECT_RECOMMEND"}.isdisjoint(officer)
    assert {"PROJECT_REVIEW", "PROJECT_RECOMMEND"} <= manager
    assert {"TECHNICAL_REVIEW", "TECHNICAL_SIGN_OFF"} <= technical
    assert "ACCEPTANCE_DECIDE" not in technical
    assert "ACCEPTANCE_DECIDE" in employer
    assert "PROJECT_REVIEW" not in employer
