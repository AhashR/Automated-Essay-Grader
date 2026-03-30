"""Flask application entry point for Automated Essay Grader."""

import os
import re
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)
from markupsafe import Markup, escape

# Add src directory to path
sys.path.append(str(Path(__file__).parent / "src"))

from essay_analyzer import EssayAnalyzer
from feedback_generator import FeedbackGenerator
from grading_engine import GradingEngine
from utils import generate_report, load_document, save_results, validate_file


load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "change-me-in-production")
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

MODEL_OPTIONS = {
    "openai": ["gpt-4", "gpt-3.5-turbo"],
    "azure_openai": ["gpt-4", "gpt-35-turbo"],
}

MODEL_PROVIDER_LABELS = {
    "openai": "OpenAI",
    "azure_openai": "Azure OpenAI",
}

LANGUAGE_LABELS = {
    "en": "English",
    "nl": "Nederlands",
}

RUBRIC_TYPE = "learning_story"
RUBRIC_LABEL = "Learning Story"

# In-memory cache for report export actions.
ANALYSIS_CACHE: Dict[str, Dict[str, Any]] = {}


def _default_form_state() -> Dict[str, Any]:
    return {
        "model_provider": "openai",
        "model_name": "gpt-4",
        "temperature": 0.3,
        "max_tokens": 2000,
        "feedback_agent_language": "en",
        "enable_grammar": True,
        "enable_style": True,
        "enable_plagiarism": False,
        "enable_sentiment": True,
        "essay_text": "",
        "essay_prompt": "",
    }


def _to_bool(value: Optional[str]) -> bool:
    return str(value).lower() in {"1", "true", "on", "yes"}


def _model_options_for(provider: str) -> list[str]:
    return MODEL_OPTIONS.get(provider, MODEL_OPTIONS["openai"])


def _render_feedback_markdown(text: str) -> Markup:
    if not text:
        return Markup("")

    escaped = escape(text)
    escaped = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", str(escaped))
    escaped = escaped.replace("\n", "<br>")
    return Markup(escaped)


@app.template_filter("render_feedback")
def render_feedback(text: str) -> Markup:
    return _render_feedback_markdown(text)


def _cache_analysis(payload: Dict[str, Any]) -> None:
    cache_id = uuid.uuid4().hex
    ANALYSIS_CACHE[cache_id] = payload
    session["analysis_id"] = cache_id


def _get_cached_analysis() -> Optional[Dict[str, Any]]:
    analysis_id = session.get("analysis_id")
    if not analysis_id:
        return None
    return ANALYSIS_CACHE.get(analysis_id)


@app.route("/", methods=["GET", "POST"])
def index():
    form_state = _default_form_state()
    results = None

    if request.method == "POST":
        form_state["model_provider"] = request.form.get("model_provider", "openai")
        form_state["model_name"] = request.form.get("model_name", "gpt-4")
        form_state["temperature"] = float(request.form.get("temperature", 0.3))
        form_state["max_tokens"] = int(request.form.get("max_tokens", 2000))
        form_state["feedback_agent_language"] = request.form.get(
            "feedback_agent_language", "en"
        )
        form_state["enable_grammar"] = _to_bool(request.form.get("enable_grammar"))
        form_state["enable_style"] = _to_bool(request.form.get("enable_style"))
        form_state["enable_plagiarism"] = _to_bool(
            request.form.get("enable_plagiarism")
        )
        form_state["enable_sentiment"] = _to_bool(
            request.form.get("enable_sentiment")
        )
        form_state["essay_text"] = request.form.get("essay_text", "")
        form_state["essay_prompt"] = request.form.get("essay_prompt", "")

        model_choices = _model_options_for(form_state["model_provider"])
        if form_state["model_name"] not in model_choices:
            form_state["model_name"] = model_choices[0]

        uploaded_file = request.files.get("essay_file")
        content = ""

        try:
            if uploaded_file and uploaded_file.filename:
                is_valid, error_message = validate_file(uploaded_file, return_error=True)
                if not is_valid:
                    flash(error_message, "error")
                    return render_template(
                        "index.html",
                        form_state=form_state,
                        model_options=model_choices,
                        model_provider_labels=MODEL_PROVIDER_LABELS,
                        language_labels=LANGUAGE_LABELS,
                        rubric_label=RUBRIC_LABEL,
                        results=results,
                    )
                content = load_document(uploaded_file)
            else:
                content = form_state["essay_text"]

            if not content or not content.strip():
                flash("Please upload a file or paste essay content to analyze.", "error")
                return render_template(
                    "index.html",
                    form_state=form_state,
                    model_options=model_choices,
                    model_provider_labels=MODEL_PROVIDER_LABELS,
                    language_labels=LANGUAGE_LABELS,
                    rubric_label=RUBRIC_LABEL,
                    results=results,
                )

            analyzer = EssayAnalyzer(
                model_provider=form_state["model_provider"],
                model_name=form_state["model_name"],
                temperature=form_state["temperature"],
                max_tokens=form_state["max_tokens"],
            )

            grading_engine = GradingEngine(
                rubric_type=RUBRIC_TYPE,
                analyzer=analyzer,
                language="en",
            )

            feedback_generator = FeedbackGenerator(analyzer=analyzer, language="en")

            analysis_results = analyzer.analyze_essay(
                content,
                prompt=form_state["essay_prompt"],
                enable_grammar=form_state["enable_grammar"],
                enable_style=form_state["enable_style"],
                enable_plagiarism=form_state["enable_plagiarism"],
                enable_sentiment=form_state["enable_sentiment"],
            )

            grade_results = grading_engine.grade_essay(
                content,
                analysis_results,
                prompt=form_state["essay_prompt"],
                language=form_state["feedback_agent_language"],
            )

            feedback = feedback_generator.generate_feedback(
                content,
                analysis_results,
                grade_results,
                prompt=form_state["essay_prompt"],
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
            grammar_issues = analysis_results.get("grammar", {}).get("grammar_issues", [])

            results = {
                "quick_stats": quick_stats,
                "overall_score": grade_results.get("overall_score", 0),
                "letter_grade": grade_results.get("letter_grade", "N/A"),
                "breakdown": breakdown_values,
                "feedback": feedback,
                "detected_language": LANGUAGE_LABELS.get(
                    analysis_results.get("language", "en"), "English"
                ),
                "feedback_language": LANGUAGE_LABELS.get(
                    feedback.get("language", "en"), "English"
                ),
                "grammar_issues": grammar_issues,
            }

            _cache_analysis(
                {
                    "content": content,
                    "analysis_results": analysis_results,
                    "grade_results": grade_results,
                    "feedback": feedback,
                }
            )
        except Exception as exc:
            flash(f"Error during analysis: {exc}", "error")

    return render_template(
        "index.html",
        form_state=form_state,
        model_options=_model_options_for(form_state["model_provider"]),
        model_provider_labels=MODEL_PROVIDER_LABELS,
        language_labels=LANGUAGE_LABELS,
        rubric_label=RUBRIC_LABEL,
        results=results,
    )


@app.route("/export/pdf")
def export_pdf():
    cached = _get_cached_analysis()
    if not cached:
        flash("No analysis results found. Run an analysis first.", "error")
        return redirect(url_for("index"))

    report_path = generate_report(
        cached["content"],
        cached["analysis_results"],
        cached["grade_results"],
        cached["feedback"],
        format="pdf",
    )

    return send_file(report_path, as_attachment=True, download_name=Path(report_path).name)


@app.route("/export/csv")
def export_csv():
    cached = _get_cached_analysis()
    if not cached:
        flash("No analysis results found. Run an analysis first.", "error")
        return redirect(url_for("index"))

    csv_path = save_results(
        cached["analysis_results"],
        cached["grade_results"],
        cached["feedback"],
        format="csv",
    )

    return send_file(csv_path, as_attachment=True, download_name=Path(csv_path).name)


@app.route("/health")
def health() -> Any:
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=False)
