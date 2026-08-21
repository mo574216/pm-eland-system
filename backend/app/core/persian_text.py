# ruff: noqa: RUF001
"""Persian text normalization for comparison and search indexing."""

import unicodedata

_CHARACTER_TRANSLATION = str.maketrans(
    {
        "ي": "ی",
        "ى": "ی",
        "ك": "ک",
        "٠": "0",
        "١": "1",
        "٢": "2",
        "٣": "3",
        "٤": "4",
        "٥": "5",
        "٦": "6",
        "٧": "7",
        "٨": "8",
        "٩": "9",
        "۰": "0",
        "۱": "1",
        "۲": "2",
        "۳": "3",
        "۴": "4",
        "۵": "5",
        "۶": "6",
        "۷": "7",
        "۸": "8",
        "۹": "9",
    }
)
_IGNORED_JOINING_CHARACTERS = {"\u200c", "\u200d", "\u0640"}


def normalize_persian_search_text(value: str) -> str:
    """Create a non-display value suitable for Persian search matching."""
    compatible = unicodedata.normalize("NFKC", value).translate(_CHARACTER_TRANSLATION)
    without_marks = "".join(
        character
        for character in compatible
        if unicodedata.category(character) != "Mn" and character not in _IGNORED_JOINING_CHARACTERS
    )
    return " ".join(without_marks.casefold().split())
