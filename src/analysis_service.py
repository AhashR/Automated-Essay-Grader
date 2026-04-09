from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

from src.essay_analyzer import EssayAnalyzer
from src.feedback_generator import FeedbackGenerator
from src.grading_engine import GradingEngine
from src.language_utils import normalize_language
from src.retrieval import LearningStoryRetriever
from src.story_quality_model import StoryQualityModel
from src.web_config import (
    LANGUAGE_LABELS,
    QUALITY_MODEL_PATH,
    RUBRIC_TYPE,
    VECTOR_DATA_PATH,
    safe_float,
    safe_int,
)
from src.web_presentation import derive_subject

logger = logging.getLogger(__name__)

LEARNING_STORY_RETRIEVER = LearningStoryRetriever(data_path=VECTOR_DATA_PATH)


def _load_quality_model() -> Optional[StoryQualityModel]:
    """Load optional quality model when a trained artifact is available."""
    if not QUALITY_MODEL_PATH.exists():
        return None

    model = StoryQualityModel(QUALITY_MODEL_PATH)
    if model.available:
        return model

    logger.warning("Story quality model unavailable: %s", model.error or "unknown")
    return None


QUALITY_MODEL = _load_quality_model()


def _get_quality_model() -> Optional[StoryQualityModel]:
    """Return cached quality model and attempt a late load when artifact appears."""
    global QUALITY_MODEL

    if QUALITY_MODEL is not None and QUALITY_MODEL.available:
        return QUALITY_MODEL

    if QUALITY_MODEL_PATH.exists():
        QUALITY_MODEL = _load_quality_model()

    return QUALITY_MODEL


def run_learning_story_analysis(
    content: str,
    form_state: Dict[str, Any],
    uploaded_filename: str = "",
) -> Dict[str, Any]:
    """Execute the full analyzer -> grading -> feedback workflow."""
    active_language = normalize_language(
        form_state.get("feedback_agent_language", "en"), default="en"
    )

    analyzer = EssayAnalyzer(
        model_provider=form_state.get("model_provider", "gemini"),
        model_name=form_state.get("model_name", "gemini-2.5-flash"),
        temperature=safe_float(form_state.get("temperature", 0.3), 0.3),
        max_tokens=safe_int(form_state.get("max_tokens", 2000), 2000),
        language=active_language,
        retriever=LEARNING_STORY_RETRIEVER,
        retrieval_top_k=max(1, min(8, safe_int(form_state.get("retrieval_top_k", 3), 3))),
        retrieval_min_score=max(
            0.0,
            min(0.9, safe_float(form_state.get("retrieval_min_score", 0.08), 0.08)),
        ),
    )

    grading_engine = GradingEngine(
        rubric_type=RUBRIC_TYPE,
        analyzer=analyzer,
        language=active_language,
        quality_model=_get_quality_model(),
    )

    feedback_generator = FeedbackGenerator(analyzer=analyzer, language=active_language)

    analysis_results = analyzer.analyze_essay(content)
    grade_results = grading_engine.grade_essay(
        content,
        analysis_results,
        language=active_language,
    )

    feedback = feedback_generator.generate_feedback(
        content,
        analysis_results,
        grade_results,
        language=active_language,
    )

    basic_stats = analysis_results.get("basic_stats", {})
    word_count = basic_stats.get("word_count", 0)
    quick_stats = {
        "word_count": word_count,
        "character_count": basic_stats.get("character_count", len(content)),
        "paragraph_count": basic_stats.get("paragraph_count", 0),
        "reading_time": max(1, word_count // 200) if word_count else 0,
    }

    results = {
        "quick_stats": quick_stats,
        "overall_score": grade_results.get("overall_score", 0),
        "base_overall_score": grade_results.get(
            "base_overall_score", grade_results.get("overall_score", 0)
        ),
        "score_adjustment": grade_results.get("score_adjustment", 0),
        "letter_grade": grade_results.get("letter_grade", "N/A"),
        "breakdown": list(grade_results.get("grading_breakdown", {}).values()),
        "feedback": feedback,
        "detected_language": LANGUAGE_LABELS.get(
            analysis_results.get("language", "en"), "English"
        ),
        "feedback_language": LANGUAGE_LABELS.get(
            feedback.get("language", "en"), "English"
        ),
        "grammar_issues": analysis_results.get("grammar", {}).get("grammar_issues", []),
        "quality_assessment": grade_results.get(
            "quality_assessment",
            {
                "available": False,
                "label": None,
                "confidence": None,
                "reason": "quality_model_not_configured",
            },
        ),
        "ai_feedback": feedback.get("ai_comprehensive_feedback", ""),
        "rubric_source": grade_results.get("rubric_source", "unknown"),
    }

    analysis_id = uuid4().hex[:12]
    cache_payload = {
        "results": results,
        "form_state": {
            "model_provider": form_state.get("model_provider", "gemini"),
            "model_name": form_state.get("model_name", "gemini-2.5-flash"),
            "temperature": safe_float(form_state.get("temperature", 0.3), 0.3),
            "max_tokens": safe_int(form_state.get("max_tokens", 2000), 2000),
            "retrieval_top_k": max(
                1, min(8, safe_int(form_state.get("retrieval_top_k", 3), 3))
            ),
            "retrieval_min_score": max(
                0.0,
                min(
                    0.9,
                    safe_float(form_state.get("retrieval_min_score", 0.08), 0.08),
                ),
            ),
            "essay_text": form_state.get("essay_text", ""),
        },
    }

    recent_entry = {
        "id": analysis_id,
        "subject": derive_subject(content, uploaded_filename),
        "prompted_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "overall_score": f"{(results['overall_score'] / 10):.1f}/10",
        "word_count": results["quick_stats"]["word_count"],
        "letter_grade": results["letter_grade"],
    }

    return {
        "analysis_id": analysis_id,
        "results": results,
        "cache_payload": cache_payload,
        "recent_entry": recent_entry,
    }