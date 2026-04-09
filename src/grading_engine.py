import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional


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
        self.language = self._normalize_language(language)
        self.quality_model = quality_model
        self.rubric, self.rubric_source, self.grade_scale = self._load_rubric(
            self.rubric_type
        )

    def _normalize_language(self, language: str) -> str:
        normalized = (language or "en").strip().lower()
        aliases = {"english": "en", "dutch": "nl", "nederlands": "nl"}
        normalized = aliases.get(normalized, normalized)
        return normalized if normalized in {"en", "nl"} else "en"

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
        active_language = self._normalize_language(language or self.language)
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

        base_overall_score = self._calculate_overall_score(criteria_scores)
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

        label = str(quality_assessment.get("label") or "").lower()
        confidence = quality_assessment.get("confidence")

        if not isinstance(confidence, (int, float)):
            return 0.0

        if confidence < 0.60:
            return 0.0

        # Scale from [0.60, 1.00] to [0.0, 1.0] to reduce unstable low-confidence impact.
        scaled = min(1.0, max(0.0, (float(confidence) - 0.60) / 0.40))

        if label == "good":
            return 8.0 * scaled
        if label == "bad":
            return -12.0 * scaled
        return 0.0

    def _score_context(self, signals: Dict[str, Any], criterion: GradingCriteria) -> float:
        base = criterion.max_score * 0.25
        context_mentions = int(signals.get("context_mentions", 0))
        stakeholders = int(signals.get("stakeholder_mentions", 0))
        deliverables = int(signals.get("deliverable_mentions", 0))
        planning = int(signals.get("planning_mentions", 0))

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

        return min(base, criterion.max_score)

    def _score_learning_goals(
        self, signals: Dict[str, Any], criterion: GradingCriteria
    ) -> float:
        base = criterion.max_score * 0.25
        goals = int(signals.get("goal_statements", 0))
        success = int(signals.get("success_criteria_mentions", 0))

        if goals >= 3:
            base += criterion.max_score * 0.4
        elif goals >= 1:
            base += criterion.max_score * 0.3

        if success >= 2:
            base += criterion.max_score * 0.25
        elif success >= 1:
            base += criterion.max_score * 0.15

        return min(base, criterion.max_score)

    def _score_learning_approach(
        self, signals: Dict[str, Any], criterion: GradingCriteria
    ) -> float:
        base = criterion.max_score * 0.25
        actions = int(signals.get("actions_count", 0))
        resources = int(signals.get("resource_mentions", 0))
        planning = int(signals.get("planning_mentions", 0))

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

        return min(base, criterion.max_score)

    def _score_substantiation(
        self, signals: Dict[str, Any], criterion: GradingCriteria
    ) -> float:
        base = criterion.max_score * 0.25
        evidence = int(signals.get("evidence_mentions", 0))
        links = int(signals.get("link_mentions", 0))
        resources = int(signals.get("resource_mentions", 0))
        reflection = int(signals.get("reflection_mentions", 0))

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

        return min(base, criterion.max_score)

    def _calculate_overall_score(self, criteria_scores: Dict[str, float]) -> float:
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
        return (weighted_average / 25.0) * 100.0

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
