"""
Language support tests for English and Dutch behavior.
"""

from src.essay_analyzer import EssayAnalyzer
from src.feedback_generator import FeedbackGenerator
from src.grading_engine import GradingEngine


def test_language_normalization_across_components():
    analyzer = EssayAnalyzer.__new__(EssayAnalyzer)
    feedback = FeedbackGenerator(analyzer=None)
    engine = GradingEngine(rubric_type="standard", analyzer=None, language="nederlands")

    assert analyzer._normalize_language("English") == "en"
    assert analyzer._normalize_language("Nederlands") == "nl"
    assert feedback._normalize_language("dutch") == "nl"
    assert engine.language == "nl"


def test_dutch_introduction_and_conclusion_patterns():
    analyzer = EssayAnalyzer.__new__(EssayAnalyzer)

    intro = "In dit essay zal ik bespreken hoe technologie het onderwijs verbetert."
    conclusion = "Tot slot kunnen we concluderen dat technologie waardevol is."

    assert analyzer._check_introduction_patterns(intro, "nl") is True
    assert analyzer._check_conclusion_patterns(conclusion, "nl") is True


def test_dutch_transition_word_counting():
    analyzer = EssayAnalyzer.__new__(EssayAnalyzer)

    text = "Ten eerste bekijken we de context. Daarnaast gebruiken we voorbeelden. Daarom is de aanpak effectief."

    count = analyzer._count_transition_words(text, "nl")
    assert count >= 3


def test_language_detection_english_and_dutch_text():
    analyzer = EssayAnalyzer.__new__(EssayAnalyzer)
    analyzer.english_stopwords = {
        "the",
        "and",
        "because",
        "this",
        "that",
        "is",
        "in",
    }
    analyzer.dutch_stopwords = {
        "de",
        "het",
        "een",
        "omdat",
        "dit",
        "dat",
        "is",
        "in",
    }

    english_text = "This learning story explains the context and the goal because this is important."
    dutch_text = "Dit leerverhaal beschrijft de context en het doel omdat dit belangrijk is."

    assert analyzer._detect_language(english_text) == "en"
    assert analyzer._detect_language(dutch_text) == "nl"


def test_feedback_language_does_not_change_scores():
    engine = GradingEngine(rubric_type="learning_story", analyzer=None)

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

    en_result = engine.grade_essay(
        essay_text="As a student, I want to learn API authentication and test strategies.",
        analysis_results=analysis_results,
        language="en",
    )
    nl_result = engine.grade_essay(
        essay_text="As a student, I want to learn API authentication and test strategies.",
        analysis_results=analysis_results,
        language="nl",
    )

    assert en_result["overall_score"] == nl_result["overall_score"]
    assert en_result["criteria_scores"] == nl_result["criteria_scores"]


def test_nederlands_agent_language_keeps_remaining_feedback_fields():
    generator = FeedbackGenerator(analyzer=None)

    analysis_results = {
        "basic_stats": {"word_count": 320},
        "vocabulary": {"lexical_diversity": 0.45, "complex_word_ratio": 0.08},
        "structure": {
            "has_clear_introduction": False,
            "has_clear_conclusion": False,
            "paragraph_count": 2,
            "transition_word_count": 1,
        },
        "grammar": {"issue_count": 7, "grammar_issues": []},
        "readability": {"flesch_reading_ease": 25, "flesch_kincaid_grade": 11},
        "style": {
            "sentence_variety_score": 6,
            "sentence_starter_variety": 0.4,
            "style_issues": [{"type": "Overused Word"}],
        },
    }
    grade_results = {"overall_score": 65}

    feedback = generator.generate_feedback(
        essay_text="Dit is een voorbeeld leerverhaal.",
        analysis_results=analysis_results,
        grade_results=grade_results,
        language="nl",
    )

    assert feedback["language"] == "nl"
    assert "strengths" not in feedback
    assert "improvements" not in feedback
    assert "suggestions" not in feedback
    assert "grammar_feedback" in feedback
    assert "style_feedback" in feedback
    assert "structure_feedback" in feedback


def test_english_agent_language_has_no_dutch_phrase_templates_in_ui_feedback_sections():
    generator = FeedbackGenerator(analyzer=None)

    analysis_results = {
        "learning_story_signals": {
            "context_mentions": 2,
            "goal_statements": 1,
            "actions_count": 1,
            "resource_mentions": 1,
            "evidence_mentions": 0,
            "reflection_mentions": 0,
            "link_mentions": 0,
        },
        "basic_stats": {"word_count": 300},
        "vocabulary": {"lexical_diversity": 0.5, "complex_word_ratio": 0.1},
        "structure": {
            "has_clear_introduction": True,
            "has_clear_conclusion": False,
            "paragraph_count": 3,
            "transition_word_count": 2,
        },
        "grammar": {"issue_count": 2, "grammar_issues": []},
        "readability": {"flesch_reading_ease": 55, "flesch_kincaid_grade": 9},
        "style": {"sentence_variety_score": 8, "sentence_starter_variety": 0.6, "style_issues": []},
    }

    grade_results = {
        "rubric_used": "learning_story",
        "criteria_scores": {"context": 15, "learning_goals": 15, "learning_approach": 15},
        "overall_score": 70,
    }

    feedback = generator.generate_feedback(
        essay_text="Test learning story",
        analysis_results=analysis_results,
        grade_results=grade_results,
        language="en",
    )

    assert "strengths" not in feedback
    assert "improvements" not in feedback
    assert "suggestions" not in feedback
    assert feedback["language"] == "en"


def test_judge_output_candidate_label_resolves_to_candidate_text():
    generator = FeedbackGenerator(analyzer=None)

    candidates = [
        "First complete feedback",
        "Second complete feedback",
        "Third complete feedback",
    ]

    assert generator._resolve_judge_selection("Candidate 1", candidates) == candidates[0]
    assert generator._resolve_judge_selection("Candidate 2:\nSecond complete feedback", candidates) == candidates[1]
    assert generator._resolve_judge_selection("Candidate 3", candidates) == candidates[2]
