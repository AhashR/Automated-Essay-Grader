from __future__ import annotations

from typing import Optional

SUPPORTED_LANGUAGES = {"en", "nl"}

LANGUAGE_ALIASES = {
    "english": "en",
    "eng": "en",
    "en_us": "en",
    "en_gb": "en",
    "dutch": "nl",
    "nederlands": "nl",
    "nl_nl": "nl",
}


def normalize_language(language: Optional[str], default: str = "en") -> str:
    """Normalize user or model language inputs to supported short codes."""
    fallback = default if default in SUPPORTED_LANGUAGES else "en"
    normalized = (language or fallback).strip().lower()
    normalized = LANGUAGE_ALIASES.get(normalized, normalized)
    return normalized if normalized in SUPPORTED_LANGUAGES else fallback