from pathlib import Path

from src.essay_analyzer import EssayAnalyzer
from src.grading_engine import GradingEngine
from src.feedback_generator import FeedbackGenerator
from src.retrieval import LearningStoryRetriever


class _FakeResponse:
	def __init__(self, content: str) -> None:
		self.content = content


class _CapturingAnalyzer:
	def __init__(self) -> None:
		self.model_provider = "mock"
		self.model_name = "mock-model"
		self.captured_messages = []

	def run_chat(self, messages, temperature=None, max_tokens=None):
		_ = (temperature, max_tokens)
		self.captured_messages.append(messages)
		return _FakeResponse("Generated feedback")


def test_structure_signals_detect_all_core_sections_en() -> None:
	analyzer = EssayAnalyzer(model_provider="mock", language="en", retriever=None)
	text = """
	Context & ambition
	I am building a portfolio dashboard for my team and client.

	Learning goals
	As a student I want to learn data validation patterns so that I can prevent broken dashboards.

	Approach and experiments
	I will research docs, build a prototype, test with peers, and iterate weekly.

	Sources and evidence
	Sources include HvA knowledge base and official docs. Evidence includes demo links and reflection.

	Reflection
	What went well and what could be better are summarized in my sprint logbook.
	"""

	analysis = analyzer.analyze_essay(text, language="en")
	signals = analysis["learning_story_signals"]

	assert signals["section_coverage_count"] >= 4
	assert signals["sections_detected"]["context"] is True
	assert signals["sections_detected"]["learning_goals"] is True
	assert signals["sections_detected"]["learning_approach"] is True
	assert signals["sections_detected"]["substantiation"] is True


def test_structure_signals_detect_all_core_sections_nl() -> None:
	analyzer = EssayAnalyzer(model_provider="mock", language="nl", retriever=None)
	text = """
	Context en ambitie
	In dit project lever ik een prototype op voor de opdrachtgever.

	Leerdoelen
	Als student wil ik leren testautomatisering zodat ik betrouwbaardere opleveringen maak.

	Aanpak
	Ik plan experimenten, bouw een eerste versie, vraag feedback en verbeter in de volgende sprint.

	Onderbouwing en bewijs
	Bronnen zijn de HvA kennisbank en documentatie. Bewijs bestaat uit testresultaten en reflectie.
	"""

	analysis = analyzer.analyze_essay(text, language="nl")
	signals = analysis["learning_story_signals"]

	assert signals["section_coverage_count"] >= 4
	assert signals["sections_detected"]["context"] is True
	assert signals["sections_detected"]["learning_goals"] is True
	assert signals["sections_detected"]["learning_approach"] is True
	assert signals["sections_detected"]["substantiation"] is True


def test_retrieval_prefers_matching_query_language(tmp_path: Path) -> None:
	english_dir = tmp_path / "good"
	dutch_dir = tmp_path / "bad"
	english_dir.mkdir(parents=True, exist_ok=True)
	dutch_dir.mkdir(parents=True, exist_ok=True)

	(english_dir / "english.md").write_text(
		"Context learning goals approach evidence with team and deliverable.",
		encoding="utf-8",
	)
	(dutch_dir / "nederlands.md").write_text(
		"Context leerdoelen aanpak onderbouwing met bronnen en bewijs.",
		encoding="utf-8",
	)

	retriever = LearningStoryRetriever(data_path=tmp_path, top_k=1, min_score=0.01)
	hits = retriever.search(
		"Ik wil leren en mijn aanpak met bronnen onderbouwen",
		top_k=1,
		language="nl",
	)

	assert hits
	assert hits[0].get("language") == "nl"


def test_feedback_prompt_uses_english_goal_template_only() -> None:
	fake_analyzer = _CapturingAnalyzer()
	generator = FeedbackGenerator(analyzer=fake_analyzer, language="en")

	result = generator.generate_feedback(
		essay_text="Short learning story content.",
		analysis_results={"learning_story_signals": {}, "retrieval_context": {}},
		grade_results={"rubric_used": "learning_story", "quality_assessment": {}},
		language="en",
	)

	assert "Generated feedback" in result["ai_comprehensive_feedback"]
	assert fake_analyzer.captured_messages

	system_content = fake_analyzer.captured_messages[0][0].content
	assert "As a student, I want to learn" in system_content
	assert "Als student wil ik leren" not in system_content


def test_grading_engine_penalizes_sparse_learning_story() -> None:
	engine = GradingEngine(language="en", quality_model=None)
	weak_signals = {
		"goal_statements": 0,
		"success_criteria_mentions": 0,
		"context_mentions": 1,
		"stakeholder_mentions": 0,
		"deliverable_mentions": 0,
		"actions_count": 1,
		"resource_mentions": 0,
		"evidence_mentions": 0,
		"reflection_mentions": 0,
		"planning_mentions": 0,
		"link_mentions": 0,
		"section_coverage_count": 1,
		"sections_detected": {
			"context": True,
			"learning_goals": False,
			"learning_approach": False,
			"substantiation": False,
		},
	}

	result = engine.grade_essay(
		essay_text="I am working on a task and will try something later.",
		analysis_results={"learning_story_signals": weak_signals, "retrieval_context": {}},
	)

	assert result["base_overall_score"] < 30.0
	assert result["overall_score"] < 30.0
