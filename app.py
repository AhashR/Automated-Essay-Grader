import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from uuid import uuid4

import markdown
from dotenv import load_dotenv
from flask import Flask, flash, jsonify, render_template, request, session
from markupsafe import Markup, escape

# Add src directory to path
sys.path.append(str(Path(__file__).parent / "src"))

from essay_analyzer import EssayAnalyzer  # noqa: E402
from feedback_generator import FeedbackGenerator  # noqa: E402
from grading_engine import GradingEngine  # noqa: E402
from retrieval import LearningStoryRetriever  # noqa: E402
from story_quality_model import StoryQualityModel  # noqa: E402
from utils import load_document, validate_file  # noqa: E402

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "change-me-in-production")
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

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
        Path(__file__).resolve().parent / "data" / "examples" / "learning_stories.json",
    )
)
QUALITY_MODEL_PATH = Path(
    os.getenv(
        "LEARNING_STORY_QUALITY_MODEL_PATH",
        Path(__file__).resolve().parent / "models" / "learning_story_good_bad.joblib",
    )
)

LEARNING_STORY_RETRIEVER = LearningStoryRetriever(data_path=VECTOR_DATA_PATH)
LEARNING_STORY_QUALITY_MODEL = StoryQualityModel(QUALITY_MODEL_PATH)
RECENT_ANALYSIS_CACHE: Dict[str, Dict[str, Any]] = {}
PROCESS_BOOT_ID = uuid4().hex


def _default_form_state() -> Dict[str, Any]:
    return {
        "model_provider": "gemini",
        "model_name": "gemini-2.5-flash",
        "feedback_agent_language": "en",
        "essay_text": "",
    }


def _normalize_language(language: Optional[str]) -> str:
    normalized = (language or "en").strip().lower()
    aliases = {"english": "en", "eng": "en", "dutch": "nl", "nederlands": "nl"}
    normalized = aliases.get(normalized, normalized)
    return normalized if normalized in LANGUAGE_LABELS else "en"


def _resolve_language() -> str:
    lang_arg = request.args.get("lang")
    if lang_arg:
        lang = _normalize_language(lang_arg)
        session["ui_language"] = lang
        return lang
    return _normalize_language(session.get("ui_language", "en"))


def _model_options_for(provider: str) -> list[str]:
    return MODEL_OPTIONS.get(provider, MODEL_OPTIONS["gemini"])


def _get_recent_analyses() -> list[Dict[str, Any]]:
    recent_analyses = session.get("recent_analyses", [])
    if not isinstance(recent_analyses, list):
        return []
    return recent_analyses[:10]


def _add_recent_analysis(entry: Dict[str, Any]) -> None:
    recent_analyses = _get_recent_analyses()
    recent_analyses.insert(0, entry)
    session["recent_analyses"] = recent_analyses[:10]
    session.modified = True


def _cache_analysis_result(entry_id: str, payload: Dict[str, Any]) -> None:
    RECENT_ANALYSIS_CACHE[entry_id] = payload


def _load_cached_analysis(entry_id: str) -> Optional[Dict[str, Any]]:
    if not entry_id:
        return None

    # Only allow opening analyses that belong to the current session history.
    recent_ids = {item.get("id") for item in _get_recent_analyses()}
    if entry_id not in recent_ids:
        return None

    return RECENT_ANALYSIS_CACHE.get(entry_id)


def _sync_session_with_process() -> None:
    session_boot_id = session.get("process_boot_id")
    if session_boot_id == PROCESS_BOOT_ID:
        return

    session["process_boot_id"] = PROCESS_BOOT_ID
    session.pop("recent_analyses", None)
    session.modified = True


def _derive_subject(content: str, uploaded_filename: str = "") -> str:
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        # Strip lightweight markdown heading/bullet prefixes for cleaner titles.
        cleaned = line.lstrip("#*- ").strip()
        if cleaned:
            return cleaned[:90]

    if uploaded_filename:
        return Path(uploaded_filename).stem[:90]
    return "Untitled learning story"


def _render_feedback_markdown(text: str) -> Markup:
    if not text:
        return Markup("")

    safe_text = str(escape(text))
    rendered = markdown.markdown(
        safe_text,
        extensions=["extra", "sane_lists", "nl2br"],
        output_format="html5",
    )
    return Markup(rendered)


@app.template_filter("render_feedback")
def render_feedback(text: str) -> Markup:
    return _render_feedback_markdown(text)


@app.route("/", methods=["GET", "POST"])
def index():
    _sync_session_with_process()

    active_language = _resolve_language()
    template_name = TEMPLATES.get(active_language, TEMPLATES["en"])

    form_state = _default_form_state()
    form_state["feedback_agent_language"] = active_language
    results = None
    recent_analyses = _get_recent_analyses()

    requested_analysis_id = request.args.get("analysis_id", "").strip()
    if request.method == "GET" and requested_analysis_id:
        cached = _load_cached_analysis(requested_analysis_id)
        if cached:
            results = cached.get("results")
            cached_form_state = cached.get("form_state")
            if isinstance(cached_form_state, dict):
                form_state.update(cached_form_state)
                form_state["feedback_agent_language"] = active_language

    if request.method == "POST":
        form_state["model_provider"] = request.form.get("model_provider", "gemini")
        form_state["model_name"] = request.form.get("model_name", "gemini-2.5-flash")
        form_state["temperature"] = float(request.form.get("temperature", 0.3))
        form_state["max_tokens"] = int(request.form.get("max_tokens", 2000))
        form_state["feedback_agent_language"] = _normalize_language(
            request.form.get(
                "feedback_agent_language", form_state["feedback_agent_language"]
            )
        )
        active_language = form_state["feedback_agent_language"]
        template_name = TEMPLATES.get(active_language, TEMPLATES["en"])
        session["ui_language"] = active_language
        form_state["essay_text"] = request.form.get("essay_text", "")

        model_choices = _model_options_for(form_state["model_provider"])
        if form_state["model_name"] not in model_choices:
            form_state["model_name"] = model_choices[0]

        uploaded_file = request.files.get("essay_file")
        uploaded_filename = uploaded_file.filename if uploaded_file else ""
        content = ""
        messages = MESSAGES.get(active_language, MESSAGES["en"])

        try:
            if uploaded_file and uploaded_file.filename:
                is_valid, error_message = validate_file(
                    uploaded_file, return_error=True
                )
                if not is_valid:
                    flash(error_message, "error")
                    return render_template(
                        template_name,
                        form_state=form_state,
                        model_options=model_choices,
                        model_provider_labels=MODEL_PROVIDER_LABELS,
                        model_options_map=MODEL_OPTIONS,
                        language_labels=LANGUAGE_LABELS,
                        active_language=active_language,
                        results=results,
                        recent_analyses=recent_analyses,
                    )
                content = load_document(uploaded_file)
            else:
                content = form_state["essay_text"]

            if not content or not content.strip():
                flash(messages["upload_or_paste_error"], "error")
                return render_template(
                    template_name,
                    form_state=form_state,
                    model_options=model_choices,
                    model_provider_labels=MODEL_PROVIDER_LABELS,
                    model_options_map=MODEL_OPTIONS,
                    language_labels=LANGUAGE_LABELS,
                    active_language=active_language,
                    results=results,
                    recent_analyses=recent_analyses,
                )

            analyzer = EssayAnalyzer(
                model_provider=form_state["model_provider"],
                model_name=form_state["model_name"],
                temperature=form_state["temperature"],
                max_tokens=form_state["max_tokens"],
                language=form_state["feedback_agent_language"],
                retriever=LEARNING_STORY_RETRIEVER,
            )

            grading_engine = GradingEngine(
                rubric_type=RUBRIC_TYPE,
                analyzer=analyzer,
                language=form_state["feedback_agent_language"],
                quality_model=LEARNING_STORY_QUALITY_MODEL,
            )

            feedback_generator = FeedbackGenerator(
                analyzer=analyzer, language=form_state["feedback_agent_language"]
            )

            analysis_results = analyzer.analyze_essay(
                content,
            )

            grade_results = grading_engine.grade_essay(
                content,
                analysis_results,
                language=form_state["feedback_agent_language"],
            )

            feedback = feedback_generator.generate_feedback(
                content,
                analysis_results,
                grade_results,
                language=form_state["feedback_agent_language"],
            )

            basic_stats = analysis_results.get("basic_stats", {})
            word_count = basic_stats.get("word_count", 0)
            quick_stats = {
                "word_count": word_count,
                "character_count": basic_stats.get("character_count", len(content)),
                "paragraph_count": basic_stats.get("paragraph_count", 0),
                "reading_time": max(1, word_count // 200) if word_count else 0,
            }

            breakdown_values = list(grade_results.get("grading_breakdown", {}).values())
            grammar_issues = analysis_results.get("grammar", {}).get(
                "grammar_issues", []
            )

            results = {
                "quick_stats": quick_stats,
                "overall_score": grade_results.get("overall_score", 0),
                "base_overall_score": grade_results.get("base_overall_score", 0),
                "score_adjustment": grade_results.get("score_adjustment", 0),
                "letter_grade": grade_results.get("letter_grade", "N/A"),
                "breakdown": breakdown_values,
                "feedback": feedback,
                "quality_assessment": grade_results.get("quality_assessment", {}),
                "detected_language": LANGUAGE_LABELS.get(
                    analysis_results.get("language", "en"), "English"
                ),
                "feedback_language": LANGUAGE_LABELS.get(
                    feedback.get("language", "en"), "English"
                ),
                "grammar_issues": grammar_issues,
                "ai_feedback": feedback.get("ai_comprehensive_feedback", ""),
                "rubric_source": grade_results.get("rubric_source", "unknown"),
            }

            analysis_id = uuid4().hex[:12]
            _cache_analysis_result(
                analysis_id,
                {
                    "results": results,
                    "form_state": {
                        "model_provider": form_state["model_provider"],
                        "model_name": form_state["model_name"],
                        "temperature": form_state["temperature"],
                        "max_tokens": form_state["max_tokens"],
                        "essay_text": form_state["essay_text"],
                    },
                },
            )

            _add_recent_analysis(
                {
                    "id": analysis_id,
                    "subject": _derive_subject(content, uploaded_filename),
                    "prompted_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "overall_score": f"{(results['overall_score'] / 10):.1f}/10",
                    "word_count": results["quick_stats"]["word_count"],
                    "letter_grade": results["letter_grade"],
                }
            )
            recent_analyses = _get_recent_analyses()
        except Exception as exc:
            flash(f"{messages['analysis_error_prefix']}: {exc}", "error")

    model_options = _model_options_for(form_state["model_provider"])
    return render_template(
        template_name,
        form_state=form_state,
        model_options=model_options,
        model_provider_labels=MODEL_PROVIDER_LABELS,
        model_options_map=MODEL_OPTIONS,
        language_labels=LANGUAGE_LABELS,
        active_language=active_language,
        results=results,
        recent_analyses=recent_analyses,
    )


@app.route("/health")
def health() -> Any:
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=False)
