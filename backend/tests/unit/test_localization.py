"""Persian localization boundary tests."""

from pathlib import Path

import pytest
import yaml

from app.core.localization import PUBLIC_ERROR_MESSAGES_FA_IR, public_error_message


def test_registered_error_code_resolves_to_persian_message() -> None:
    assert public_error_message("RESOURCE_LOCKED") == (
        "این مورد در مرحله قفل‌شده قرار دارد و قابل ویرایش نیست."
    )


def test_unregistered_error_code_fails_instead_of_exposing_fallback_copy() -> None:
    with pytest.raises(ValueError, match="No fa-IR public message"):
        public_error_message("UNKNOWN_ERROR")


def test_runtime_message_catalog_matches_shared_error_contract() -> None:
    contract_path = Path(__file__).parents[3] / "contracts" / "error-codes.yaml"
    contract = yaml.safe_load(contract_path.read_text(encoding="utf-8"))
    contract_messages = {
        code: definition["default_message"] for code, definition in contract["errors"].items()
    }

    assert PUBLIC_ERROR_MESSAGES_FA_IR == contract_messages
