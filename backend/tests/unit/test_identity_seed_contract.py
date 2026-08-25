"""Identity seed contract tests."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import ModuleType
from typing import Any, cast

import yaml


def load_revision() -> ModuleType:
    revision_path = Path(__file__).parents[2] / "alembic" / "versions" / "0002_identity_schema.py"
    spec = spec_from_file_location("identity_schema_revision", revision_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load identity migration: {revision_path}")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_identity_seeds_match_canonical_permission_contract() -> None:
    revision = load_revision()
    contract_path = Path(__file__).parents[3] / "contracts" / "permissions.yaml"
    contract = cast(dict[str, Any], yaml.safe_load(contract_path.read_text(encoding="utf-8")))
    permission_seeds = revision.PERMISSION_SEEDS
    legacy_codes = {permission[1] for permission in permission_seeds}
    legacy_permissions = [
        definition for definition in contract["permissions"] if definition["code"] in legacy_codes
    ]
    seeded_permissions = [
        {
            "code": code,
            "resource": resource,
            "action": action,
            "description": description,
        }
        for _, code, resource, action, description in permission_seeds
    ]
    assert seeded_permissions == legacy_permissions

    seeded_roles = {role["code"]: role for role in revision.ROLE_SEEDS}
    for code in seeded_roles:
        definition = contract["roles"][code]
        assert seeded_roles[code]["description"] == definition["description"]
        assert seeded_roles[code]["is_system"] is True
        expected_grants = [grant for grant in definition["grants"] if grant in legacy_codes]
        assert list(revision.ROLE_GRANTS[code]) == expected_grants


def test_identity_seed_identifiers_are_unique() -> None:
    revision = load_revision()
    role_ids = [role["id"] for role in revision.ROLE_SEEDS]
    permission_ids = [permission[0] for permission in revision.PERMISSION_SEEDS]

    assert len(role_ids) == len(set(role_ids))
    assert len(permission_ids) == len(set(permission_ids))
