"""
Grading Engine Module
From Hasif's Workspace

AI-powered essay grading system with customizable rubrics.
Author: Hasif50
"""

import json
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path
from langchain_core.messages import HumanMessage, SystemMessage


@dataclass
class GradingCriteria:
    """Data class for grading criteria."""

    name: str
    weight: float
    max_score: int
    description: str


@dataclass
class GradeResult:
    """Data class for grade results."""

    overall_score: float
    letter_grade: str
    criteria_scores: Dict[str, float]
    feedback: str
    rubric_used: str


class GradingEngine:
    """
    Main grading engine that evaluates essays based on customizable rubrics.
    From Hasif's Workspace - Built for comprehensive essay evaluation.
    """

    def __init__(self, rubric_type: str = "standard", analyzer=None, language: str = "en"):
        """
        Initialize the grading engine.

        Args:
            rubric_type: Type of rubric to use for grading
            analyzer: EssayAnalyzer instance for AI capabilities
            language: Language code used in generated grading feedback
        """
        self.rubric_type = self._normalize_rubric_type(rubric_type)
        self.analyzer = analyzer
        self.language = self._normalize_language(language)
        self.rubric = self._load_rubric(self.rubric_type)

    def _normalize_language(self, language: str) -> str:
        """Normalize language inputs to supported codes."""
        normalized = (language or "en").strip().lower()
        aliases = {"english": "en", "dutch": "nl", "nederlands": "nl"}
        normalized = aliases.get(normalized, normalized)
        return normalized if normalized in {"en", "nl"} else "en"

    def _normalize_rubric_type(self, rubric_type: str) -> str:
        """Normalize rubric keys so UI labels and aliases map consistently."""
        normalized = (rubric_type or "standard").strip().lower().replace("-", "_")
        normalized = normalized.replace(" ", "_")

        aliases = {
            "learningstory": "learning_story",
            "learning_story_rubric": "learning_story",
            "creative": "creative_writing",
            "creativewriting": "creative_writing",
        }

        return aliases.get(normalized, normalized)

    def _load_rubric_from_file(self, rubric_type: str) -> Optional[Dict[str, GradingCriteria]]:
        """Load rubric definitions from JSON files in data/rubrics when available."""
        rubrics_dir = Path(__file__).resolve().parent.parent / "data" / "rubrics"
        candidate_files = [
            rubrics_dir / f"{rubric_type}.json",
            rubrics_dir / f"{rubric_type}_rubric.json",
        ]

        for rubric_file in candidate_files:
            if not rubric_file.exists():
                continue

            try:
                with rubric_file.open("r", encoding="utf-8") as f:
                    rubric_data = json.load(f)

                criteria = rubric_data.get("criteria", {})
                parsed_criteria = {}
                for key, value in criteria.items():
                    parsed_criteria[key] = GradingCriteria(
                        name=value.get("name", key.replace("_", " ").title()),
                        weight=float(value.get("weight", 0.25)),
                        max_score=int(value.get("max_score", 25)),
                        description=value.get("description", "No description provided"),
                    )

                if parsed_criteria:
                    return parsed_criteria
            except (OSError, json.JSONDecodeError, TypeError, ValueError):
                # Fall back to built-in rubric definitions if file is invalid.
                continue

        return None

    def _load_rubric(self, rubric_type: str) -> Dict[str, GradingCriteria]:
        """Load grading rubric based on type."""
        file_rubric = self._load_rubric_from_file(rubric_type)
        if file_rubric:
            return file_rubric

        rubrics = {
            "standard": {
                "content": GradingCriteria(
                    name="Content & Ideas",
                    weight=0.35,
                    max_score=25,
                    description="Quality of ideas, depth of analysis, and relevance to topic",
                ),
                "organization": GradingCriteria(
                    name="Organization & Structure",
                    weight=0.25,
                    max_score=25,
                    description="Logical flow, paragraph structure, and overall organization",
                ),
                "grammar": GradingCriteria(
                    name="Grammar & Mechanics",
                    weight=0.20,
                    max_score=25,
                    description="Grammar, spelling, punctuation, and sentence structure",
                ),
                "style": GradingCriteria(
                    name="Style & Voice",
                    weight=0.20,
                    max_score=25,
                    description="Writing style, voice, word choice, and clarity",
                ),
            },
            "academic": {
                "thesis": GradingCriteria(
                    name="Thesis & Argument",
                    weight=0.30,
                    max_score=25,
                    description="Clear thesis statement and argument development",
                ),
                "evidence": GradingCriteria(
                    name="Evidence & Support",
                    weight=0.25,
                    max_score=25,
                    description="Use of evidence, examples, and supporting details",
                ),
                "analysis": GradingCriteria(
                    name="Critical Analysis",
                    weight=0.25,
                    max_score=25,
                    description="Depth of analysis and critical thinking",
                ),
                "mechanics": GradingCriteria(
                    name="Writing Mechanics",
                    weight=0.20,
                    max_score=25,
                    description="Grammar, style, and academic writing conventions",
                ),
            },
            "creative_writing": {
                "creativity": GradingCriteria(
                    name="Creativity & Originality",
                    weight=0.30,
                    max_score=25,
                    description="Original ideas, creative expression, and imagination",
                ),
                "narrative": GradingCriteria(
                    name="Narrative Structure",
                    weight=0.25,
                    max_score=25,
                    description="Plot development, character development, and pacing",
                ),
                "language": GradingCriteria(
                    name="Language & Style",
                    weight=0.25,
                    max_score=25,
                    description="Descriptive language, literary devices, and voice",
                ),
                "mechanics": GradingCriteria(
                    name="Technical Skills",
                    weight=0.20,
                    max_score=25,
                    description="Grammar, spelling, and writing conventions",
                ),
            },
            "argumentative": {
                "claim": GradingCriteria(
                    name="Claim & Position",
                    weight=0.25,
                    max_score=25,
                    description="Clear claim and position on the issue",
                ),
                "reasoning": GradingCriteria(
                    name="Reasoning & Logic",
                    weight=0.30,
                    max_score=25,
                    description="Logical reasoning and argument development",
                ),
                "evidence": GradingCriteria(
                    name="Evidence & Sources",
                    weight=0.25,
                    max_score=25,
                    description="Quality and relevance of evidence and sources",
                ),
                "counterargument": GradingCriteria(
                    name="Counterargument",
                    weight=0.20,
                    max_score=25,
                    description="Acknowledgment and refutation of opposing views",
                ),
            },
            "learning_story": {
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
            },
        }

        return rubrics.get(rubric_type, rubrics["standard"])

    def grade_essay(
        self,
        essay_text: str,
        analysis_results: Dict[str, Any],
        prompt: Optional[str] = None,
        language: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Grade an essay based on the selected rubric.

        Args:
            essay_text: The essay content
            analysis_results: Results from essay analysis
            prompt: Optional essay prompt
            language: Optional language override for generated feedback

        Returns:
            Dictionary containing grading results
        """
        # Calculate scores for each criterion
        active_language = self._normalize_language(language or self.language)
        criteria_scores = {}

        for criterion_key, criterion in self.rubric.items():
            score = self._grade_criterion(
                essay_text, analysis_results, criterion, prompt
            )
            criteria_scores[criterion_key] = score

        # Calculate overall score
        overall_score = self._calculate_overall_score(criteria_scores)

        # Determine letter grade
        letter_grade = self._get_letter_grade(overall_score)

        # Generate detailed feedback
        detailed_feedback = self._generate_detailed_feedback(
            essay_text,
            criteria_scores,
            analysis_results,
            prompt,
            language=active_language,
        )

        return {
            "overall_score": round(overall_score, 1),
            "letter_grade": letter_grade,
            "criteria_scores": {k: round(v, 1) for k, v in criteria_scores.items()},
            "content_score": criteria_scores.get(
                "content", criteria_scores.get("thesis", 0)
            ),
            "organization_score": criteria_scores.get(
                "organization", criteria_scores.get("narrative", 0)
            ),
            "grammar_score": criteria_scores.get(
                "grammar", criteria_scores.get("mechanics", 0)
            ),
            "style_score": criteria_scores.get(
                "style", criteria_scores.get("language", 0)
            ),
            "detailed_feedback": detailed_feedback,
            "rubric_used": self.rubric_type,
            "language": active_language,
            "grading_breakdown": self._get_grading_breakdown(criteria_scores),
            "workspace_attribution": "From Hasif's Workspace",
        }

    def _grade_criterion(
        self,
        essay_text: str,
        analysis_results: Dict[str, Any],
        criterion: GradingCriteria,
        prompt: Optional[str] = None,
    ) -> float:
        """Grade a specific criterion."""

        if criterion.name == "Content & Ideas" or criterion.name == "Thesis & Argument":
            return self._grade_content(essay_text, analysis_results, criterion, prompt)

        elif (
            criterion.name == "Context & Understanding"
            or criterion.name == "Learning Goals & Formulation"
        ):
            return self._grade_content(essay_text, analysis_results, criterion, prompt)

        elif (
            criterion.name == "Organization & Structure"
            or criterion.name == "Narrative Structure"
        ):
            return self._grade_organization(essay_text, analysis_results, criterion)

        elif (
            criterion.name == "Grammar & Mechanics"
            or criterion.name == "Writing Mechanics"
            or criterion.name == "Technical Skills"
        ):
            return self._grade_grammar(essay_text, analysis_results, criterion)

        elif criterion.name == "Style & Voice" or criterion.name == "Language & Style":
            return self._grade_style(essay_text, analysis_results, criterion)

        elif (
            criterion.name == "Evidence & Support"
            or criterion.name == "Evidence & Sources"
            or criterion.name == "Substantiation & Evidence Quality"
        ):
            return self._grade_evidence(essay_text, analysis_results, criterion)

        elif criterion.name == "Critical Analysis":
            return self._grade_analysis(essay_text, analysis_results, criterion)

        elif criterion.name == "Creativity & Originality":
            return self._grade_creativity(essay_text, analysis_results, criterion)

        elif criterion.name == "Claim & Position":
            return self._grade_claim(essay_text, analysis_results, criterion)

        elif criterion.name == "Reasoning & Logic":
            return self._grade_reasoning(essay_text, analysis_results, criterion)

        elif criterion.name == "Counterargument":
            return self._grade_counterargument(essay_text, analysis_results, criterion)

        else:
            # Default scoring based on basic metrics
            return self._default_scoring(essay_text, analysis_results, criterion)

    def _grade_content(
        self,
        essay_text: str,
        analysis_results: Dict,
        criterion: GradingCriteria,
        prompt: Optional[str],
    ) -> float:
        """Grade content quality and ideas."""
        base_score = criterion.max_score * 0.6  # Start with 60% base

        # Word count factor
        word_count = analysis_results.get("basic_stats", {}).get("word_count", 0)
        if word_count >= 500:
            base_score += criterion.max_score * 0.1
        elif word_count >= 300:
            base_score += criterion.max_score * 0.05

        # Vocabulary complexity
        vocab_data = analysis_results.get("vocabulary", {})
        lexical_diversity = vocab_data.get("lexical_diversity", 0)
        complex_word_ratio = vocab_data.get("complex_word_ratio", 0)

        if lexical_diversity > 0.6:
            base_score += criterion.max_score * 0.1
        if complex_word_ratio > 0.15:
            base_score += criterion.max_score * 0.1

        # AI content analysis boost
        if "content_analysis" in analysis_results:
            base_score += criterion.max_score * 0.1

        return min(base_score, criterion.max_score)

    def _grade_organization(
        self, essay_text: str, analysis_results: Dict, criterion: GradingCriteria
    ) -> float:
        """Grade organization and structure."""
        base_score = criterion.max_score * 0.5

        structure_data = analysis_results.get("structure", {})

        # Check for introduction and conclusion
        if structure_data.get("has_clear_introduction", False):
            base_score += criterion.max_score * 0.15
        if structure_data.get("has_clear_conclusion", False):
            base_score += criterion.max_score * 0.15

        # Paragraph count and balance
        paragraph_count = structure_data.get("paragraph_count", 0)
        if 3 <= paragraph_count <= 7:
            base_score += criterion.max_score * 0.1

        # Transition words
        transition_count = structure_data.get("transition_word_count", 0)
        if transition_count >= 3:
            base_score += criterion.max_score * 0.1

        return min(base_score, criterion.max_score)

    def _grade_grammar(
        self, essay_text: str, analysis_results: Dict, criterion: GradingCriteria
    ) -> float:
        """Grade grammar and mechanics."""
        base_score = criterion.max_score * 0.8  # Start high, deduct for issues

        grammar_data = analysis_results.get("grammar", {})
        issue_count = grammar_data.get("issue_count", 0)

        # Deduct points for grammar issues
        word_count = analysis_results.get("basic_stats", {}).get("word_count", 1)
        error_ratio = issue_count / word_count * 100  # Errors per 100 words

        if error_ratio > 5:
            base_score -= criterion.max_score * 0.3
        elif error_ratio > 2:
            base_score -= criterion.max_score * 0.2
        elif error_ratio > 1:
            base_score -= criterion.max_score * 0.1

        # Readability bonus
        readability_data = analysis_results.get("readability", {})
        flesch_score = readability_data.get("flesch_reading_ease", 0)
        if flesch_score > 60:  # Good readability
            base_score += criterion.max_score * 0.1

        return max(base_score, criterion.max_score * 0.3)  # Minimum 30%

    def _grade_style(
        self, essay_text: str, analysis_results: Dict, criterion: GradingCriteria
    ) -> float:
        """Grade writing style and voice."""
        base_score = criterion.max_score * 0.6

        style_data = analysis_results.get("style", {})

        # Sentence variety
        variety_score = style_data.get("sentence_variety_score", 0)
        if variety_score > 10:  # Good sentence variety
            base_score += criterion.max_score * 0.15

        # Sentence starter variety
        starter_variety = style_data.get("sentence_starter_variety", 0)
        if starter_variety > 0.7:
            base_score += criterion.max_score * 0.1

        # Sophisticated vocabulary
        vocab_data = analysis_results.get("vocabulary", {})
        sophisticated_ratio = vocab_data.get("complex_word_ratio", 0)
        if sophisticated_ratio > 0.1:
            base_score += criterion.max_score * 0.15

        return min(base_score, criterion.max_score)

    def _grade_evidence(
        self, essay_text: str, analysis_results: Dict, criterion: GradingCriteria
    ) -> float:
        """Grade use of evidence and support."""
        # This is a simplified implementation
        # In a real system, you would use more sophisticated NLP to detect evidence

        base_score = criterion.max_score * 0.5

        # Look for evidence indicators
        evidence_indicators = [
            "according to",
            "research shows",
            "studies indicate",
            "for example",
            "for instance",
            "data reveals",
            "statistics show",
            "evidence suggests",
        ]

        text_lower = essay_text.lower()
        evidence_count = sum(
            1 for indicator in evidence_indicators if indicator in text_lower
        )

        if evidence_count >= 3:
            base_score += criterion.max_score * 0.3
        elif evidence_count >= 1:
            base_score += criterion.max_score * 0.2

        # Check for specific examples
        example_indicators = ["such as", "including", "like", "namely"]
        example_count = sum(
            1 for indicator in example_indicators if indicator in text_lower
        )

        if example_count >= 2:
            base_score += criterion.max_score * 0.2

        return min(base_score, criterion.max_score)

    def _grade_analysis(
        self, essay_text: str, analysis_results: Dict, criterion: GradingCriteria
    ) -> float:
        """Grade critical analysis and thinking."""
        base_score = criterion.max_score * 0.6

        # Look for analytical language
        analytical_words = [
            "analyze",
            "examine",
            "evaluate",
            "assess",
            "compare",
            "contrast",
            "interpret",
            "conclude",
            "infer",
            "imply",
            "suggest",
            "indicate",
        ]

        text_lower = essay_text.lower()
        analytical_count = sum(1 for word in analytical_words if word in text_lower)

        if analytical_count >= 5:
            base_score += criterion.max_score * 0.25
        elif analytical_count >= 3:
            base_score += criterion.max_score * 0.15

        # Vocabulary complexity as indicator of analytical thinking
        vocab_data = analysis_results.get("vocabulary", {})
        complex_word_ratio = vocab_data.get("complex_word_ratio", 0)
        if complex_word_ratio > 0.2:
            base_score += criterion.max_score * 0.15

        return min(base_score, criterion.max_score)

    def _grade_creativity(
        self, essay_text: str, analysis_results: Dict, criterion: GradingCriteria
    ) -> float:
        """Grade creativity and originality."""
        base_score = criterion.max_score * 0.7

        # Look for creative language indicators
        creative_indicators = [
            "imagine",
            "picture",
            "visualize",
            "metaphor",
            "simile",
            "suddenly",
            "unexpectedly",
            "mysterious",
            "magical",
        ]

        text_lower = essay_text.lower()
        creative_count = sum(
            1 for indicator in creative_indicators if indicator in text_lower
        )

        if creative_count >= 3:
            base_score += criterion.max_score * 0.2
        elif creative_count >= 1:
            base_score += criterion.max_score * 0.1

        # Vocabulary diversity as creativity indicator
        vocab_data = analysis_results.get("vocabulary", {})
        lexical_diversity = vocab_data.get("lexical_diversity", 0)
        if lexical_diversity > 0.7:
            base_score += criterion.max_score * 0.1

        return min(base_score, criterion.max_score)

    def _grade_claim(
        self, essay_text: str, analysis_results: Dict, criterion: GradingCriteria
    ) -> float:
        """Grade claim and position clarity."""
        base_score = criterion.max_score * 0.6

        # Look for claim indicators
        claim_indicators = [
            "i believe",
            "i argue",
            "my position",
            "i contend",
            "i maintain",
            "it is clear that",
            "therefore",
            "thus",
            "in conclusion",
        ]

        text_lower = essay_text.lower()
        claim_count = sum(
            1 for indicator in claim_indicators if indicator in text_lower
        )

        if claim_count >= 2:
            base_score += criterion.max_score * 0.25
        elif claim_count >= 1:
            base_score += criterion.max_score * 0.15

        # Check for thesis-like statements in first paragraph
        paragraphs = [p.strip() for p in essay_text.split("\n\n") if p.strip()]
        if paragraphs:
            first_para = paragraphs[0].lower()
            if any(indicator in first_para for indicator in claim_indicators):
                base_score += criterion.max_score * 0.15

        return min(base_score, criterion.max_score)

    def _grade_reasoning(
        self, essay_text: str, analysis_results: Dict, criterion: GradingCriteria
    ) -> float:
        """Grade reasoning and logical development."""
        base_score = criterion.max_score * 0.6

        # Look for logical connectors
        logical_connectors = [
            "because",
            "since",
            "therefore",
            "thus",
            "consequently",
            "as a result",
            "due to",
            "leads to",
            "causes",
            "results in",
        ]

        text_lower = essay_text.lower()
        logic_count = sum(
            1 for connector in logical_connectors if connector in text_lower
        )

        if logic_count >= 5:
            base_score += criterion.max_score * 0.25
        elif logic_count >= 3:
            base_score += criterion.max_score * 0.15

        # Transition words indicate logical flow
        structure_data = analysis_results.get("structure", {})
        transition_count = structure_data.get("transition_word_count", 0)
        if transition_count >= 5:
            base_score += criterion.max_score * 0.15

        return min(base_score, criterion.max_score)

    def _grade_counterargument(
        self, essay_text: str, analysis_results: Dict, criterion: GradingCriteria
    ) -> float:
        """Grade acknowledgment of counterarguments."""
        base_score = criterion.max_score * 0.4  # Lower base since this is often missing

        # Look for counterargument indicators
        counter_indicators = [
            "however",
            "although",
            "while",
            "despite",
            "nevertheless",
            "on the other hand",
            "critics argue",
            "opponents claim",
            "some may say",
            "it could be argued",
        ]

        text_lower = essay_text.lower()
        counter_count = sum(
            1 for indicator in counter_indicators if indicator in text_lower
        )

        if counter_count >= 3:
            base_score += criterion.max_score * 0.4
        elif counter_count >= 1:
            base_score += criterion.max_score * 0.2

        # Look for refutation language
        refutation_indicators = [
            "but",
            "yet",
            "still",
            "nonetheless",
            "even so",
            "this argument fails",
            "this view is flawed",
        ]

        refutation_count = sum(
            1 for indicator in refutation_indicators if indicator in text_lower
        )
        if refutation_count >= 1:
            base_score += criterion.max_score * 0.2

        return min(base_score, criterion.max_score)

    def _default_scoring(
        self, essay_text: str, analysis_results: Dict, criterion: GradingCriteria
    ) -> float:
        """Default scoring method for unspecified criteria."""
        # Basic scoring based on word count and readability
        base_score = criterion.max_score * 0.6

        word_count = analysis_results.get("basic_stats", {}).get("word_count", 0)
        if word_count >= 300:
            base_score += criterion.max_score * 0.2

        readability_data = analysis_results.get("readability", {})
        flesch_score = readability_data.get("flesch_reading_ease", 0)
        if flesch_score > 50:
            base_score += criterion.max_score * 0.2

        return min(base_score, criterion.max_score)

    def _calculate_overall_score(self, criteria_scores: Dict[str, float]) -> float:
        """Calculate weighted overall score."""
        total_score = 0
        total_weight = 0

        for criterion_key, score in criteria_scores.items():
            if criterion_key in self.rubric:
                weight = self.rubric[criterion_key].weight
                total_score += score * weight
                total_weight += weight

        if total_weight == 0:
            return 0

        # Convert to 100-point scale
        weighted_average = total_score / total_weight
        return (
            weighted_average / 25
        ) * 100  # Assuming max_score is 25 for each criterion

    def _get_letter_grade(self, overall_score: float) -> str:
        """Convert numerical score to letter grade."""
        if overall_score >= 97:
            return "A+"
        elif overall_score >= 93:
            return "A"
        elif overall_score >= 90:
            return "A-"
        elif overall_score >= 87:
            return "B+"
        elif overall_score >= 83:
            return "B"
        elif overall_score >= 80:
            return "B-"
        elif overall_score >= 77:
            return "C+"
        elif overall_score >= 73:
            return "C"
        elif overall_score >= 70:
            return "C-"
        elif overall_score >= 67:
            return "D+"
        elif overall_score >= 63:
            return "D"
        elif overall_score >= 60:
            return "D-"
        else:
            return "F"

    def _generate_detailed_feedback(
        self,
        essay_text: str,
        criteria_scores: Dict[str, float],
        analysis_results: Dict[str, Any],
        prompt: Optional[str] = None,
        language: str = "en",
    ) -> str:
        """Generate detailed feedback using AI."""
        if not self.analyzer:
            return "Detailed feedback requires AI analyzer initialization."

        try:
            # Prepare feedback prompt
            scores_summary = "\n".join(
                [
                    f"- {self.rubric[k].name}: {v:.1f}/{self.rubric[k].max_score}"
                    for k, v in criteria_scores.items()
                    if k in self.rubric
                ]
            )

            language_name = "Dutch" if language == "nl" else "English"
            system_message = f"""You are an expert writing instructor providing detailed feedback on student essays. 
            
The essay has been graded using the {self.rubric_type} rubric with the following scores:
{scores_summary}

Provide constructive, specific feedback that:
1. Acknowledges strengths in the writing
2. Identifies specific areas for improvement
3. Offers concrete suggestions for enhancement
4. Maintains an encouraging and supportive tone
5. References specific aspects of the rubric criteria

Return all feedback in {language_name}.

Keep feedback professional and educational. From Hasif's Workspace."""

            user_message = f"Essay to provide feedback on:\n\n{essay_text}"

            if prompt:
                user_message = f"Essay prompt: {prompt}\n\n{user_message}"

            messages = [
                SystemMessage(content=system_message),
                HumanMessage(content=user_message),
            ]

            response = self.analyzer.llm(messages)
            return response.content

        except Exception as e:
            return f"Error generating detailed feedback: {str(e)}"

    def _get_grading_breakdown(
        self, criteria_scores: Dict[str, float]
    ) -> Dict[str, Any]:
        """Get detailed grading breakdown."""
        breakdown = {}

        for criterion_key, score in criteria_scores.items():
            if criterion_key in self.rubric:
                criterion = self.rubric[criterion_key]
                percentage = (score / criterion.max_score) * 100

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
        """Get performance level description."""
        if percentage >= 90:
            return "Excellent"
        elif percentage >= 80:
            return "Proficient"
        elif percentage >= 70:
            return "Developing"
        elif percentage >= 60:
            return "Beginning"
        else:
            return "Below Basic"
