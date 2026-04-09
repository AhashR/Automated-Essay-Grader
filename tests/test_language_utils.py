import pytest

from src.language_utils import normalize_language


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("en", "en"),
        ("english", "en"),
        ("EN_us", "en"),
        ("nl", "nl"),
        ("dutch", "nl"),
        ("Nederlands", "nl"),
        ("unknown", "en"),
        (None, "en"),
    ],
)
def test_normalize_language_defaults(raw, expected):
    assert normalize_language(raw) == expected


def test_normalize_language_respects_supported_default():
    assert normalize_language("unknown", default="nl") == "nl"
