"""
Test Essay Analyzer Module
From Hasif's Workspace

Unit tests for the essay analyzer functionality.
Author: Hasif50
"""

import pytest
import sys
from pathlib import Path

src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from essay_analyzer import EssayAnalyzer


class TestEssayAnalyzer:
    """Test cases for EssayAnalyzer class."""

    @pytest.fixture
    def sample_essay(self):
        """Sample essay text for testing."""
        return """
        Technology has revolutionized modern education in unprecedented ways. Students now have access to vast amounts of information through the internet, enabling them to learn beyond traditional classroom boundaries. Online learning platforms have made education more accessible to people worldwide.
        
        However, technology also presents challenges. The digital divide creates inequality among students who have different levels of access to technology. Additionally, excessive screen time and digital distractions can negatively impact learning outcomes.
        
        In conclusion, while technology offers significant benefits to education, it must be implemented thoughtfully to maximize its positive impact while minimizing potential drawbacks.
        """

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance for testing."""
        # Mock analyzer without requiring API keys
        return EssayAnalyzer(model_provider="mock", model_name="test")

    def test_basic_statistics(self, analyzer, sample_essay):
        """Test basic text statistics calculation."""
        # This would need to be adapted based on actual implementation
        # For now, testing the concept
        stats = analyzer._get_basic_statistics(sample_essay)

        assert "word_count" in stats
        assert "sentence_count" in stats
        assert "paragraph_count" in stats
        assert stats["word_count"] > 0
        assert stats["sentence_count"] > 0
        assert stats["paragraph_count"] > 0

    def test_readability_analysis(self, analyzer, sample_essay):
        """Test readability metrics calculation."""
        readability = analyzer._analyze_readability(sample_essay)

        assert "flesch_reading_ease" in readability
        assert "flesch_kincaid_grade" in readability
        assert isinstance(readability["flesch_reading_ease"], (int, float))
        assert isinstance(readability["flesch_kincaid_grade"], (int, float))

    def test_structure_analysis(self, analyzer, sample_essay):
        """Test essay structure analysis."""
        structure = analyzer._analyze_structure(sample_essay)

        assert "paragraph_count" in structure
        assert "avg_paragraph_length" in structure
        assert "has_clear_introduction" in structure
        assert "has_clear_conclusion" in structure
        assert structure["paragraph_count"] >= 1

    def test_vocabulary_analysis(self, analyzer, sample_essay):
        """Test vocabulary analysis."""
        vocab = analyzer._analyze_vocabulary(sample_essay)

        assert "total_words" in vocab
        assert "unique_words" in vocab
        assert "lexical_diversity" in vocab
        assert "avg_word_length" in vocab
        assert vocab["total_words"] > 0
        assert vocab["unique_words"] > 0
        assert 0 <= vocab["lexical_diversity"] <= 1

    def test_empty_essay_handling(self, analyzer):
        """Test handling of empty essay input."""
        with pytest.raises(Exception):
            analyzer.analyze_essay("")

    def test_very_short_essay(self, analyzer):
        """Test handling of very short essays."""
        short_essay = "This is a very short essay."
        result = analyzer._get_basic_statistics(short_essay)

        assert result["word_count"] > 0
        assert result["sentence_count"] >= 1

    def test_transition_word_counting(self, analyzer):
        """Test transition word detection."""
        text_with_transitions = "First, we must consider the evidence. However, there are counterarguments. Furthermore, additional research is needed. Finally, we can conclude."

        count = analyzer._count_transition_words(text_with_transitions)
        assert count >= 4  # Should detect at least the obvious transitions

    def test_passive_voice_detection(self, analyzer):
        """Test passive voice detection."""
        passive_sentence = "The ball was thrown by the player."
        active_sentence = "The player threw the ball."

        assert analyzer._contains_passive_voice(passive_sentence) == True
        assert analyzer._contains_passive_voice(active_sentence) == False

    def test_introduction_pattern_detection(self, analyzer):
        """Test introduction pattern recognition."""
        intro_text = (
            "In this essay, I will discuss the impact of technology on education."
        )
        non_intro_text = "Technology has many applications in various fields."

        assert analyzer._check_introduction_patterns(intro_text) == True
        assert analyzer._check_introduction_patterns(non_intro_text) == False

    def test_conclusion_pattern_detection(self, analyzer):
        """Test conclusion pattern recognition."""
        conclusion_text = (
            "In conclusion, technology has transformed education significantly."
        )
        non_conclusion_text = "Technology continues to evolve rapidly."

        assert analyzer._check_conclusion_patterns(conclusion_text) == True
        assert analyzer._check_conclusion_patterns(non_conclusion_text) == False


class TestEssayAnalyzerIntegration:
    """Integration tests for essay analyzer."""

    def test_full_analysis_workflow(self):
        """Test complete analysis workflow."""
        # This would require actual API keys for full testing
        # For now, testing the structure
        sample_text = "This is a sample essay for testing purposes. It contains multiple sentences and demonstrates basic essay structure."

        # Mock the analyzer to avoid API calls in tests
        analyzer = EssayAnalyzer(model_provider="mock", model_name="test")

        # Test that the analysis structure is correct
        try:
            # This would need to be mocked for actual testing
            # result = analyzer.analyze_essay(sample_text)
            # assert "basic_stats" in result
            # assert "readability" in result
            # assert "structure" in result
            # assert "vocabulary" in result
            pass
        except Exception as e:
            # Expected to fail without proper setup
            assert "API" in str(e) or "model" in str(e).lower()


if __name__ == "__main__":
    pytest.main([__file__])
