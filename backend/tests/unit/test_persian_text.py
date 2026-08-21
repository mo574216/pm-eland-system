"""Persian search normalization tests."""

import pytest

from app.core.persian_text import normalize_persian_search_text


@pytest.mark.parametrize(
    ("left", "right"),
    [
        ("يادگيري", "یادگیری"),
        ("كتاب", "کتاب"),
        ("می\u200cرود", "میرود"),
        ("عَـلَم", "علم"),
        ("پروژه ۱۲۳", "پروژه ١٢٣"),
        ("  دانش   پروژه ", "دانش پروژه"),
    ],
)
def test_equivalent_persian_search_values_normalize_identically(left: str, right: str) -> None:
    assert normalize_persian_search_text(left) == normalize_persian_search_text(right)


def test_search_normalization_does_not_mutate_display_value() -> None:
    display_value = "پروژه‌ی شماره ۱۲"

    normalized = normalize_persian_search_text(display_value)

    assert display_value == "پروژه‌ی شماره ۱۲"
    assert normalized == "پروژهی شماره 12"
