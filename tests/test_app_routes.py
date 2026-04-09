import app as app_module


def _fake_analysis_payload():
    return {
        "analysis_id": "abc123def456",
        "results": {
            "quick_stats": {
                "word_count": 12,
                "character_count": 80,
                "paragraph_count": 1,
                "reading_time": 1,
            },
            "overall_score": 82.5,
            "base_overall_score": 80.0,
            "score_adjustment": 2.5,
            "letter_grade": "B",
            "breakdown": [
                {
                    "name": "Context & Understanding",
                    "score": 20,
                    "weight": 0.25,
                },
                {
                    "name": "Learning Goals & Formulation",
                    "score": 18,
                    "weight": 0.25,
                },
            ],
            "feedback": {
                "language": "en",
                "ai_comprehensive_feedback": "ok",
            },
            "detected_language": "English",
            "feedback_language": "English",
            "grammar_issues": [],
            "quality_assessment": {
                "available": False,
                "label": None,
                "confidence": None,
                "reason": "quality_model_not_configured",
            },
            "ai_feedback": "ok",
            "rubric_source": "file",
        },
        "cache_payload": {
            "results": {},
            "form_state": {},
        },
        "recent_entry": {
            "id": "abc123def456",
            "subject": "Test",
            "prompted_at": "2026-04-09 12:00",
            "overall_score": "8.3/10",
            "word_count": 12,
            "letter_grade": "B",
        },
    }


def test_health_route_returns_ok():
    app_module.app.config["TESTING"] = True
    client = app_module.app.test_client()

    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_index_get_renders():
    app_module.app.config["TESTING"] = True
    client = app_module.app.test_client()

    response = client.get("/")

    assert response.status_code == 200


def test_index_post_renders_with_stubbed_analysis(monkeypatch):
    app_module.app.config["TESTING"] = True
    client = app_module.app.test_client()

    monkeypatch.setattr(
        app_module,
        "run_learning_story_analysis",
        lambda content, form_state, uploaded_filename="": _fake_analysis_payload(),
    )

    response = client.post(
        "/",
        data={
            "essay_text": "Test learning story",
            "model_provider": "gemini",
            "model_name": "gemini-2.5-flash",
            "feedback_agent_language": "en",
        },
    )

    assert response.status_code == 200
