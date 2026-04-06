"""
Feedback Generator Module

AI-powered feedback generation for comprehensive essay evaluation.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from langchain_core.messages import HumanMessage, SystemMessage


class FeedbackGenerator:
    """
    Generates detailed, constructive feedback for essays using AI.
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

    def _localize_fixed_feedback_sections(self, feedback: Dict[str, str]) -> Dict[str, str]:
        """Deterministically localize fixed feedback blocks to Dutch.

        This avoids relying on LLM translation for the main UI sections.
        """
        dutch_map = {
            "**Adequate Length**: Your essay meets the expected word count, demonstrating thorough development of ideas.": "**Voldoende lengte**: Je essay voldoet aan het verwachte aantal woorden en laat een grondige uitwerking van idee+�n zien.",
            "**Good Length**: Your essay has a solid word count that allows for meaningful discussion of the topic.": "**Goede lengte**: Je essay heeft een sterk aantal woorden, waardoor een inhoudelijke bespreking van het onderwerp mogelijk is.",
            "**Rich Vocabulary**: You demonstrate excellent vocabulary diversity, using varied and sophisticated word choices.": "**Rijke woordenschat**: Je laat uitstekende variatie in woordgebruik zien met gevarieerde en verfijnde woordkeuzes.",
            "**Good Vocabulary**: Your vocabulary shows good variety and appropriate word selection.": "**Goede woordenschat**: Je woordenschat toont goede variatie en passende woordkeuzes.",
            "**Academic Language**: You effectively use complex vocabulary that enhances the sophistication of your writing.": "**Academisch taalgebruik**: Je gebruikt complexe woordenschat effectief, wat de kwaliteit van je schrijfstijl verhoogt.",
            "**Strong Introduction**: Your essay begins with a clear introduction that sets up your topic effectively.": "**Sterke inleiding**: Je essay begint met een duidelijke inleiding die het onderwerp effectief neerzet.",
            "**Effective Conclusion**: Your essay ends with a conclusion that brings closure to your discussion.": "**Effectieve conclusie**: Je essay eindigt met een conclusie die je betoog op een duidelijke manier afrondt.",
            "**Good Flow**: You use transition words effectively to connect ideas and create smooth flow between paragraphs.": "**Goede samenhang**: Je gebruikt verbindingswoorden effectief om idee+�n te koppelen en een vloeiende overgang tussen alinea���s te cre+�ren.",
            "**Clear Writing**: Your writing is clear and accessible, making it easy for readers to follow your ideas.": "**Duidelijk schrijfwerk**: Je tekst is helder en toegankelijk, waardoor lezers je idee+�n gemakkelijk kunnen volgen.",
            "**Strong Mechanics**: Your essay demonstrates excellent grammar and mechanical accuracy.": "**Sterke taalverzorging**: Je essay laat uitstekende grammatica en taaltechnische nauwkeurigheid zien.",
            "**Good Mechanics**: Your essay shows solid command of grammar and writing conventions.": "**Goede taalverzorging**: Je essay toont een degelijke beheersing van grammatica en schrijfconventies.",
            "**Sentence Variety**: You demonstrate good sentence variety, creating engaging and dynamic prose.": "**Variatie in zinnen**: Je laat goede afwisseling in zinsbouw zien, wat je tekst boeiend en dynamisch maakt.",
            "**Positive Tone**: Your writing maintains an engaging and optimistic tone throughout.": "**Positieve toon**: Je tekst behoudt een betrokken en optimistische toon.",
            "**Balanced Tone**: Your writing maintains an appropriate and balanced tone for academic discourse.": "**Gebalanceerde toon**: Je tekst houdt een passende en evenwichtige toon aan voor academisch schrijven.",
            "**Effort and Completion**: You have completed the assignment and demonstrated effort in your writing.": "**Inzet en afronding**: Je hebt de opdracht afgerond en duidelijke inzet getoond in je schrijfwerk.",
            "**Essay Length**: Consider expanding your essay to develop your ideas more fully. Aim for at least 300-500 words to provide adequate depth and detail.": "**Lengte van het essay**: Overweeg je essay uit te breiden zodat je idee+�n vollediger worden uitgewerkt. Streef naar minstens 300-500 woorden voor voldoende diepgang en detail.",
            "**Introduction**: Strengthen your introduction by clearly stating your main topic or thesis. A strong opening paragraph should engage the reader and preview your main points.": "**Inleiding**: Versterk je inleiding door je hoofdonderwerp of stelling duidelijk te formuleren. Een sterke openingsalinea trekt de lezer aan en kondigt je belangrijkste punten aan.",
            "**Conclusion**: Add a more definitive conclusion that summarizes your main points and provides closure. Avoid simply restating your introduction.": "**Conclusie**: Voeg een duidelijkere conclusie toe die je hoofdpunten samenvat en je tekst afrondt. Vermijd het simpelweg herhalen van je inleiding.",
            "**Paragraph Structure**: Organize your essay into more distinct paragraphs. Each paragraph should focus on one main idea and include supporting details.": "**Alineastructuur**: Organiseer je essay in duidelijkere alinea���s. Elke alinea moet zich richten op +�+�n hoofdidee met ondersteunende details.",
            "**Transitions**: Use more transition words and phrases to connect your ideas and improve the flow between paragraphs (e.g., 'furthermore,' 'however,' 'in addition').": "**Overgangen**: Gebruik meer verbindingswoorden en -zinnen om je idee+�n te verbinden en de samenhang tussen alinea���s te verbeteren (bijv. 'bovendien', 'echter', 'daarnaast').",
            "**Vocabulary Variety**: Expand your vocabulary by using more varied word choices. Avoid repeating the same words frequently and consider using synonyms.": "**Variatie in woordenschat**: Breid je woordenschat uit door gevarieerdere woordkeuzes te gebruiken. Vermijd herhaling en gebruik waar passend synoniemen.",
            "**Grammar and Mechanics**: Focus on improving grammar, spelling, and punctuation. Consider proofreading more carefully or using grammar-checking tools.": "**Grammatica en taalverzorging**: Richt je op verbetering van grammatica, spelling en interpunctie. Overweeg zorgvuldiger na te kijken of hulpmiddelen voor taalcontrole te gebruiken.",
            "**Proofreading**: Review your essay for minor grammar and mechanical errors. A final proofread can help catch small mistakes.": "**Nalezen**: Controleer je essay op kleine grammaticale en taaltechnische fouten. Een laatste controleronde helpt om details te verbeteren.",
            "**Sentence Clarity**: Some sentences may be too complex. Consider breaking down long, complicated sentences into shorter, clearer ones.": "**Duidelijkheid van zinnen**: Sommige zinnen zijn mogelijk te complex. Overweeg lange en ingewikkelde zinnen op te delen in kortere, duidelijkere zinnen.",
            "**Word Choice**: Avoid overusing certain words. Look for opportunities to use synonyms and vary your language.": "**Woordkeuze**: Vermijd overmatig gebruik van dezelfde woorden. Zoek kansen om synoniemen te gebruiken en je taalgebruik te vari+�ren.",
            "**Original Language**: Replace clich+�d phrases with more original and specific language that better expresses your ideas.": "**Origineel taalgebruik**: Vervang clich+�-uitdrukkingen door originelere en specifiekere formuleringen die je idee+�n beter overbrengen.",
            "**Overall Development**: Focus on developing your ideas more thoroughly with specific examples, details, and explanations to support your main points.": "**Algemene uitwerking**: Focus op een grondigere uitwerking van je idee+�n met specifieke voorbeelden, details en uitleg ter ondersteuning van je hoofdpunten.",
            "**Continue Refining**: While your essay shows good effort, continue to refine your writing by focusing on clarity, detail, and precision in your expression.": "**Blijf verfijnen**: Je essay laat goede inzet zien; blijf je schrijfwerk verbeteren door te focussen op helderheid, detail en precisie in formulering.",
            "**Expand with Examples**: Add specific examples, anecdotes, or evidence to support your main points and reach a more substantial word count.": "**Breid uit met voorbeelden**: Voeg specifieke voorbeelden, anekdotes of bewijs toe om je hoofdpunten te ondersteunen en tot een stevigere tekstomvang te komen.",
            "**Paragraph Development**: Consider organizing your essay into 4-5 paragraphs: introduction, 2-3 body paragraphs (each with one main idea), and conclusion.": "**Uitwerking van alinea���s**: Overweeg je essay te structureren in 4-5 alinea���s: inleiding, 2-3 kernalinea���s (elk met +�+�n hoofdidee) en conclusie.",
            "**Active Voice**: Try converting passive voice sentences to active voice for stronger, more direct writing. For example, change 'The ball was thrown by John' to 'John threw the ball.'": "**Actieve vorm**: Probeer zinnen in de lijdende vorm om te zetten naar de actieve vorm voor krachtiger en directer schrijven. Bijvoorbeeld: verander 'De bal werd door Jan gegooid' naar 'Jan gooide de bal.'",
            "**Sentence Length**: Break down overly long sentences into shorter, more manageable ones. Aim for an average of 15-20 words per sentence.": "**Zinslengte**: Deel te lange zinnen op in kortere, beter hanteerbare zinnen. Streef naar gemiddeld 15-20 woorden per zin.",
            "**Academic Vocabulary**: Incorporate more sophisticated vocabulary appropriate to your topic. Use a thesaurus to find more precise or academic alternatives to common words.": "**Academische woordenschat**: Gebruik meer verfijnde woordenschat die past bij je onderwerp. Gebruik eventueel een synoniemenlijst om preciezere of academischere alternatieven te vinden.",
            "**Simplify Complex Ideas**: While sophisticated vocabulary is good, ensure your ideas are clearly expressed. Consider breaking complex concepts into simpler, more digestible parts.": "**Vereenvoudig complexe idee+�n**: Hoewel geavanceerde woordenschat goed is, moeten je idee+�n duidelijk blijven. Overweeg complexe concepten op te delen in eenvoudigere onderdelen.",
            "**Add Transitions**: Use transitional phrases to connect your ideas: 'First,' 'Additionally,' 'However,' 'In contrast,' 'Furthermore,' 'Finally,' etc.": "**Voeg overgangen toe**: Gebruik verbindende zinnen om je idee+�n te koppelen: 'Ten eerste', 'Daarnaast', 'Echter', 'Daarentegen', 'Bovendien', 'Tot slot', enzovoort.",
            "**Support with Evidence**: Strengthen your arguments with specific examples, statistics, quotes, or personal experiences that directly relate to your main points.": "**Onderbouw met bewijs**: Versterk je argumenten met specifieke voorbeelden, statistieken, citaten of persoonlijke ervaringen die direct aansluiten op je hoofdpunten.",
            "**Read Aloud**: Read your essay aloud to catch awkward phrasing, run-on sentences, and areas where the flow could be improved.": "**Lees hardop**: Lees je essay hardop om onhandige formuleringen, te lange zinnen en plekken met minder vloeiende samenhang te ontdekken.",
            "**Peer Review**: Have someone else read your essay and provide feedback on clarity and persuasiveness of your arguments.": "**Peer review**: Laat iemand anders je essay lezen en feedback geven op de helderheid en overtuigingskracht van je argumenten.",
            "**Final Proofread**: After making content revisions, do a final proofread focusing specifically on grammar, spelling, and punctuation errors.": "**Laatste controle**: Doe na inhoudelijke revisie een laatste correctieronde gericht op grammatica, spelling en interpunctie.",
        }

        for key in ["strengths", "improvements", "suggestions"]:
            section_text = feedback.get(key, "")
            if not isinstance(section_text, str) or not section_text.strip():
                continue

            blocks = section_text.split("\n\n")
            feedback[key] = "\n\n".join(dutch_map.get(block, block) for block in blocks)

        return feedback

    def generate_feedback(
        self,
        essay_text: str,
        analysis_results: Dict[str, Any],
        grade_results: Dict[str, Any],
        prompt: Optional[str] = None,
        language: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Generate comprehensive feedback for an essay.

        Args:
            essay_text: The essay content
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
            self._load_learning_story_rubric_details() if rubric_used == "learning_story" else None
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

        feedback["grammar_feedback"] = self._generate_grammar_feedback(analysis_results)
        feedback["style_feedback"] = self._generate_style_feedback(analysis_results)
        feedback["structure_feedback"] = self._generate_structure_feedback(
            analysis_results
        )

        if active_language == "nl":
            feedback = self._localize_feedback(feedback, active_language)

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
            overall_score = grade_results.get("overall_score", 0)
            letter_grade = grade_results.get("letter_grade", "N/A")
            word_count = analysis_results.get("basic_stats", {}).get("word_count", 0)
            language_name = "Dutch" if language == "nl" else "English"
            retrieval_context = analysis_results.get("retrieval_context", {}) or {}
            vector_block = retrieval_context.get("vector_block", "")
            retrieval_text = ""
            if vector_block:
                retrieval_text = (
                    "Ground the feedback in these learning story examples first (highest priority):\n"
                    f"{vector_block or 'None retrieved'}\n"
                )

            hva_context = ""
            if rubric_used == "learning_story":
                expectations = []
                if rubric_details:
                    expectations = (
                        rubric_details.get("hva_guidelines", {}).get("expectations", [])
                    )

                expectation_snippet = "; ".join(expectations[:3]) if expectations else "Focus op context, leerdoelen, aanpak en bewijs volgens HvA Learning Story."

                signal_summary = ""
                if signals:
                    signal_summary = (
                        f"Detected signals ��� context: {signals.get('context_mentions', 0)}, "
                        f"goals: {signals.get('goal_statements', 0)}, actions: {signals.get('actions_count', 0)}, "
                        f"sources: {signals.get('resource_mentions', 0)}, evidence: {signals.get('evidence_mentions', 0)}."
                    )

                hva_context = (
                    "Use the HvA Learning Story rubric. Prioritize content over generic writing advice. "
                    "Focus on four pillars: (1) context/situatie/rol + deliverable/stakeholders, "
                    "(2) 2-3 learning goals formulated as 'Als student wil ik leren ... zodat ...' with success criteria, "
                    "(3) concrete learning approach with planned actions/experiments, resources and timeboxing, "
                    "(4) substantiation: sources, evidence/artefacts, reflection/feedback. "
                    f"HvA expectations: {expectation_snippet} "
                    f"{signal_summary}"
                    " Use these as guidelines���not hard restrictions���so you can adapt to the student's specific learning story. "
                    f"{retrieval_text}"
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

            user_message = f"Essay to provide feedback on:\n\n{essay_text}"
            if prompt:
                user_message = f"Essay prompt: {prompt}\n\n{user_message}"

            messages = [
                SystemMessage(content=system_message),
                HumanMessage(content=user_message),
            ]

            # Generate multiple candidates with varied temperatures and let the model pick the best.
            candidate_temps = [0.35, 0.6, 0.85]
            sample_max_tokens = 4000  # Allow full substantive feedback without truncation
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
                    chosen_feedback = str(getattr(judge_response, "content", "")).strip()
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

    def _translate_text(self, text: str, target_language: str) -> str:
        """Translate one feedback block while preserving markdown formatting."""
        if not text or not self.analyzer:
            return text

        language_name = "Dutch" if target_language == "nl" else "English"

        try:
            messages = [
                SystemMessage(
                    content=(
                        "You are a precise educational translator. "
                        "Translate the given text exactly into "
                        f"{language_name} while preserving markdown formatting and structure. "
                        "Return only the translated text."
                    )
                ),
                HumanMessage(content=text),
            ]
            response = self.analyzer.run_chat(messages, temperature=0.0)
            return response.content.strip()
        except Exception:
            return text

    def _localize_feedback(self, feedback: Dict[str, str], language: str) -> Dict[str, str]:
        """Localize generated feedback fields when a non-English output is selected."""
        if language == "en" or not self.analyzer:
            return feedback

        localizable_keys = [
            "ai_comprehensive_feedback",
            "grammar_feedback",
            "style_feedback",
            "structure_feedback",
        ]

        for key in localizable_keys:
            source_text = feedback.get(key, "")
            if isinstance(source_text, str) and source_text.strip():
                feedback[key] = self._translate_text(source_text, language)

        return feedback

    def _load_learning_story_rubric_details(self) -> Optional[Dict[str, Any]]:
        """Load HvA learning story rubric metadata once for rubric-aware prompts."""
        if self._learning_story_rubric_details is not None:
            return self._learning_story_rubric_details

        rubric_path = Path(__file__).resolve().parent.parent / "data" / "rubrics" / "learning_story.json"
        try:
            with rubric_path.open("r", encoding="utf-8") as handle:
                self._learning_story_rubric_details = json.load(handle)
        except Exception:
            self._learning_story_rubric_details = None

        return self._learning_story_rubric_details

    def _ls_text(self, language: str, en_text: str, nl_text: str) -> str:
        """Return text in the requested language."""
        return nl_text if language == "nl" else en_text

    def _identify_learning_story_strengths(
        self, analysis_results: Dict[str, Any], grade_results: Dict[str, Any], language: str
    ) -> str:
        """Identify strengths with HvA learning story focus."""
        signals = analysis_results.get("learning_story_signals", {}) or {}
        criteria_scores = grade_results.get("criteria_scores", {}) or {}

        strengths: List[str] = []

        if signals.get("context_mentions", 0) > 0:
            strengths.append(
                self._ls_text(
                    language,
                    "Context is described (situatie/rol) and connects to the learning story.",
                    "Context is beschreven (situatie/rol) en gekoppeld aan de learning story."
                )
            )

        if signals.get("deliverable_mentions", 0) > 0:
            strengths.append(
                self._ls_text(
                    language,
                    "Deliverable or result is stated, making expected outcome tangible.",
                    "Deliverable/resultaat is benoemd, waardoor de verwachting concreet is."
                )
            )

        if signals.get("goal_statements", 0) >= 2:
            strengths.append(
                self._ls_text(
                    language,
                    "Multiple learning goals are formulated; strong alignment with HvA format.",
                    "Meerdere leerdoelen zijn geformuleerd; sluit goed aan bij het HvA-format."
                )
            )

        if signals.get("success_criteria_mentions", 0) >= 1:
            strengths.append(
                self._ls_text(
                    language,
                    "Success/acceptance criteria are present, clarifying when the goal is met.",
                    "Succes-/acceptatiecriteria zijn aanwezig, waardoor duidelijk is wanneer het doel gehaald is."
                )
            )

        if signals.get("actions_count", 0) >= 2:
            strengths.append(
                self._ls_text(
                    language,
                    "Concrete learning actions or experiments are planned.",
                    "Concrete leeracties of experimenten zijn gepland."
                )
            )

        if signals.get("resource_mentions", 0) >= 2 or signals.get("link_mentions", 0) >= 1:
            strengths.append(
                self._ls_text(
                    language,
                    "Multiple sources/resources are cited to support the plan.",
                    "Meerdere bronnen/ondersteuning worden genoemd ter onderbouwing van de aanpak."
                )
            )

        if signals.get("evidence_mentions", 0) >= 1:
            strengths.append(
                self._ls_text(
                    language,
                    "Evidence or proof of learning is considered (artefacts, tests, reflection).",
                    "Bewijs of bewijsvoering wordt benoemd (artefacten, testen, reflectie)."
                )
            )

        if not strengths:
            strengths.append(
                self._ls_text(
                    language,
                    "Learning story shows effort; refine details per rubric for higher impact.",
                    "Learning story laat inzet zien; verfijn per rubric voor meer impact."
                )
            )

        return "\n\n".join(strengths)

    def _identify_learning_story_improvements(
        self, analysis_results: Dict[str, Any], grade_results: Dict[str, Any], language: str
    ) -> str:
        """Targeted improvements for HvA learning stories."""
        signals = analysis_results.get("learning_story_signals", {}) or {}
        criteria_scores = grade_results.get("criteria_scores", {}) or {}

        improvements: List[str] = []

        if signals.get("context_mentions", 0) == 0 or criteria_scores.get("context", 0) < 18:
            improvements.append(
                self._ls_text(
                    language,
                    "Context: describe the situation/role/assignment, the stakeholders involved, and the intended deliverable/result.",
                    "Context: beschrijf situatie/rol/opdracht, betrokken stakeholders en het beoogde deliverable/resultaat."
                )
            )

        if signals.get("goal_statements", 0) < 2 or criteria_scores.get("learning_goals", 0) < 18:
            improvements.append(
                self._ls_text(
                    language,
                    "Learning goals: write 2-3 goals in the HvA format ('Als student wil ik leren ... zodat ...' / 'As a student I want to learn ... so that ...') and add a success/acceptance criterion per goal.",
                    "Leerdoelen: formuleer 2-3 doelen in het HvA-format ('Als student wil ik leren ... zodat ...') en koppel per doel een succes- of acceptatiecriterium."
                )
            )

        if signals.get("actions_count", 0) < 2 or criteria_scores.get("learning_approach", 0) < 18:
            improvements.append(
                self._ls_text(
                    language,
                    "Approach: plan 3-4 concrete actions/experiments (research, build, test, feedback) with a timeline and link them to your goals.",
                    "Aanpak: plan 3-4 concrete acties/experimenten (onderzoek, bouwen, testen, feedback) met tijdpad en koppel ze aan je doelen."
                )
            )

        if signals.get("resource_mentions", 0) < 2:
            improvements.append(
                self._ls_text(
                    language,
                    "Resources: add at least two specific sources (HvA knowledge base, lecturers/coaches, articles, tutorials) and explain why you pick each.",
                    "Bronnen: voeg minimaal twee specifieke bronnen toe (HvA-kennisbank, docenten/lectoraat, artikelen, tutorials) en motiveer je keuze."
                )
            )

        if signals.get("evidence_mentions", 0) < 1:
            improvements.append(
                self._ls_text(
                    language,
                    "Evidence: describe what proof you will deliver (artefact/demo/reflection), how you will validate it (test result/review), and how you will process feedback.",
                    "Bewijslast: omschrijf welk bewijs je oplevert (artefact/demo/reflectie), hoe je toetst (testresultaat/review) en hoe je feedback verwerkt."
                )
            )

        if signals.get("reflection_mentions", 0) < 1:
            improvements.append(
                self._ls_text(
                    language,
                    "Reflection/feedback: schedule a moment to gather feedback and briefly reflect on progress and the next step.",
                    "Reflectie/feedback: plan een moment om feedback te verzamelen en kort te reflecteren op voortgang en volgende stap."
                )
            )

        if not improvements:
            improvements.append(
                self._ls_text(
                    language,
                    "Deepen the learning story with extra evidence and sharper acceptance criteria to reach the next quality level.",
                    "Verdiep de learning story met extra bewijs en scherpere acceptatiecriteria om naar de volgende kwaliteitsstap te gaan."
                )
            )

        return "\n\n".join(improvements)

    def _generate_learning_story_suggestions(
        self, analysis_results: Dict[str, Any], grade_results: Dict[str, Any], language: str
    ) -> str:
        """Actionable next steps for HvA learning stories."""
        signals = analysis_results.get("learning_story_signals", {}) or {}

        suggestions: List[str] = []

        suggestions.append(
            self._ls_text(
                language,
                "Rewrite goals: craft 2-3 goals in 'Als student wil ik leren ... zodat ...' / 'As a student I want to learn ... so that ...' and add a success criterion per goal.",
                "Herformuleer doelen: schrijf 2-3 doelen in 'Als student wil ik leren ... zodat ...' en voeg een succescriterium toe per doel."
            )
        )

        if signals.get("actions_count", 0) < 3:
            suggestions.append(
                self._ls_text(
                    language,
                    "Plan actions: list three concrete actions/experiments (research, build, test) with a week-by-week planning and expected outcome.",
                    "Plan acties: noteer drie concrete acties/experimenten (onderzoek, bouwen, testen) met een weekplanning en verwachte uitkomst."
                )
            )

        if signals.get("resource_mentions", 0) < 2:
            suggestions.append(
                self._ls_text(
                    language,
                    "Connect sources: select at least two concrete sources (HvA knowledge base, articles, lecturer/coach) and note how you will use each one.",
                    "Koppel bronnen: selecteer minimaal twee specifieke bronnen (HvA-kennisbank, artikelen, docent/coach) en geef per bron wat je ermee doet."
                )
            )

        if signals.get("evidence_mentions", 0) < 1:
            suggestions.append(
                self._ls_text(
                    language,
                    "Evidence plan: decide which artefact or result you will deliver (code/demo/reflection), how you will test/review it, and how you will process feedback.",
                    "Bewijsplan: bepaal welk artefact of resultaat je oplevert (code/demo/reflectie), hoe je het toetst (review/test) en hoe je feedback verwerkt."
                )
            )

        suggestions.append(
            self._ls_text(
                language,
                "HvA structure check: follow Context -> Learning goals + success criteria -> Approach/experiments -> Sources -> Evidence/reflection.",
                "Check op HvA-structuur: volg de volgorde Context -> Leerdoelen + succescriteria -> Aanpak/experimenten -> Bronnen -> Bewijs/reflectie."
            )
        )

        return "\n\n".join(suggestions)

    def _identify_strengths(
        self, analysis_results: Dict[str, Any], grade_results: Dict[str, Any]
    ) -> str:
        """Identify and describe essay strengths."""
        strengths = []

        # Check basic statistics
        basic_stats = analysis_results.get("basic_stats", {})
        word_count = basic_stats.get("word_count", 0)

        if word_count >= 500:
            strengths.append(
                "**Adequate Length**: Your essay meets the expected word count, demonstrating thorough development of ideas."
            )
        elif word_count >= 300:
            strengths.append(
                "**Good Length**: Your essay has a solid word count that allows for meaningful discussion of the topic."
            )

        # Check vocabulary
        vocab_data = analysis_results.get("vocabulary", {})
        lexical_diversity = vocab_data.get("lexical_diversity", 0)
        complex_word_ratio = vocab_data.get("complex_word_ratio", 0)

        if lexical_diversity > 0.6:
            strengths.append(
                "**Rich Vocabulary**: You demonstrate excellent vocabulary diversity, using varied and sophisticated word choices."
            )
        elif lexical_diversity > 0.4:
            strengths.append(
                "**Good Vocabulary**: Your vocabulary shows good variety and appropriate word selection."
            )

        if complex_word_ratio > 0.15:
            strengths.append(
                "**Academic Language**: You effectively use complex vocabulary that enhances the sophistication of your writing."
            )

        # Check structure
        structure_data = analysis_results.get("structure", {})

        if structure_data.get("has_clear_introduction", False):
            strengths.append(
                "**Strong Introduction**: Your essay begins with a clear introduction that sets up your topic effectively."
            )

        if structure_data.get("has_clear_conclusion", False):
            strengths.append(
                "**Effective Conclusion**: Your essay ends with a conclusion that brings closure to your discussion."
            )

        transition_count = structure_data.get("transition_word_count", 0)
        if transition_count >= 5:
            strengths.append(
                "**Good Flow**: You use transition words effectively to connect ideas and create smooth flow between paragraphs."
            )

        # Check readability
        readability_data = analysis_results.get("readability", {})
        flesch_score = readability_data.get("flesch_reading_ease", 0)

        if flesch_score > 60:
            strengths.append(
                "**Clear Writing**: Your writing is clear and accessible, making it easy for readers to follow your ideas."
            )

        # Check grammar
        grammar_data = analysis_results.get("grammar", {})
        issue_count = grammar_data.get("issue_count", 0)

        if issue_count <= 2:
            strengths.append(
                "**Strong Mechanics**: Your essay demonstrates excellent grammar and mechanical accuracy."
            )
        elif issue_count <= 5:
            strengths.append(
                "**Good Mechanics**: Your essay shows solid command of grammar and writing conventions."
            )

        # Check style
        style_data = analysis_results.get("style", {})
        variety_score = style_data.get("sentence_variety_score", 0)

        if variety_score > 10:
            strengths.append(
                "**Sentence Variety**: You demonstrate good sentence variety, creating engaging and dynamic prose."
            )

        # Check sentiment for appropriate tone
        sentiment_data = analysis_results.get("sentiment", {})
        if sentiment_data:
            tone = sentiment_data.get("overall_tone", "neutral")
            if tone == "positive":
                strengths.append(
                    "**Positive Tone**: Your writing maintains an engaging and optimistic tone throughout."
                )
            elif tone == "neutral":
                strengths.append(
                    "**Balanced Tone**: Your writing maintains an appropriate and balanced tone for academic discourse."
                )

        if not strengths:
            strengths.append(
                "**Effort and Completion**: You have completed the assignment and demonstrated effort in your writing."
            )

        return "\n\n".join(strengths)

    def _identify_improvements(
        self, analysis_results: Dict[str, Any], grade_results: Dict[str, Any]
    ) -> str:
        """Identify areas for improvement."""
        improvements = []

        # Check word count
        basic_stats = analysis_results.get("basic_stats", {})
        word_count = basic_stats.get("word_count", 0)

        if word_count < 250:
            improvements.append(
                "**Essay Length**: Consider expanding your essay to develop your ideas more fully. Aim for at least 300-500 words to provide adequate depth and detail."
            )

        # Check structure issues
        structure_data = analysis_results.get("structure", {})

        if not structure_data.get("has_clear_introduction", False):
            improvements.append(
                "**Introduction**: Strengthen your introduction by clearly stating your main topic or thesis. A strong opening paragraph should engage the reader and preview your main points."
            )

        if not structure_data.get("has_clear_conclusion", False):
            improvements.append(
                "**Conclusion**: Add a more definitive conclusion that summarizes your main points and provides closure. Avoid simply restating your introduction."
            )

        paragraph_count = structure_data.get("paragraph_count", 0)
        if paragraph_count < 3:
            improvements.append(
                "**Paragraph Structure**: Organize your essay into more distinct paragraphs. Each paragraph should focus on one main idea and include supporting details."
            )

        transition_count = structure_data.get("transition_word_count", 0)
        if transition_count < 2:
            improvements.append(
                "**Transitions**: Use more transition words and phrases to connect your ideas and improve the flow between paragraphs (e.g., 'furthermore,' 'however,' 'in addition')."
            )

        # Check vocabulary
        vocab_data = analysis_results.get("vocabulary", {})
        lexical_diversity = vocab_data.get("lexical_diversity", 0)

        if lexical_diversity < 0.4:
            improvements.append(
                "**Vocabulary Variety**: Expand your vocabulary by using more varied word choices. Avoid repeating the same words frequently and consider using synonyms."
            )

        # Check grammar issues
        grammar_data = analysis_results.get("grammar", {})
        issue_count = grammar_data.get("issue_count", 0)

        if issue_count > 10:
            improvements.append(
                "**Grammar and Mechanics**: Focus on improving grammar, spelling, and punctuation. Consider proofreading more carefully or using grammar-checking tools."
            )
        elif issue_count > 5:
            improvements.append(
                "**Proofreading**: Review your essay for minor grammar and mechanical errors. A final proofread can help catch small mistakes."
            )

        # Check readability
        readability_data = analysis_results.get("readability", {})
        flesch_score = readability_data.get("flesch_reading_ease", 0)

        if flesch_score < 30:
            improvements.append(
                "**Sentence Clarity**: Some sentences may be too complex. Consider breaking down long, complicated sentences into shorter, clearer ones."
            )

        # Check style issues
        style_data = analysis_results.get("style", {})
        starter_variety = style_data.get("sentence_starter_variety", 0)

        if starter_variety < 0.5:
            improvements.append(
                "**Sentence Variety**: Vary how you begin your sentences. Starting too many sentences the same way can make your writing feel repetitive."
            )

        style_issues = style_data.get("style_issues", [])
        if style_issues:
            issue_types = set(issue["type"] for issue in style_issues)
            if "Overused Word" in issue_types:
                improvements.append(
                    "**Word Choice**: Avoid overusing certain words. Look for opportunities to use synonyms and vary your language."
                )
            if "Clich+�" in issue_types:
                improvements.append(
                    "**Original Language**: Replace clich+�d phrases with more original and specific language that better expresses your ideas."
                )

        # Check overall score for general improvements
        overall_score = grade_results.get("overall_score", 0)

        if overall_score < 70:
            improvements.append(
                "**Overall Development**: Focus on developing your ideas more thoroughly with specific examples, details, and explanations to support your main points."
            )

        if not improvements:
            improvements.append(
                "**Continue Refining**: While your essay shows good effort, continue to refine your writing by focusing on clarity, detail, and precision in your expression."
            )

        return "\n\n".join(improvements)

    def _generate_suggestions(
        self, analysis_results: Dict[str, Any], grade_results: Dict[str, Any]
    ) -> str:
        """Generate specific actionable suggestions."""
        suggestions = []

        # Content development suggestions
        word_count = analysis_results.get("basic_stats", {}).get("word_count", 0)
        if word_count < 400:
            suggestions.append(
                "**Expand with Examples**: Add specific examples, anecdotes, or evidence to support your main points and reach a more substantial word count."
            )

        # Structure suggestions
        structure_data = analysis_results.get("structure", {})
        paragraph_count = structure_data.get("paragraph_count", 0)

        if paragraph_count < 4:
            suggestions.append(
                "**Paragraph Development**: Consider organizing your essay into 4-5 paragraphs: introduction, 2-3 body paragraphs (each with one main idea), and conclusion."
            )

        # Grammar and style suggestions
        grammar_data = analysis_results.get("grammar", {})
        grammar_issues = grammar_data.get("grammar_issues", [])

        if grammar_issues:
            passive_voice_count = sum(
                1 for issue in grammar_issues if issue.get("type") == "Passive Voice"
            )
            if passive_voice_count > 2:
                suggestions.append(
                    "**Active Voice**: Try converting passive voice sentences to active voice for stronger, more direct writing. For example, change 'The ball was thrown by John' to 'John threw the ball.'"
                )

            long_sentence_count = sum(
                1 for issue in grammar_issues if issue.get("type") == "Long Sentence"
            )
            if long_sentence_count > 1:
                suggestions.append(
                    "**Sentence Length**: Break down overly long sentences into shorter, more manageable ones. Aim for an average of 15-20 words per sentence."
                )

        # Vocabulary suggestions
        vocab_data = analysis_results.get("vocabulary", {})
        complex_word_ratio = vocab_data.get("complex_word_ratio", 0)

        if complex_word_ratio < 0.1:
            suggestions.append(
                "**Academic Vocabulary**: Incorporate more sophisticated vocabulary appropriate to your topic. Use a thesaurus to find more precise or academic alternatives to common words."
            )

        # Readability suggestions
        readability_data = analysis_results.get("readability", {})
        flesch_kincaid_grade = readability_data.get("flesch_kincaid_grade", 0)

        if flesch_kincaid_grade > 12:
            suggestions.append(
                "**Simplify Complex Ideas**: While sophisticated vocabulary is good, ensure your ideas are clearly expressed. Consider breaking complex concepts into simpler, more digestible parts."
            )

        # Transition suggestions
        transition_count = structure_data.get("transition_word_count", 0)
        if transition_count < 3:
            suggestions.append(
                "**Add Transitions**: Use transitional phrases to connect your ideas: 'First,' 'Additionally,' 'However,' 'In contrast,' 'Furthermore,' 'Finally,' etc."
            )

        # Evidence and support suggestions
        suggestions.append(
            "**Support with Evidence**: Strengthen your arguments with specific examples, statistics, quotes, or personal experiences that directly relate to your main points."
        )

        # Revision suggestions
        suggestions.append(
            "**Read Aloud**: Read your essay aloud to catch awkward phrasing, run-on sentences, and areas where the flow could be improved."
        )

        suggestions.append(
            "**Peer Review**: Have someone else read your essay and provide feedback on clarity and persuasiveness of your arguments."
        )

        # Final polish suggestions
        suggestions.append(
            "**Final Proofread**: After making content revisions, do a final proofread focusing specifically on grammar, spelling, and punctuation errors."
        )

        return "\n\n".join(suggestions)

    def _generate_grammar_feedback(self, analysis_results: Dict[str, Any]) -> str:
        """Generate specific grammar feedback."""
        grammar_data = analysis_results.get("grammar", {})
        grammar_issues = grammar_data.get("grammar_issues", [])

        if not grammar_issues:
            return "**Excellent Grammar**: Your essay demonstrates strong command of grammar and mechanics with minimal errors."

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
                feedback_parts.append(
                    f"**Long Sentences** ({count} instances): Consider breaking down lengthy sentences for better readability. Aim for 15-25 words per sentence on average."
                )

            elif issue_type == "Short Sentence":
                feedback_parts.append(
                    f"**Short Sentences** ({count} instances): Some sentences are very brief. Consider combining related short sentences or adding more detail."
                )

            elif issue_type == "Passive Voice":
                feedback_parts.append(
                    f"**Passive Voice** ({count} instances): Try using active voice for more direct and engaging writing. Active voice typically makes your writing stronger and clearer."
                )

            elif issue_type == "Sentence Fragment":
                feedback_parts.append(
                    f"**Sentence Fragments** ({count} instances): Ensure all sentences are complete with a subject and predicate. Fragments can confuse readers."
                )

            else:
                feedback_parts.append(
                    f"**{issue_type}** ({count} instances): Review these areas for improvement."
                )

        return "\n\n".join(feedback_parts)

    def _generate_style_feedback(self, analysis_results: Dict[str, Any]) -> str:
        """Generate specific style feedback."""
        style_data = analysis_results.get("style", {})

        feedback_parts = []

        # Sentence variety
        variety_score = style_data.get("sentence_variety_score", 0)
        if variety_score < 5:
            feedback_parts.append(
                "**Sentence Variety**: Your sentences tend to be similar in length. Try varying sentence length and structure to create more engaging prose."
            )
        elif variety_score > 15:
            feedback_parts.append(
                "**Sentence Consistency**: While variety is good, ensure your sentences maintain a consistent style appropriate for your audience."
            )
        else:
            feedback_parts.append(
                "**Good Sentence Variety**: You demonstrate effective variation in sentence length and structure."
            )

        # Sentence starters
        starter_variety = style_data.get("sentence_starter_variety", 0)
        if starter_variety < 0.6:
            feedback_parts.append(
                "**Sentence Beginnings**: Vary how you start your sentences. Avoid beginning too many sentences with the same words or patterns."
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
                    feedback_parts.append(
                        f"**Word Repetition**: You repeat certain words frequently. Use synonyms and varied vocabulary to avoid monotony."
                    )
                elif issue_type == "Clich+�":
                    feedback_parts.append(
                        f"**Clich+�d Language**: Replace overused phrases with more original and specific language."
                    )

        if not feedback_parts:
            feedback_parts.append(
                "**Strong Style**: Your writing demonstrates good stylistic choices with appropriate variety and voice."
            )

        return "\n\n".join(feedback_parts)

    def _generate_structure_feedback(self, analysis_results: Dict[str, Any]) -> str:
        """Generate specific structure feedback."""
        structure_data = analysis_results.get("structure", {})

        feedback_parts = []

        # Paragraph organization
        paragraph_count = structure_data.get("paragraph_count", 0)
        if paragraph_count < 3:
            feedback_parts.append(
                "**Paragraph Organization**: Organize your essay into more distinct paragraphs. A typical essay should have an introduction, body paragraphs (2-3), and a conclusion."
            )
        elif paragraph_count > 7:
            feedback_parts.append(
                "**Paragraph Consolidation**: Consider combining some paragraphs. Too many short paragraphs can make your essay feel choppy."
            )

        # Paragraph balance
        paragraph_lengths = structure_data.get("paragraph_lengths", [])
        if paragraph_lengths:
            avg_length = sum(paragraph_lengths) / len(paragraph_lengths)
            if avg_length < 30:
                feedback_parts.append(
                    "**Paragraph Development**: Develop your paragraphs more fully. Each paragraph should contain 50-100 words and focus on one main idea with supporting details."
                )
            elif avg_length > 150:
                feedback_parts.append(
                    "**Paragraph Length**: Some paragraphs may be too long. Consider breaking lengthy paragraphs into smaller, more focused ones."
                )

        # Introduction and conclusion
        if not structure_data.get("has_clear_introduction", False):
            feedback_parts.append(
                "**Introduction**: Strengthen your opening paragraph. A good introduction should engage the reader, introduce your topic, and preview your main points."
            )

        if not structure_data.get("has_clear_conclusion", False):
            feedback_parts.append(
                "**Conclusion**: Add a stronger conclusion that summarizes your main points and provides a sense of closure. Avoid simply repeating your introduction."
            )

        # Transitions
        transition_count = structure_data.get("transition_word_count", 0)
        if transition_count < 2:
            feedback_parts.append(
                "**Transitions**: Use more transitional words and phrases to connect your ideas and improve flow between paragraphs."
            )
        elif transition_count > 10:
            feedback_parts.append(
                "**Transition Balance**: While transitions are important, ensure they feel natural and don't overwhelm your writing."
            )

        if not feedback_parts:
            feedback_parts.append(
                "**Well-Structured**: Your essay demonstrates good organizational structure with clear paragraphs and logical flow."
            )

        return "\n\n".join(feedback_parts)
