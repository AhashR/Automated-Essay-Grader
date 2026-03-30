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


def test_nederlands_agent_language_localizes_ui_feedback_sections():
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
    assert "**Goede lengte**" in feedback["strengths"]
    assert "**Good Length**" not in feedback["strengths"]
    assert "**Onderbouw met bewijs**" in feedback["suggestions"]
    assert "**Support with Evidence**" not in feedback["suggestions"]
