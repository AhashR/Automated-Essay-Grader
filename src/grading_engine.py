import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from src.language_utils import normalize_language


@dataclass
class GradingCriteria:
    """Rubric criterion metadata used during scoring."""

    name: str
    weight: float
    max_score: int
    description: str


class GradingEngine:
    """HvA-only grading engine for Learning Story submissions."""

    def __init__(
        self,
        rubric_type: str = "learning_story",
        analyzer=None,
        language: str = "en",
        quality_model=None,
    ):
        self.rubric_type = self._normalize_rubric_type(rubric_type)
        self.analyzer = analyzer
        self.language = normalize_language(language)
        self.quality_model = quality_model
        self.rubric, self.rubric_source, self.grade_scale = self._load_rubric(
            self.rubric_type
        )

    def _normalize_rubric_type(self, rubric_type: str) -> str:
        normalized = (rubric_type or "learning_story").strip().lower()
        aliases = {
            "learningstory": "learning_story",
            "learning_story_rubric": "learning_story",
        }
        return aliases.get(normalized, normalized)

    def _load_rubric(
        self, rubric_type: str
    ) -> tuple[Dict[str, GradingCriteria], str, Dict[str, Dict[str, float]]]:
        rubric_file = Path(__file__).resolve().parent.parent / "rubrics" / "learning_story.json"

        if rubric_type == "learning_story" and rubric_file.exists():
            with rubric_file.open("r", encoding="utf-8") as handle:
                data = json.load(handle)

            parsed = {}
            for key, value in data.get("criteria", {}).items():
                parsed[key] = GradingCriteria(
                    name=value.get("name", key.replace("_", " ").title()),
                    weight=float(value.get("weight", 0.25)),
                    max_score=int(value.get("max_score", 25)),
                    description=value.get("description", ""),
                )

            if parsed:
                return parsed, "file", data.get("grade_scale", {})

        fallback = {
            "context": GradingCriteria(
                name="Context & Understanding",
                weight=0.25,
                max_score=25,
                description="Clarity of context and understanding of required learning",
            ),
            "learning_goals": GradingCriteria(
                name="Learning Goals & Formulation",
                weight=0.25,
                max_score=25,
                description="Quality and clarity of learning goals",
            ),
            "learning_approach": GradingCriteria(
                name="Learning Approach & Concrete Actions",
                weight=0.25,
                max_score=25,
                description="Concrete learning steps and suitable resources",
            ),
            "substantiation": GradingCriteria(
                name="Substantiation & Evidence Quality",
                weight=0.25,
                max_score=25,
                description="Source documentation and evidence quality",
            ),
        }

        fallback_scale = {
            "A": {"min": 90.0, "max": 100.0},
            "B": {"min": 80.0, "max": 89.9},
            "C": {"min": 70.0, "max": 79.9},
            "D": {"min": 60.0, "max": 69.9},
            "F": {"min": 0.0, "max": 59.9},
        }
        return fallback, "builtin", fallback_scale

    def grade_essay(
        self,
        essay_text: str,
        analysis_results: Dict[str, Any],
        prompt: Optional[str] = None,
        language: Optional[str] = None,
    ) -> Dict[str, Any]:
        _ = prompt
        active_language = normalize_language(language or self.language)
        signals = analysis_results.get("learning_story_signals", {}) or {}

        criteria_scores = {
            "context": self._score_context(signals, self.rubric["context"]),
            "learning_goals": self._score_learning_goals(
                signals, self.rubric["learning_goals"]
            ),
            "learning_approach": self._score_learning_approach(
                signals, self.rubric["learning_approach"]
            ),
            "substantiation": self._score_substantiation(
                signals, self.rubric["substantiation"]
            ),
        }

        base_overall_score = self._calculate_overall_score(
            criteria_scores, signals, essay_text
        )
        quality_assessment = self._get_quality_assessment(essay_text)
        score_adjustment = self._compute_score_adjustment(quality_assessment)
        overall_score = min(100.0, max(0.0, base_overall_score + score_adjustment))
        letter_grade = self._get_letter_grade(overall_score)

        return {
            "overall_score": round(overall_score, 1),
            "base_overall_score": round(base_overall_score, 1),
            "score_adjustment": round(score_adjustment, 1),
            "letter_grade": letter_grade,
            "criteria_scores": {k: round(v, 1) for k, v in criteria_scores.items()},
            "content_score": criteria_scores.get("context", 0),
            "organization_score": criteria_scores.get("learning_goals", 0),
            "grammar_score": criteria_scores.get("learning_approach", 0),
            "style_score": criteria_scores.get("substantiation", 0),
            "detailed_feedback": self._generate_detailed_feedback(
                criteria_scores,
                quality_assessment,
                score_adjustment,
                language=active_language,
            ),
            "rubric_used": self.rubric_type,
            "rubric_source": self.rubric_source,
            "quality_assessment": quality_assessment,
            "language": active_language,
            "grading_breakdown": self._get_grading_breakdown(criteria_scores),
            "workspace_attribution": "HvA Feedback Agent",
        }

    def _get_quality_assessment(self, essay_text: str) -> Dict[str, Any]:
        if self.quality_model is None:
            return {
                "available": False,
                "label": None,
                "confidence": None,
                "reason": "quality_model_not_configured",
            }

        prediction = self.quality_model.predict(essay_text)
        prediction.setdefault("reason", "ok" if prediction.get("available") else "unavailable")
        return prediction

    def _compute_score_adjustment(self, quality_assessment: Dict[str, Any]) -> float:
        """Apply conservative classifier-based adjustment to improve score fidelity."""
        if not quality_assessment.get("available"):
            return 0.0

        good_probability = quality_assessment.get("good_probability")
        bad_probability = quality_assessment.get("bad_probability")
        confidence = quality_assessment.get("confidence")

        if not isinstance(good_probability, (int, float)):
            if not isinstance(confidence, (int, float)):
                return 0.0
            good_probability = float(confidence)

        if isinstance(bad_probability, (int, float)):
            bad_probability = float(bad_probability)
        else:
            bad_probability = None

        good_probability = float(good_probability)

        if bad_probability is not None and bad_probability >= 0.60:
            scaled = min(1.0, max(0.0, (bad_probability - 0.60) / 0.40))
            return -14.0 * scaled

        if good_probability >= 0.80:
            scaled = min(1.0, max(0.0, (good_probability - 0.80) / 0.20))
            return 8.0 * scaled

        if good_probability < 0.65:
            scaled = min(1.0, max(0.0, (0.65 - good_probability) / 0.65))
            return -8.0 * scaled

        if not isinstance(confidence, (int, float)):
            return 0.0

        scaled = min(1.0, max(0.0, (float(confidence) - 0.60) / 0.40))
        return 4.0 * scaled if quality_assessment.get("label") == "good" else -6.0 * scaled

    def _score_context(self, signals: Dict[str, Any], criterion: GradingCriteria) -> float:
        base = criterion.max_score * 0.10
        context_mentions = int(signals.get("context_mentions", 0))
        stakeholders = int(signals.get("stakeholder_mentions", 0))
        deliverables = int(signals.get("deliverable_mentions", 0))
        planning = int(signals.get("planning_mentions", 0))
        sections_detected = signals.get("sections_detected", {}) or {}

        if context_mentions == 0 and not sections_detected.get("context"):
            return min(base, criterion.max_score * 0.20)

        if context_mentions >= 4:
            base += criterion.max_score * 0.4
        elif context_mentions >= 2:
            base += criterion.max_score * 0.3
        elif context_mentions >= 1:
            base += criterion.max_score * 0.2

        if stakeholders >= 1:
            base += criterion.max_score * 0.1
        if deliverables >= 1:
            base += criterion.max_score * 0.15
        if planning >= 1:
            base += criterion.max_score * 0.1
        if sections_detected.get("context"):
            base += criterion.max_score * 0.08

        if context_mentions < 2 and not (stakeholders or deliverables or planning):
            base = min(base, criterion.max_score * 0.40)

        return min(base, criterion.max_score)

    def _score_learning_goals(
        self, signals: Dict[str, Any], criterion: GradingCriteria
    ) -> float:
        base = criterion.max_score * 0.10
        goals = int(signals.get("goal_statements", 0))
        success = int(signals.get("success_criteria_mentions", 0))
        sections_detected = signals.get("sections_detected", {}) or {}

        if goals == 0 and success == 0 and not sections_detected.get("learning_goals"):
            return min(base, criterion.max_score * 0.18)

        if goals >= 3:
            base += criterion.max_score * 0.4
        elif goals >= 1:
            base += criterion.max_score * 0.3

        if success >= 2:
            base += criterion.max_score * 0.25
        elif success >= 1:
            base += criterion.max_score * 0.15
        if sections_detected.get("learning_goals"):
            base += criterion.max_score * 0.08

        if goals < 2 and success == 0:
            base = min(base, criterion.max_score * 0.45)

        return min(base, criterion.max_score)

    def _score_learning_approach(
        self, signals: Dict[str, Any], criterion: GradingCriteria
    ) -> float:
        base = criterion.max_score * 0.10
        actions = int(signals.get("actions_count", 0))
        resources = int(signals.get("resource_mentions", 0))
        planning = int(signals.get("planning_mentions", 0))
        sections_detected = signals.get("sections_detected", {}) or {}

        if actions == 0 and resources == 0 and planning == 0 and not sections_detected.get(
            "learning_approach"
        ):
            return min(base, criterion.max_score * 0.16)

        if actions >= 5:
            base += criterion.max_score * 0.35
        elif actions >= 2:
            base += criterion.max_score * 0.25

        if resources >= 3:
            base += criterion.max_score * 0.25
        elif resources >= 1:
            base += criterion.max_score * 0.15

        if planning >= 1:
            base += criterion.max_score * 0.15
        if sections_detected.get("learning_approach"):
            base += criterion.max_score * 0.08

        if actions < 2 and resources < 1:
            base = min(base, criterion.max_score * 0.35)
        elif actions < 3 or resources < 2:
            base = min(base, criterion.max_score * 0.60)

        return min(base, criterion.max_score)

    def _score_substantiation(
        self, signals: Dict[str, Any], criterion: GradingCriteria
    ) -> float:
        base = criterion.max_score * 0.10
        evidence = int(signals.get("evidence_mentions", 0))
        links = int(signals.get("link_mentions", 0))
        resources = int(signals.get("resource_mentions", 0))
        reflection = int(signals.get("reflection_mentions", 0))
        sections_detected = signals.get("sections_detected", {}) or {}

        if evidence == 0 and links == 0 and resources == 0 and reflection == 0 and not sections_detected.get(
            "substantiation"
        ):
            return min(base, criterion.max_score * 0.16)

        if evidence >= 3:
            base += criterion.max_score * 0.35
        elif evidence >= 1:
            base += criterion.max_score * 0.25

        if links >= 1 or resources >= 2:
            base += criterion.max_score * 0.25
        elif resources >= 1:
            base += criterion.max_score * 0.15

        if reflection >= 1:
            base += criterion.max_score * 0.15
        if sections_detected.get("substantiation") or sections_detected.get("reflection"):
            base += criterion.max_score * 0.08

        if evidence < 1 and links == 0 and resources < 1:
            base = min(base, criterion.max_score * 0.35)
        elif evidence < 2 or resources < 2:
            base = min(base, criterion.max_score * 0.60)

        return min(base, criterion.max_score)

    def _calculate_overall_score(
        self,
        criteria_scores: Dict[str, float],
        signals: Dict[str, Any],
        essay_text: str,
    ) -> float:
        total_score = 0.0
        total_weight = 0.0

        for criterion_key, score in criteria_scores.items():
            criterion = self.rubric.get(criterion_key)
            if not criterion:
                continue
            total_score += score * criterion.weight
            total_weight += criterion.weight

        if total_weight == 0:
            return 0.0

        weighted_average = total_score / total_weight
        overall_score = (weighted_average / 25.0) * 100.0

        coverage_count = int(signals.get("section_coverage_count", 0))
        missing_sections = max(0, 4 - coverage_count)
        overall_score -= missing_sections * 4.0

        word_count = len([word for word in essay_text.split() if word.strip()])
        if word_count < 100:
            overall_score -= 4.0
        elif word_count < 150:
            overall_score -= 2.0

        return max(0.0, overall_score)

    def _get_letter_grade(self, overall_score: float) -> str:
        if self.grade_scale:
            for grade, bounds in self.grade_scale.items():
                minimum = float(bounds.get("min", 0.0))
                maximum = float(bounds.get("max", 100.0))
                if minimum <= overall_score <= maximum:
                    return grade
        return "F"

    def _generate_detailed_feedback(
        self,
        criteria_scores: Dict[str, float],
        quality_assessment: Optional[Dict[str, Any]] = None,
        score_adjustment: float = 0.0,
        language: str = "en",
    ) -> str:
        weakest = min(criteria_scores.items(), key=lambda item: item[1])[0]
        weakest_name = self.rubric[weakest].name
        quality_label = str((quality_assessment or {}).get("label") or "").lower()
        quality_confidence = (quality_assessment or {}).get("confidence")

        quality_line_en = ""
        quality_line_nl = ""
        if isinstance(quality_confidence, (int, float)) and quality_label in {"good", "bad"}:
            quality_line_en = (
                f" Learned pattern signal suggests '{quality_label}' quality "
                f"(confidence {quality_confidence:.2f}, score adjustment {score_adjustment:+.1f})."
            )
            quality_line_nl = (
                f" Geleerd patroon-signaal duidt op '{quality_label}' kwaliteit "
                f"(betrouwbaarheid {quality_confidence:.2f}, scoreaanpassing {score_adjustment:+.1f})."
            )

        if language == "nl":
            return (
                f"Focus in de volgende versie vooral op '{weakest_name}'. "
                "Voeg meer concrete voorbeelden, bronnen en bewijs toe zodat je "
                f"learning story sterker onderbouwd is.{quality_line_nl}"
            )

        return (
            f"Focus your next revision primarily on '{weakest_name}'. "
            "Add more concrete examples, sources, and evidence so your learning "
            f"story is better substantiated.{quality_line_en}"
        )

    def _get_grading_breakdown(
        self, criteria_scores: Dict[str, float]
    ) -> Dict[str, Any]:
        breakdown = {}

        for criterion_key, score in criteria_scores.items():
            if criterion_key not in self.rubric:
                continue

            criterion = self.rubric[criterion_key]
            percentage = (score / criterion.max_score) * 100.0 if criterion.max_score else 0.0

            breakdown[criterion_key] = {
                "name": criterion.name,
                "score": score,
                "max_score": criterion.max_score,
                "percentage": round(percentage, 1),
                "weight": criterion.weight,
                "description": criterion.description,
                "performance_level": self._get_performance_level(percentage),
            }

        return breakdown

    def _get_performance_level(self, percentage: float) -> str:
        if percentage >= 90:
            return "Excellent"
        if percentage >= 80:
            return "Proficient"
        if percentage >= 70:
            return "Developing"
        if percentage >= 60:
            return "Beginning"
        return "Below Basic"
