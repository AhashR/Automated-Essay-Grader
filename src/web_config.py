from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict

MODEL_OPTIONS = {
    "gemini": ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.5-flash-lite"],
}

MODEL_PROVIDER_LABELS = {
    "gemini": "Google Gemini",
}

LANGUAGE_LABELS = {
    "en": "English",
    "nl": "Nederlands",
}

TEMPLATES = {
    "en": "index.html",
    "nl": "index_nl.html",
}

MESSAGES: Dict[str, Dict[str, str]] = {
    "en": {
        "upload_or_paste_error": "Please upload a file or paste a learning story to analyze.",
        "analysis_error_prefix": "Error during analysis",
    },
    "nl": {
        "upload_or_paste_error": "Upload een bestand of plak een learning story om te analyseren.",
        "analysis_error_prefix": "Fout tijdens de analyse",
    },
}

RUBRIC_TYPE = "learning_story"

VECTOR_DATA_PATH = Path(
    os.getenv(
        "LEARNING_STORY_VECTOR_PATH",
        Path(__file__).resolve().parent.parent
        / "data"
        / "examples"
        / "learning_stories.json",
    )
)

QUALITY_MODEL_PATH = Path(
    os.getenv("STORY_QUALITY_MODEL_PATH")
    or os.getenv("LEARNING_STORY_QUALITY_MODEL_PATH")
    or Path(__file__).resolve().parent.parent
    / "models"
    / "story_quality_model.joblib"
)


def default_form_state() -> Dict[str, Any]:
    return {
        "model_provider": "gemini",
        "model_name": "gemini-2.5-flash",
        "temperature": 0.3,
        "max_tokens": 2000,
        "retrieval_top_k": 3,
        "retrieval_min_score": 0.08,
        "feedback_agent_language": "en",
        "essay_text": "",
    }


def model_options_for(provider: str) -> list[str]:
    return MODEL_OPTIONS.get(provider, MODEL_OPTIONS["gemini"])


def safe_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default