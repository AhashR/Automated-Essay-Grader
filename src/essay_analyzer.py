import logging
import os
import re
from typing import Any, Dict, List, Optional

import nltk
from nltk.corpus import stopwords

from src.language_utils import normalize_language

logger = logging.getLogger(__name__)

# Download required NLTK data
try:
    nltk.data.find("tokenizers/punkt_tab")
except LookupError:
    try:
        nltk.download("punkt_tab")
    except Exception:
        nltk.download("punkt")

try:
    nltk.data.find("corpora/stopwords")
except LookupError:
    nltk.download("stopwords")


class EssayAnalyzer:
    """HvA learning story analyzer focused on rubric-relevant signals."""

    def __init__(
        self,
        model_provider: str = "gemini",
        model_name: str = "gemini-2.5-flash",
        temperature: float = 0.3,
        max_tokens: int = 2000,
        language: str = "en",
        retriever: Optional[Any] = None,
        retrieval_top_k: int = 3,
        retrieval_min_score: float = 0.08,
    ):
        self.model_provider = model_provider
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.language = normalize_language(language)
        self.retriever = retriever
        self.retrieval_top_k = retrieval_top_k
        self.retrieval_min_score = retrieval_min_score
        self.english_stopwords = set(stopwords.words("english"))
        self.dutch_stopwords = set(stopwords.words("dutch"))

        self._initialize_model()

    def _detect_language(self, text: str) -> str:
        """Detect whether story text is primarily English or Dutch."""
        words = [w.lower() for w in nltk.word_tokenize(text) if w.isalpha()]
        if not words:
            return "en"

        english_hits = sum(1 for w in words if w in self.english_stopwords)
        dutch_hits = sum(1 for w in words if w in self.dutch_stopwords)

        if english_hits == dutch_hits:
            english_markers = {
                "the",
                "and",
                "because",
                "therefore",
                "however",
                "this",
                "that",
            }
            dutch_markers = {
                "de",
                "het",
                "een",
                "omdat",
                "daarom",
                "echter",
                "deze",
                "dit",
            }
            english_hits += sum(1 for w in words if w in english_markers)
            dutch_hits += sum(1 for w in words if w in dutch_markers)

        return "nl" if dutch_hits > english_hits else "en"

    def _gather_retrieval_context(
        self, essay_text: str, prompt: Optional[str], language: str
    ) -> Dict[str, Any]:
        """Pull top matches from the internal vector store."""
        query_text = f"{prompt or ''}\n\n{essay_text}" if prompt else essay_text
        context: Dict[str, Any] = {"vector_hits": [], "notes": []}

        if self.retriever:
            try:
                context["vector_hits"] = self.retriever.search(
                    query_text,
                    top_k=self.retrieval_top_k,
                    language=language,
                    min_score=self.retrieval_min_score,
                )
            except Exception as exc:
                context["notes"].append(f"Vector search unavailable: {exc}")

        return context

    def _format_retrieval_blocks(
        self, retrieval_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Pre-format retrieval hits for prompt injection."""
        vector_block = ""
        retriever = self.retriever

        if (
            retrieval_context.get("vector_hits")
            and retriever is not None
            and hasattr(retriever, "build_context_block")
        ):
            vector_block = retriever.build_context_block(
                retrieval_context.get("vector_hits", [])
            )

        retrieval_context["vector_block"] = vector_block
        return retrieval_context

    def _initialize_model(self):
        """Initialize the AI model based on provider."""
        try:
            self.llm = self._build_llm()
        except Exception as e:
            raise Exception(f"Failed to initialize AI model: {str(e)}")

    def _build_llm(
        self, temperature: Optional[float] = None, max_tokens: Optional[int] = None
    ):
        """Construct a provider-specific LLM with optional overrides."""
        temp = self.temperature if temperature is None else temperature
        tokens = self.max_tokens if max_tokens is None else max_tokens

        if self.model_provider == "gemini":
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY not configured.")

            try:
                from langchain_google_genai import ChatGoogleGenerativeAI
            except ImportError as exc:
                raise ImportError(
                    "langchain-google-genai is required for Gemini. Install via 'pip install langchain-google-genai google-generativeai'."
                ) from exc

            return ChatGoogleGenerativeAI(
                model=self.model_name,
                temperature=temp,
                max_output_tokens=tokens,
                google_api_key=api_key,
            )

        if self.model_provider == "mock":
            class _MockLLM:
                def invoke(self, messages):
                    class _MockResponse:
                        content = "Mock analysis response"

                    return _MockResponse()

                def __call__(self, messages):
                    return self.invoke(messages)

            return _MockLLM()

        raise ValueError(f"Unsupported model provider: {self.model_provider}")

    def run_chat(
        self,
        messages: list[Any],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ):
        """Execute a chat call with optional sampling overrides."""
        call_temperature = self.temperature if temperature is None else temperature
        call_tokens = self.max_tokens if max_tokens is None else max_tokens

        logger.info(
            "LLM call start provider=%s model=%s temperature=%.2f max_tokens=%s",
            self.model_provider,
            self.model_name,
            call_temperature,
            call_tokens,
        )

        try:
            llm = (
                self.llm
                if temperature is None and max_tokens is None
                else self._build_llm(temperature=temperature, max_tokens=max_tokens)
            )
            response = llm.invoke(messages)
            logger.info(
                "LLM call success provider=%s model=%s content_length=%s",
                self.model_provider,
                self.model_name,
                len(getattr(response, "content", "") or ""),
            )
            return response
        except Exception as exc:
            logger.error(
                "LLM call failed provider=%s model=%s error=%s",
                self.model_provider,
                self.model_name,
                exc,
            )
            raise

    def analyze_essay(
        self,
        essay_text: str,
        prompt: Optional[str] = None,
        enable_grammar: bool = True,
        enable_style: bool = True,
        enable_sentiment: bool = False,
        language: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Analyze learning story text and return rubric-relevant features."""
        if not essay_text or not essay_text.strip():
            raise ValueError("Learning story text cannot be empty.")

        _ = enable_sentiment  # Backward-compatible flag not used in HvA flow.
        detected_language = self._detect_language(essay_text)
        active_language = normalize_language(language or detected_language)
        basic_stats = self._get_basic_statistics(essay_text)
        structured_sections = self._extract_structured_sections(
            essay_text, detected_language
        )
        learning_signals = self._extract_learning_story_signals(
            essay_text,
            detected_language,
            sections=structured_sections,
        )

        results: Dict[str, Any] = {
            "basic_stats": basic_stats,
            "readability": self._analyze_readability(essay_text, basic_stats),
            "structure": self._analyze_structure(
                essay_text,
                learning_signals,
                structured_sections=structured_sections,
            ),
            "vocabulary": self._analyze_vocabulary(essay_text),
            "learning_story_signals": learning_signals,
            "language": active_language,
            "detected_text_language": detected_language,
        }

        if enable_grammar:
            results["grammar"] = self._analyze_grammar(
                essay_text, learning_signals, active_language
            )

        if enable_style:
            results["style"] = self._analyze_style(
                essay_text, learning_signals, active_language
            )

        retrieval_context = self._gather_retrieval_context(
            essay_text,
            prompt,
            language=detected_language,
        )
        results["retrieval_context"] = self._format_retrieval_blocks(retrieval_context)

        return results

    def _get_basic_statistics(self, text: str) -> Dict[str, float]:
        """Get basic text statistics."""
        sentences = nltk.sent_tokenize(text)
        words = nltk.word_tokenize(text)
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

        return {
            "word_count": len(words),
            "sentence_count": len(sentences),
            "paragraph_count": len(paragraphs),
            "character_count": len(text),
            "character_count_no_spaces": len(text.replace(" ", "")),
            "avg_words_per_sentence": len(words) / len(sentences) if sentences else 0,
            "avg_sentences_per_paragraph": (
                len(sentences) / len(paragraphs) if paragraphs else 0
            ),
        }

    def _analyze_readability(
        self, text: str, basic_stats: Optional[Dict[str, float]] = None
    ) -> Dict[str, float]:
        """Provide lightweight readability proxies without external NLP-heavy deps."""
        stats = basic_stats or self._get_basic_statistics(text)
        word_count = int(stats.get("word_count", 0))
        avg_words_per_sentence = float(stats.get("avg_words_per_sentence", 0.0))

        return {
            "reading_time_minutes": max(1.0, word_count / 200.0) if word_count else 0.0,
            "avg_words_per_sentence": avg_words_per_sentence,
            "readability_risk": 1.0 if avg_words_per_sentence > 30 else 0.0,
        }

    def _analyze_structure(
        self,
        text: str,
        signals: Optional[Dict[str, Any]] = None,
        structured_sections: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Analyze structure in HvA terms: context-goals-approach-evidence coverage."""
        story_signals = signals or self._extract_learning_story_signals(
            text, self._detect_language(text)
        )
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        paragraph_lengths = [len(p.split()) for p in paragraphs]

        has_context = story_signals.get("context_mentions", 0) > 0
        has_goals = story_signals.get("goal_statements", 0) > 0
        has_approach = story_signals.get("actions_count", 0) > 0
        has_evidence = (
            story_signals.get("evidence_mentions", 0) > 0
            or story_signals.get("resource_mentions", 0) > 1
            or story_signals.get("link_mentions", 0) > 0
        )

        coverage_count = sum([has_context, has_goals, has_approach, has_evidence])
        sections = structured_sections or self._extract_structured_sections(
            text, self._detect_language(text)
        )

        return {
            "paragraph_count": len(paragraphs),
            "avg_paragraph_length": (
                sum(paragraph_lengths) / len(paragraph_lengths)
                if paragraph_lengths
                else 0
            ),
            "min_paragraph_length": min(paragraph_lengths) if paragraph_lengths else 0,
            "max_paragraph_length": max(paragraph_lengths) if paragraph_lengths else 0,
            "paragraph_lengths": paragraph_lengths,
            "has_clear_introduction": has_context,
            "has_clear_conclusion": story_signals.get("reflection_mentions", 0) > 0,
            "transition_word_count": story_signals.get("planning_mentions", 0),
            "learning_story_component_coverage": coverage_count,
            "section_coverage_count": sections.get("coverage_count", 0),
            "missing_sections": sections.get("missing_sections", []),
            "sections_detected": sections.get("sections_detected", {}),
        }

    def _extract_structured_sections(self, text: str, language: str) -> Dict[str, Any]:
        """Detect rubric sections using heading patterns and paragraph cues."""
        active_language = normalize_language(language)
        section_patterns = {
            "en": {
                "context": ["context", "background", "situation"],
                "learning_goals": ["learning goals", "goals", "objective"],
                "learning_approach": ["approach", "plan", "actions", "method"],
                "substantiation": ["evidence", "sources", "substantiation"],
                "reflection": ["reflection", "lessons learned", "next steps"],
            },
            "nl": {
                "context": ["context", "situatie", "achtergrond"],
                "learning_goals": ["leerdoelen", "doelen", "leerdoel"],
                "learning_approach": ["aanpak", "plan", "acties", "methode"],
                "substantiation": ["onderbouwing", "bewijs", "bronnen"],
                "reflection": ["reflectie", "terugblik", "vervolgstap"],
            },
        }
        active_patterns = section_patterns.get(active_language, section_patterns["en"])

        lines = [line.strip() for line in text.splitlines() if line.strip()]
        headings = [line.lower().strip("#:- ") for line in lines if len(line) <= 90]
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

        sections_detected: Dict[str, bool] = {}
        paragraph_matches: Dict[str, int] = {}

        for section, patterns in active_patterns.items():
            heading_match = any(
                any(re.search(rf"\b{re.escape(pattern)}\b", heading) for pattern in patterns)
                for heading in headings
            )

            paragraph_match = sum(
                1
                for paragraph in paragraphs
                if any(
                    re.search(rf"\b{re.escape(pattern)}\b", paragraph.lower())
                    for pattern in patterns
                )
            )

            sections_detected[section] = bool(heading_match or paragraph_match > 0)
            paragraph_matches[section] = paragraph_match

        coverage_count = sum(1 for found in sections_detected.values() if found)
        missing_sections = [
            section for section, found in sections_detected.items() if not found
        ]

        return {
            "coverage_count": coverage_count,
            "missing_sections": missing_sections,
            "sections_detected": sections_detected,
            "section_paragraph_matches": paragraph_matches,
        }

    def _analyze_vocabulary(self, text: str) -> Dict[str, Any]:
        """Lightweight vocabulary summary for compatibility with grading fallbacks."""
        words = [w for w in nltk.word_tokenize(text.lower()) if w.isalpha()]
        unique_words = set(words)

        lexical_diversity = len(unique_words) / len(words) if words else 0
        avg_word_length = (
            sum(len(word) for word in words) / len(words) if words else 0
        )

        return {
            "total_words": len(words),
            "unique_words": len(unique_words),
            "lexical_diversity": lexical_diversity,
            "avg_word_length": avg_word_length,
            "complex_word_count": 0,
            "complex_word_ratio": 0,
        }

    def _analyze_grammar(
        self,
        text: str,
        signals: Optional[Dict[str, Any]] = None,
        language: Optional[str] = None,
    ) -> Dict[str, Any]:
        """HvA-oriented clarity checks (not full grammar scoring)."""
        active_language = normalize_language(language or self._detect_language(text))
        story_signals = signals or self._extract_learning_story_signals(
            text, active_language
        )
        grammar_issues: List[Dict[str, Any]] = []

        sentences = nltk.sent_tokenize(text)
        for i, sentence in enumerate(sentences):
            words = len(sentence.split())
            if words > 35:
                long_sentence_description = (
                    f"Zin heeft {words} woorden. Splits lange zinnen in kleinere stappen."
                    if active_language == "nl"
                    else (
                        f"Sentence has {words} words. Split long ideas into smaller steps."
                    )
                )
                grammar_issues.append(
                    {
                        "type": "Long Sentence",
                        "sentence_number": i + 1,
                        "description": long_sentence_description,
                        "severity": "medium",
                    }
                )

        if story_signals.get("goal_statements", 0) == 0:
            missing_goal_description = (
                "Neem minstens een expliciete leerdoelformulering op."
                if active_language == "nl"
                else "Include at least one explicit learning goal statement."
            )
            grammar_issues.append(
                {
                    "type": "Missing Goal Formulation",
                    "description": missing_goal_description,
                    "severity": "high",
                }
            )

        if story_signals.get("actions_count", 0) == 0:
            missing_actions_description = (
                "Beschrijf concrete stappen, experimenten of taken."
                if active_language == "nl"
                else "Describe concrete steps, experiments, or tasks."
            )
            grammar_issues.append(
                {
                    "type": "Missing Concrete Actions",
                    "description": missing_actions_description,
                    "severity": "high",
                }
            )

        return {
            "grammar_issues": grammar_issues,
            "issue_count": len(grammar_issues),
        }

    def _analyze_style(
        self,
        text: str,
        signals: Optional[Dict[str, Any]] = None,
        language: Optional[str] = None,
    ) -> Dict[str, Any]:
        """HvA-oriented style analysis focused on actionability and specificity."""
        active_language = normalize_language(language or self._detect_language(text))
        story_signals = signals or self._extract_learning_story_signals(
            text, active_language
        )
        sentences = nltk.sent_tokenize(text)
        sentence_lengths = [len(sentence.split()) for sentence in sentences]

        actions_count = story_signals.get("actions_count", 0)
        resources = story_signals.get("resource_mentions", 0)

        style_issues: List[Dict[str, Any]] = []
        if actions_count < 2:
            low_action_description = (
                "Voeg stapsgewijze acties toe om je leerroute concreet te maken."
                if active_language == "nl"
                else "Add step-by-step actions to make your learning approach concrete."
            )
            style_issues.append(
                {
                    "type": "Low Action Specificity",
                    "description": low_action_description,
                    "severity": "medium",
                }
            )

        if resources < 1 and story_signals.get("link_mentions", 0) < 1:
            missing_source_description = (
                "Noem leerbronnen (artikelen, documentatie, video's, mentors) of voeg links toe."
                if active_language == "nl"
                else "Name learning resources (articles, docs, videos, mentors) or add links."
            )
            style_issues.append(
                {
                    "type": "Missing Source Strategy",
                    "description": missing_source_description,
                    "severity": "medium",
                }
            )

        return {
            "sentence_variety_score": float(len(set(sentence_lengths)))
            if sentence_lengths
            else 0.0,
            "sentence_starter_variety": 0.0,
            "avg_sentence_length": (
                sum(sentence_lengths) / len(sentence_lengths) if sentence_lengths else 0
            ),
            "sophisticated_word_ratio": 0.0,
            "style_issues": style_issues,
        }

    def _extract_learning_story_signals(
        self,
        text: str,
        language: str = "en",
        sections: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Extract HvA learning story signals (context, goals, plan, evidence)."""
        active_language = normalize_language(language)
        lowered = text.lower()

        def _count_keywords(keywords: List[str]) -> int:
            total = 0
            for keyword in keywords:
                escaped = re.escape(keyword.lower().strip())
                if not escaped:
                    continue

                # Prefix matching for single tokens keeps support for stems like "prototyp".
                pattern = (
                    rf"\b{escaped}\b"
                    if " " in keyword
                    else rf"\b{escaped}\w*\b"
                )
                total += len(re.findall(pattern, lowered))
            return total

        goal_patterns_by_language = {
            "nl": [
                r"\bals\s+[^.,\n]+?\s+wil\s+ik\s",
                r"\bik\s+wil\s+leren\b",
                r"\bik\s+wil\s+me\s+verbeteren\b",
                r"\bleerdoel\b",
            ],
            "en": [
                r"\bas\s+a\s+student[^.,\n]+?i\s+want\s+to\s+learn\b",
                r"\bi\s+want\s+to\s+learn\b",
                r"\bmy\s+learning\s+goal\b",
                r"\blearning\s+goal\b",
            ],
        }

        keyword_sets_by_language = {
            "nl": {
                "success_criteria": [
                    "succescriter",
                    "acceptatiecriter",
                    "definition of done",
                    "klaar wanneer",
                    "done wanneer",
                    "behaald wanneer",
                ],
                "context": [
                    "context",
                    "situatie",
                    "achtergrond",
                    "probleem",
                    "vraagstuk",
                    "opdracht",
                    "project",
                    "rol",
                    "stakeholder",
                    "klant",
                    "team",
                    "omgeving",
                    "resultaat",
                    "casus",
                ],
                "stakeholder": [
                    "stakeholder",
                    "stakeholders",
                    "klant",
                    "opdrachtgever",
                    "gebruiker",
                    "gebruikers",
                ],
                "deliverable": [
                    "oplevering",
                    "artefact",
                    "artefacten",
                    "prototype",
                    "demo",
                    "rapport",
                    "verslag",
                    "bewijs",
                    "resultaat",
                    "product",
                ],
                "actions": [
                    "plan",
                    "stap",
                    "stappen",
                    "aanpak",
                    "experiment",
                    "experimenten",
                    "test",
                    "testen",
                    "onderzoek",
                    "onderzoeken",
                    "interview",
                    "oefenen",
                    "implement",
                    "bouwen",
                    "prototyp",
                    "uitwerken",
                    "uitproberen",
                ],
                "resources": [
                    "bron",
                    "bronnen",
                    "artikel",
                    "artikelen",
                    "paper",
                    "boek",
                    "literatuur",
                    "video",
                    "tutorial",
                    "cursus",
                    "mentor",
                    "coach",
                    "docent",
                    "lectoraat",
                    "kennisbank",
                    "documentatie",
                    "richtlijn",
                    "best practice",
                    "voorbeeld",
                ],
                "evidence": [
                    "bewijs",
                    "onderbouwing",
                    "reflectie",
                    "feedback",
                    "referentie",
                    "referenties",
                    "bronvermelding",
                    "bijlage",
                    "appendix",
                    "logboek",
                    "portfolio",
                    "assessment",
                    "rubric",
                ],
                "reflection": [
                    "reflectie",
                    "terugblik",
                    "wat ging goed",
                    "wat kan beter",
                    "geleerd",
                    "leerpunt",
                    "leerpunten",
                ],
                "planning": [
                    "planning",
                    "tijd",
                    "tijdpad",
                    "sprint",
                    "week",
                    "deadline",
                    "roadmap",
                    "volgende stap",
                ],
            },
            "en": {
                "success_criteria": [
                    "acceptance criteria",
                    "success criteria",
                    "definition of done",
                    "done when",
                    "completed when",
                ],
                "context": [
                    "context",
                    "background",
                    "situation",
                    "problem",
                    "challenge",
                    "assignment",
                    "project",
                    "role",
                    "stakeholder",
                    "client",
                    "team",
                    "environment",
                    "outcome",
                    "case",
                ],
                "stakeholder": [
                    "stakeholder",
                    "stakeholders",
                    "client",
                    "customer",
                    "users",
                    "user",
                ],
                "deliverable": [
                    "deliverable",
                    "artifact",
                    "artefact",
                    "prototype",
                    "demo",
                    "report",
                    "evidence",
                    "outcome",
                    "result",
                    "product",
                ],
                "actions": [
                    "plan",
                    "step",
                    "steps",
                    "approach",
                    "experiment",
                    "experiments",
                    "test",
                    "testing",
                    "research",
                    "interview",
                    "practice",
                    "implement",
                    "build",
                    "prototype",
                    "iterate",
                    "validate",
                ],
                "resources": [
                    "source",
                    "sources",
                    "article",
                    "articles",
                    "paper",
                    "book",
                    "literature",
                    "video",
                    "tutorial",
                    "course",
                    "mentor",
                    "coach",
                    "teacher",
                    "knowledge base",
                    "documentation",
                    "guideline",
                    "best practice",
                    "example",
                ],
                "evidence": [
                    "evidence",
                    "substantiation",
                    "reflection",
                    "feedback",
                    "reference",
                    "references",
                    "citation",
                    "appendix",
                    "logbook",
                    "portfolio",
                    "assessment",
                    "rubric",
                ],
                "reflection": [
                    "reflection",
                    "lessons learned",
                    "what went well",
                    "what could be better",
                    "learned",
                    "learning point",
                    "learning points",
                ],
                "planning": [
                    "planning",
                    "timeline",
                    "timeframe",
                    "sprint",
                    "week",
                    "deadline",
                    "roadmap",
                    "next step",
                    "next steps",
                ],
            },
        }

        active_goal_patterns = goal_patterns_by_language.get(
            active_language, goal_patterns_by_language["en"]
        )
        active_keyword_sets = keyword_sets_by_language.get(
            active_language, keyword_sets_by_language["en"]
        )

        goal_statements = sum(
            len(re.findall(pattern, lowered)) for pattern in active_goal_patterns
        )

        success_criteria_mentions = _count_keywords(
            active_keyword_sets["success_criteria"]
        )

        context_mentions = _count_keywords(active_keyword_sets["context"])

        stakeholder_mentions = _count_keywords(active_keyword_sets["stakeholder"])

        deliverable_mentions = _count_keywords(active_keyword_sets["deliverable"])

        actions_count = _count_keywords(active_keyword_sets["actions"])

        resource_mentions = _count_keywords(active_keyword_sets["resources"])

        evidence_mentions = _count_keywords(active_keyword_sets["evidence"])

        reflection_mentions = _count_keywords(active_keyword_sets["reflection"])

        planning_mentions = _count_keywords(active_keyword_sets["planning"])

        link_mentions = len(re.findall(r"https?://", text, flags=re.IGNORECASE))
        section_data = sections or self._extract_structured_sections(text, active_language)
        sections_detected = section_data.get("sections_detected", {})

        return {
            "goal_statements": goal_statements,
            "success_criteria_mentions": success_criteria_mentions,
            "context_mentions": context_mentions,
            "stakeholder_mentions": stakeholder_mentions,
            "deliverable_mentions": deliverable_mentions,
            "actions_count": actions_count,
            "resource_mentions": resource_mentions,
            "evidence_mentions": evidence_mentions,
            "reflection_mentions": reflection_mentions,
            "planning_mentions": planning_mentions,
            "link_mentions": link_mentions,
            "section_coverage_count": section_data.get("coverage_count", 0),
            "missing_core_sections": section_data.get("missing_sections", []),
            "sections_detected": sections_detected,
            "has_minimum_sources": resource_mentions >= 2 or link_mentions >= 1,
        }
