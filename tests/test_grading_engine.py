"""
Test Grading Engine Module
From Hasif's Workspace

Unit tests for rubric loading and rubric-specific grading behavior.
"""

from src.grading_engine import GradingEngine


def test_learning_story_rubric_normalization_and_loading():
    """Learning Story UI label should resolve to the learning_story rubric."""
    engine = GradingEngine(rubric_type="Learning Story")

    assert engine.rubric_type == "learning_story"
    assert "context" in engine.rubric
    assert "learning_goals" in engine.rubric
    assert "content" not in engine.rubric


def test_learning_story_grading_uses_learning_story_criteria():
    """Grading output should reflect learning_story rubric criteria in breakdown."""
    engine = GradingEngine(rubric_type="learning_story")

    analysis_results = {
        "basic_stats": {"word_count": 320},
        "vocabulary": {"lexical_diversity": 0.58, "complex_word_ratio": 0.12},
        "structure": {
            "has_clear_introduction": True,
            "has_clear_conclusion": True,
            "paragraph_count": 4,
            "transition_word_count": 4,
        },
        "grammar": {"issue_count": 4},
        "readability": {"flesch_reading_ease": 62},
        "style": {"sentence_variety_score": 9, "sentence_starter_variety": 0.65},
    }

    result = engine.grade_essay(
        essay_text="As a student, I want to learn API authentication and test strategies.",
        analysis_results=analysis_results,
    )

    assert result["rubric_used"] == "learning_story"
    assert "context" in result["grading_breakdown"]
    assert "learning_goals" in result["grading_breakdown"]
    assert "content" not in result["grading_breakdown"]
