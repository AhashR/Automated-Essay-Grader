import os
from typing import Any, Dict, Optional
from uuid import uuid4

from dotenv import load_dotenv
from flask import Flask, flash, jsonify, render_template, request, session

from src.analysis_service import run_learning_story_analysis
from src.language_utils import normalize_language
from src.utils import load_document, validate_file
from src.web_config import (
    LANGUAGE_LABELS,
    MESSAGES,
    MODEL_OPTIONS,
    MODEL_PROVIDER_LABELS,
    TEMPLATES,
    default_form_state,
    model_options_for,
    safe_float,
    safe_int,
)
from src.web_presentation import render_feedback_markdown

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "change-me-in-production")
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

RECENT_ANALYSIS_CACHE: Dict[str, Dict[str, Any]] = {}
PROCESS_BOOT_ID = uuid4().hex


def _resolve_language() -> str:
    lang_arg = request.args.get("lang")
    if lang_arg:
        lang = normalize_language(lang_arg, default="en")
        session["ui_language"] = lang
        return lang
    return normalize_language(session.get("ui_language", "en"), default="en")


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


def _render_index(
    template_name: str,
    form_state: Dict[str, Any],
    active_language: str,
    results: Optional[Dict[str, Any]],
    recent_analyses: list[Dict[str, Any]],
):
    model_options = model_options_for(form_state["model_provider"])
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


@app.template_filter("render_feedback")
def render_feedback(text: str):
    return render_feedback_markdown(text)


@app.route("/", methods=["GET", "POST"])
def index():
    _sync_session_with_process()

    active_language = _resolve_language()
    template_name = TEMPLATES.get(active_language, TEMPLATES["en"])

    form_state = default_form_state()
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
        if form_state["model_provider"] not in MODEL_OPTIONS:
            form_state["model_provider"] = "gemini"

        form_state["model_name"] = request.form.get("model_name", "gemini-2.5-flash")
        form_state["temperature"] = safe_float(request.form.get("temperature"), 0.3)
        form_state["max_tokens"] = safe_int(request.form.get("max_tokens"), 2000)
        form_state["retrieval_top_k"] = max(
            1, min(8, safe_int(request.form.get("retrieval_top_k"), 3))
        )
        form_state["retrieval_min_score"] = max(
            0.0,
            min(
                0.9,
                safe_float(request.form.get("retrieval_min_score"), 0.08),
            ),
        )
        form_state["feedback_agent_language"] = normalize_language(
            request.form.get(
                "feedback_agent_language", form_state["feedback_agent_language"]
            ),
            default="en",
        )

        active_language = form_state["feedback_agent_language"]
        template_name = TEMPLATES.get(active_language, TEMPLATES["en"])
        session["ui_language"] = active_language
        form_state["essay_text"] = request.form.get("essay_text", "")

        model_choices = model_options_for(form_state["model_provider"])
        if form_state["model_name"] not in model_choices:
            form_state["model_name"] = model_choices[0]

        uploaded_file = request.files.get("essay_file")
        uploaded_filename = (uploaded_file.filename or "") if uploaded_file else ""
        content = ""
        messages = MESSAGES.get(active_language, MESSAGES["en"])

        try:
            if uploaded_file and uploaded_file.filename:
                validation_result = validate_file(uploaded_file, return_error=True)
                if isinstance(validation_result, tuple):
                    is_valid = bool(validation_result[0])
                    error_message = validation_result[1]
                else:
                    is_valid = bool(validation_result)
                    error_message = None

                if not is_valid:
                    flash(str(error_message or "Invalid file"), "error")
                    return _render_index(
                        template_name,
                        form_state,
                        active_language,
                        results,
                        recent_analyses,
                    )
                content = load_document(uploaded_file)
            else:
                content = form_state["essay_text"]

            if not content or not content.strip():
                flash(messages["upload_or_paste_error"], "error")
                return _render_index(
                    template_name,
                    form_state,
                    active_language,
                    results,
                    recent_analyses,
                )

            analysis_package = run_learning_story_analysis(
                content,
                form_state,
                uploaded_filename,
            )
            results = analysis_package["results"]
            _cache_analysis_result(
                analysis_package["analysis_id"], analysis_package["cache_payload"]
            )
            _add_recent_analysis(analysis_package["recent_entry"])
            recent_analyses = _get_recent_analyses()
        except Exception as exc:
            flash(f"{messages['analysis_error_prefix']}: {exc}", "error")

    return _render_index(template_name, form_state, active_language, results, recent_analyses)


@app.route("/health")
def health() -> Any:
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=False)
