import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from langchain_core.messages import HumanMessage, SystemMessage


class FeedbackGenerator:
    """
    Generates detailed, constructive feedback for HvA learning stories.
    """

    def __init__(self, analyzer=None, language: str = "en"):
        """
        Initialize the feedback generator.

        Args:
            analyzer: EssayAnalyzer instance for AI capabilities
            language: Language code used in generated feedback ('en' or 'nl')
        """
        self.analyzer = analyzer
        self.language = self._normalize_language(language)
        self._learning_story_rubric_details: Optional[Dict[str, Any]] = None

    def _normalize_language(self, language: str) -> str:
        """Normalize language inputs to supported codes."""
        normalized = (language or "en").strip().lower()
        aliases = {"english": "en", "dutch": "nl", "nederlands": "nl"}
        normalized = aliases.get(normalized, normalized)
        return normalized if normalized in {"en", "nl"} else "en"

    def generate_feedback(
        self,
        essay_text: str,
        analysis_results: Dict[str, Any],
        grade_results: Dict[str, Any],
        prompt: Optional[str] = None,
        language: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Generate comprehensive feedback for a learning story.

        Args:
            essay_text: The learning story content
            analysis_results: Results from essay analysis
            grade_results: Results from grading
            prompt: Optional essay prompt
            language: Optional language override for generated feedback

        Returns:
            Dictionary containing different types of feedback
        """
        active_language = self._normalize_language(language or self.language)
        feedback: Dict[str, str] = {}

        rubric_used = grade_results.get("rubric_used", "")
        learning_signals = analysis_results.get("learning_story_signals", {})
        rubric_details = (
            self._load_learning_story_rubric_details()
            if rubric_used == "learning_story"
            else None
        )

        # Generate AI-powered feedback
        if self.analyzer:
            feedback.update(
                self._generate_ai_feedback(
                    essay_text,
                    analysis_results,
                    grade_results,
                    prompt,
                    language=active_language,
                    rubric_details=rubric_details,
                    signals=learning_signals,
                    rubric_used=rubric_used,
                )
            )

        feedback["grammar_feedback"] = self._generate_grammar_feedback(
            analysis_results, active_language
        )
        feedback["style_feedback"] = self._generate_style_feedback(
            analysis_results, active_language
        )
        feedback["structure_feedback"] = self._generate_structure_feedback(
            analysis_results, active_language
        )

        # Add workspace attribution
        feedback["workspace_attribution"] = "HvA Feedback Agent"
        feedback["language"] = active_language

        return feedback

    def _generate_ai_feedback(
        self,
        essay_text: str,
        analysis_results: Dict[str, Any],
        grade_results: Dict[str, Any],
        prompt: Optional[str] = None,
        language: str = "en",
        rubric_details: Optional[Dict[str, Any]] = None,
        signals: Optional[Dict[str, Any]] = None,
        rubric_used: str = "",
    ) -> Dict[str, str]:
        """Generate AI-powered comprehensive feedback."""
        try:
            language_name = "Dutch" if language == "nl" else "English"
            retrieval_context = analysis_results.get("retrieval_context", {}) or {}
            vector_block = retrieval_context.get("vector_block", "")
            retrieval_text = ""
            if vector_block:
                retrieval_text = (
                    "Ground the feedback in these learning story examples first (highest priority):\n"
                    f"{vector_block or 'None retrieved'}\n"
                )

            quality_assessment = grade_results.get("quality_assessment", {}) or {}
            quality_text = ""
            if quality_assessment.get("available"):
                quality_text = (
                    "\nClassifier signal from local good/bad learning stories: "
                    f"label={quality_assessment.get('label')}, "
                    f"confidence={quality_assessment.get('confidence')}"
                    ". Use this as a secondary calibration signal, not as sole evidence."
                )

            hva_context = ""
            if rubric_used == "learning_story" and rubric_details:
                # Format the complete rubric for the active AI model
                full_rubric_text = self._format_rubric_for_model(rubric_details)

                signal_summary = ""
                if signals:
                    signal_summary = (
                        f"\n\nDETECTED SIGNALS IN SUBMISSION: "
                        f"context mentions: {signals.get('context_mentions', 0)}, "
                        f"goal statements: {signals.get('goal_statements', 0)}, "
                        f"actions/concrete steps: {signals.get('actions_count', 0)}, "
                        f"resource/source mentions: {signals.get('resource_mentions', 0)}, "
                        f"evidence/artefact mentions: {signals.get('evidence_mentions', 0)}."
                    )

                hva_context = (
                    "Use the complete HvA Learning Story rubric provided below. "
                    "Prioritize content and learning strategy over generic writing advice. "
                    "Use the rubric criteria, performance levels, and guidelines as your primary reference. "
                    f"{retrieval_text}"
                    f"\n{full_rubric_text}"
                    f"{signal_summary}"
                    f"{quality_text}"
                    "\n\nGuidance: Use these rubric criteria as guidelines helping you evaluate the submission comprehensively. "
                    "Adapt your feedback to the student's specific learning story; focus on the most impactful improvements."
                )

            system_message = f"""You are an expert learning-focused instructor providing detailed, constructive feedback on Learning Story submissions at HvA (Amsterdam University of Applied Sciences).

LEARNING STORY FUNDAMENTALS:
A Learning Story is a structured approach that bridges User Stories and skill development. Students must:
1. **Identify Context**: What problem/user story requires new learning? Define the role, stakeholders, and deliverables.
2. **Formulate Learning Goals**: 'Als student wil ik leren [skill/knowledge] zodat ik [concrete goal/outcome] kan bereiken.' Include success criteria for each goal.
3. **Design Learning Approach**: Concrete, step-by-step actions, planned experiments/research, relevant resources (links, books, videos, knowledge bases, mentorship), and realistic timeboxing.
4. **Substantiate with Evidence**: Cite sources, include artifacts/evidence of learning, and reflect on what was learned and how it applies.

VALUABLE RESOURCES:
- HvA Knowledge Base: https://knowledgebase.hbo-ict-hva.nl/
- W3Schools (web development): https://w3schools.com/
- Academic literature, tutorials, videos, case studies, peer feedback

Your feedback must be:
1. **Content-focused**: Evaluate depth of learning strategy, not just writing mechanics.
2. **Constructive and encouraging**: Balance positive observations with actionable improvements.
3. **Specific**: Reference the four pillars above; point to gaps explicitly.
4. **Actionable**: Suggest concrete next steps for strengthening the learning story.
5. **Pragmatic**: Adapt expectations to student level; focus on most impactful feedback.
6. **No score or grade**: Do not include any numeric score, percentage, or letter grade in the feedback.

{hva_context}

When using context, first align with the internal learning stories (highest priority). Treat rubric rules as guidance; if the student's text is atypical, adapt rather than reject it.

Provide comprehensive, detailed feedback as a single Markdown response with:
- An overall assessment
- Key observations about the submission
- Priority gaps or issues to address
- Concrete next steps
- Relevant resources or references

Return all feedback in {language_name} and format it in Markdown.
Use clear section headings, bullet lists, and short paragraphs so the feedback renders cleanly on the website.
Do not wrap the response in code fences or HTML.
Provide substantive, thorough analysis—be specific and detailed, using the full space available.

Powered by the HvA Feedback Agent system."""

            user_message = f"Learning story to provide feedback on:\n\n{essay_text}"
            if prompt:
                user_message = f"Learning objective/context: {prompt}\n\n{user_message}"

            messages = [
                SystemMessage(content=system_message),
                HumanMessage(content=user_message),
            ]

            # Generate multiple candidates with varied temperatures and let the model pick the best.
            candidate_temps = [0.35, 0.6, 0.85]
            sample_max_tokens = (
                4000  # Allow full substantive feedback without truncation
            )
            candidates: List[str] = []

            for temp in candidate_temps:
                try:
                    response = self.analyzer.run_chat(
                        messages, temperature=temp, max_tokens=sample_max_tokens
                    )
                    if getattr(response, "content", ""):
                        candidates.append(str(response.content).strip())
                except Exception:
                    continue

            # Fallback if no candidates generated
            if not candidates:
                return {
                    "ai_comprehensive_feedback": "Error generating AI feedback: no candidate responses generated.",
                    "ai_provider": "error",
                }

            if len(candidates) == 1:
                chosen_feedback = candidates[0]
            else:
                # Ask the model to choose the best candidate and return only that text.
                judge_instructions = (
                    "You are selecting the best feedback. Choose the response that is clearest, most actionable, well-structured, and concise. "
                    "Return ONLY the full text of the best candidate with no commentary, numbering, or added text."
                )

                numbered = []
                for idx, cand in enumerate(candidates, start=1):
                    numbered.append(f"Candidate {idx}:\n{cand}")

                judge_messages = [
                    SystemMessage(content=judge_instructions),
                    HumanMessage(content="\n\n".join(numbered)),
                ]

                try:
                    judge_response = self.analyzer.run_chat(
                        judge_messages, temperature=0.0, max_tokens=sample_max_tokens
                    )
                    chosen_feedback = str(
                        getattr(judge_response, "content", "")
                    ).strip()
                    if not chosen_feedback:
                        chosen_feedback = candidates[0]
                except Exception:
                    chosen_feedback = candidates[0]

            return {
                "ai_comprehensive_feedback": chosen_feedback,
                "ai_provider": f"{self.analyzer.model_provider}_{self.analyzer.model_name}",
            }

        except Exception as e:
            return {
                "ai_comprehensive_feedback": f"Error generating AI feedback: {str(e)}",
                "ai_provider": "error",
            }

    def _load_learning_story_rubric_details(self) -> Optional[Dict[str, Any]]:
        """Load HvA learning story rubric metadata once for rubric-aware prompts."""
        if self._learning_story_rubric_details is not None:
            return self._learning_story_rubric_details

        rubric_path = (
            Path(__file__).resolve().parent.parent / "rubrics" / "learning_story.json"
        )
        try:
            with rubric_path.open("r", encoding="utf-8") as handle:
                self._learning_story_rubric_details = json.load(handle)
        except Exception:
            self._learning_story_rubric_details = None

        return self._learning_story_rubric_details

    def _format_rubric_for_model(self, rubric_details: Dict[str, Any]) -> str:
        """Format the entire rubric JSON as a readable text block for the AI model."""
        if not rubric_details:
            return ""

        rubric_text = f"""
COMPLETE HVA LEARNING STORY RUBRIC:

Name: {rubric_details.get('name', 'N/A')}
Description: {rubric_details.get('description', 'N/A')}
Attribution: {rubric_details.get('attribution', 'N/A')}

GRADING CRITERIA:

"""

        criteria = rubric_details.get("criteria", {})
        for criterion_key, criterion_data in criteria.items():
            rubric_text += f"\n### {criterion_data.get('name', criterion_key)}\n"
            rubric_text += f"Weight: {criterion_data.get('weight', 0):.0%} | Max Score: {criterion_data.get('max_score', 0)}\n"
            rubric_text += (
                f"Description: {criterion_data.get('description', 'N/A')}\n\n"
            )
            rubric_text += "Performance Levels:\n"

            levels = criterion_data.get("levels", {})
            for level_key, level_data in levels.items():
                score_range = level_data.get("score_range", [0, 0])
                rubric_text += f"- **{level_key.upper()}** ({score_range[0]}-{score_range[1]} points): {level_data.get('description', 'N/A')}\n"
            rubric_text += "\n"

        # Add HvA Guidelines
        hva_guidelines = rubric_details.get("hva_guidelines", {})
        if hva_guidelines:
            rubric_text += "\nHVA GUIDELINES:\n\n"

            expectations = hva_guidelines.get("expectations", [])
            if expectations:
                rubric_text += "**Expectations:**\n"
                for i, exp in enumerate(expectations, 1):
                    rubric_text += f"{i}. {exp}\n"
                rubric_text += "\n"

            structure_hints = hva_guidelines.get("structure_hints", [])
            if structure_hints:
                rubric_text += "**Suggested Structure:**\n"
                for hint in structure_hints:
                    rubric_text += f"- {hint}\n"
                rubric_text += "\n"

        # Add Learning Story Components
        components = rubric_details.get("learning_story_components", {})
        if components:
            rubric_text += "\nLEARNING STORY COMPONENTS:\n"
            for component_key, component_desc in components.items():
                if isinstance(component_desc, list):
                    rubric_text += (
                        f"- **{component_key}**: {', '.join(component_desc)}\n"
                    )
                else:
                    rubric_text += f"- **{component_key}**: {component_desc}\n"
            rubric_text += "\n"

        return rubric_text

    def _generate_grammar_feedback(
        self, analysis_results: Dict[str, Any], language: str
    ) -> str:
        """Generate clarity feedback for learning story formulation."""
        grammar_data = analysis_results.get("grammar", {})
        grammar_issues = grammar_data.get("grammar_issues", [])

        if not grammar_issues:
            if language == "nl":
                return "**Heldere Formulering**: Je learning story is duidelijk geformuleerd en goed te volgen."
            return "**Clear Formulation**: Your learning story is clearly phrased and easy to follow."

        feedback_parts = []

        # Group issues by type
        issue_types = {}
        for issue in grammar_issues:
            issue_type = issue.get("type", "General")
            if issue_type not in issue_types:
                issue_types[issue_type] = []
            issue_types[issue_type].append(issue)

        # Provide feedback for each type
        for issue_type, issues in issue_types.items():
            count = len(issues)

            if issue_type == "Long Sentence":
                if language == "nl":
                    feedback_parts.append(
                        f"**Lange Zinnen** ({count} keer): Splits lange zinnen zodat je leerdoelen en stappen duidelijker zijn."
                    )
                else:
                    feedback_parts.append(
                        f"**Long Sentences** ({count} instances): Split long sentences so your learning goals and steps are easier to understand."
                    )

            elif issue_type == "Missing Goal Formulation":
                if language == "nl":
                    feedback_parts.append(
                        "**Leerdoelen Ontbreken**: Voeg expliciete doelzinnen toe (bijvoorbeeld: 'Als student wil ik leren ... zodat ik ...')."
                    )
                else:
                    feedback_parts.append(
                        "**Learning Goals Missing**: Add explicit goal statements (for example: 'As a student I want to learn ... so that I can ...')."
                    )

            elif issue_type == "Missing Concrete Actions":
                if language == "nl":
                    feedback_parts.append(
                        "**Concrete Stappen Ontbreken**: Beschrijf specifieke acties, experimenten of taken die je gaat uitvoeren."
                    )
                else:
                    feedback_parts.append(
                        "**Concrete Steps Missing**: Describe specific actions, experiments, or tasks you will execute."
                    )

            else:
                if language == "nl":
                    feedback_parts.append(
                        f"**{issue_type}** ({count} keer): Bekijk dit onderdeel en verbeter waar nodig."
                    )
                else:
                    feedback_parts.append(
                        f"**{issue_type}** ({count} instances): Review these areas for improvement."
                    )

        return "\n\n".join(feedback_parts)

    def _generate_style_feedback(
        self, analysis_results: Dict[str, Any], language: str
    ) -> str:
        """Generate learning-approach feedback from HvA signals."""
        style_data = analysis_results.get("style", {})

        feedback_parts = []

        # Sentence variety
        variety_score = style_data.get("sentence_variety_score", 0)
        if variety_score < 2:
            if language == "nl":
                feedback_parts.append(
                    "**Meer Detail in Aanpak**: Maak je aanpak specifieker met duidelijke stappen en verwachte uitkomsten."
                )
            else:
                feedback_parts.append(
                    "**Approach Detail**: Your approach section can be more specific. Add clear step-by-step actions and expected outcomes."
                )
        else:
            if language == "nl":
                feedback_parts.append(
                    "**Goede Aanpakduidelijkheid**: Je leerroute bevat voldoende concrete details om te volgen."
                )
            else:
                feedback_parts.append(
                    "**Good Approach Clarity**: Your learning approach contains enough concrete detail to follow."
                )

        # Sentence starters
        starter_variety = style_data.get("sentence_starter_variety", 0)
        if starter_variety < 0.2:
            if language == "nl":
                feedback_parts.append(
                    "**Actiewerkwoorden**: Gebruik duidelijke werkwoorden (onderzoeken, testen, bouwen, evalueren) om je plan uitvoerbaar te maken."
                )
            else:
                feedback_parts.append(
                    "**Action Verbs**: Use clear action verbs (research, test, build, evaluate) to make your plan more operational."
                )

        # Style issues
        style_issues = style_data.get("style_issues", [])
        if style_issues:
            issue_summary = {}
            for issue in style_issues:
                issue_type = issue.get("type", "General")
                if issue_type not in issue_summary:
                    issue_summary[issue_type] = 0
                issue_summary[issue_type] += 1

            for issue_type, count in issue_summary.items():
                if issue_type == "Overused Word":
                    if language == "nl":
                        feedback_parts.append(
                            "**Specificiteit**: Vervang herhalende algemene woorden door concrete leeracties en meetbare deliverables."
                        )
                    else:
                        feedback_parts.append(
                            "**Specificity**: Replace repeated generic wording with concrete learning actions and measurable deliverables."
                        )
                elif issue_type == "Low Action Specificity":
                    if language == "nl":
                        feedback_parts.append(
                            "**Concreetheid**: Voeg concrete stappen toe (wat, wanneer en hoe) zodat je leerproces toetsbaar wordt."
                        )
                    else:
                        feedback_parts.append(
                            "**Actionability**: Add concrete steps (what, when, and how) so others can verify your learning process."
                        )
                elif issue_type == "Missing Source Strategy":
                    if language == "nl":
                        feedback_parts.append(
                            "**Bronnenstrategie**: Voeg bronnen toe (links, documentatie, tutorials, experts) om je aanpak te onderbouwen."
                        )
                    else:
                        feedback_parts.append(
                            "**Source Strategy**: Add sources (links, docs, tutorials, experts) to substantiate your approach."
                        )

        if not feedback_parts:
            if language == "nl":
                feedback_parts.append(
                    "**Sterke Leerroute**: Je aanpak is specifiek en praktisch uitvoerbaar."
                )
            else:
                feedback_parts.append(
                    "**Strong Learning Approach**: Your approach is specific and usable as a practical plan."
                )

        return "\n\n".join(feedback_parts)

    def _generate_structure_feedback(
        self, analysis_results: Dict[str, Any], language: str
    ) -> str:
        """Generate structure feedback aligned to HvA learning story pillars."""
        structure_data = analysis_results.get("structure", {})

        feedback_parts = []

        # Paragraph organization
        paragraph_count = structure_data.get("paragraph_count", 0)
        if paragraph_count < 3:
            if language == "nl":
                feedback_parts.append(
                    "**Sectie-indeling**: Splits je learning story in duidelijkere delen (context, doelen, aanpak, bewijs/reflectie)."
                )
            else:
                feedback_parts.append(
                    "**Sectioning**: Split your learning story into clearer sections (context, goals, approach, evidence/reflection)."
                )
        elif paragraph_count > 7:
            if language == "nl":
                feedback_parts.append(
                    "**Focus**: Bundel overlappende delen zodat elke alinea een concreet punt uitwerkt."
                )
            else:
                feedback_parts.append(
                    "**Focus**: Consolidate overlapping sections so each paragraph supports one concrete point."
                )

        # Paragraph balance
        paragraph_lengths = structure_data.get("paragraph_lengths", [])
        if paragraph_lengths:
            avg_length = sum(paragraph_lengths) / len(paragraph_lengths)
            if avg_length < 30:
                if language == "nl":
                    feedback_parts.append(
                        "**Diepgang**: Werk kernonderdelen uit met concrete keuzes, onderbouwing en verwachte resultaten."
                    )
                else:
                    feedback_parts.append(
                        "**Depth**: Expand key sections with concrete decisions, rationale, and expected outcomes."
                    )
            elif avg_length > 150:
                if language == "nl":
                    feedback_parts.append(
                        "**Scanbaarheid**: Knip lange secties op zodat leerdoelen en acties sneller te beoordelen zijn."
                    )
                else:
                    feedback_parts.append(
                        "**Scannability**: Break up long sections so goals and action steps are easier to review."
                    )

        # Introduction and conclusion
        if not structure_data.get("has_clear_introduction", False):
            if language == "nl":
                feedback_parts.append(
                    "**Context Ontbreekt**: Beschrijf de opdracht/het probleem, je rol, stakeholders en het beoogde deliverable."
                )
            else:
                feedback_parts.append(
                    "**Context Missing**: Describe the assignment/problem, role, stakeholders, and intended deliverable."
                )

        if not structure_data.get("has_clear_conclusion", False):
            if language == "nl":
                feedback_parts.append(
                    "**Reflectie Ontbreekt**: Voeg een korte reflectie toe op wat je leerde en wat je de volgende keer anders doet."
                )
            else:
                feedback_parts.append(
                    "**Reflection Missing**: Add a short reflection on what you learned and what you would improve next time."
                )

        # Transitions
        transition_count = structure_data.get("transition_word_count", 0)
        if transition_count < 2:
            if language == "nl":
                feedback_parts.append(
                    "**Planningsdetail**: Voeg tijdsmarkeringen toe (week, sprint, deadline) om haalbaarheid te tonen."
                )
            else:
                feedback_parts.append(
                    "**Planning Detail**: Add timing markers (week, sprint, deadline) to strengthen feasibility."
                )

        if not feedback_parts:
            if language == "nl":
                feedback_parts.append(
                    "**Goed Gestructureerde Learning Story**: Je context, doelen, aanpak en bewijs zijn voldoende uitgewerkt."
                )
            else:
                feedback_parts.append(
                    "**Well-Structured Learning Story**: Your context, goals, approach, and evidence are sufficiently covered."
                )

        return "\n\n".join(feedback_parts)
