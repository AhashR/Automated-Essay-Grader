import logging
import os
import re
from typing import Any, Dict, List, Optional

import nltk
from nltk.corpus import stopwords

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
    ):
        self.model_provider = model_provider
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.language = self._normalize_language(language)
        self.retriever = retriever
        self.retrieval_top_k = retrieval_top_k
        self.english_stopwords = set(stopwords.words("english"))
        self.dutch_stopwords = set(stopwords.words("dutch"))

        self._initialize_model()

    def _normalize_language(self, language: str) -> str:
        """Normalize language inputs to supported codes."""
        normalized = (language or "en").strip().lower()
        aliases = {
            "english": "en",
            "eng": "en",
            "nederlands": "nl",
            "dutch": "nl",
            "nl_nl": "nl",
            "en_us": "en",
            "en_gb": "en",
        }
        normalized = aliases.get(normalized, normalized)
        return normalized if normalized in {"en", "nl"} else "en"

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
        self, essay_text: str, prompt: Optional[str]
    ) -> Dict[str, Any]:
        """Pull top matches from the internal vector store."""
        query_text = f"{prompt or ''}\n\n{essay_text}" if prompt else essay_text
        context: Dict[str, Any] = {"vector_hits": [], "notes": []}

        if self.retriever:
            try:
                context["vector_hits"] = self.retriever.search(
                    query_text, top_k=self.retrieval_top_k
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
        _ = language  # Reserved for backward compatibility.

        detected_language = self._detect_language(essay_text)
        basic_stats = self._get_basic_statistics(essay_text)
        learning_signals = self._extract_learning_story_signals(
            essay_text, detected_language
        )

        results: Dict[str, Any] = {
            "basic_stats": basic_stats,
            "readability": self._analyze_readability(essay_text, basic_stats),
            "structure": self._analyze_structure(essay_text, learning_signals),
            "vocabulary": self._analyze_vocabulary(essay_text),
            "learning_story_signals": learning_signals,
            "language": detected_language,
        }

        if enable_grammar:
            results["grammar"] = self._analyze_grammar(essay_text, learning_signals)

        if enable_style:
            results["style"] = self._analyze_style(essay_text, learning_signals)

        retrieval_context = self._gather_retrieval_context(essay_text, prompt)
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
        self, text: str, signals: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Analyze structure in HvA terms: context-goals-approach-evidence coverage."""
        story_signals = signals or self._extract_learning_story_signals(text)
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
        self, text: str, signals: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """HvA-oriented clarity checks (not full grammar scoring)."""
        story_signals = signals or self._extract_learning_story_signals(text)
        grammar_issues: List[Dict[str, Any]] = []

        sentences = nltk.sent_tokenize(text)
        for i, sentence in enumerate(sentences):
            words = len(sentence.split())
            if words > 35:
                grammar_issues.append(
                    {
                        "type": "Long Sentence",
                        "sentence_number": i + 1,
                        "description": (
                            f"Sentence has {words} words. Split long ideas into smaller steps."
                        ),
                        "severity": "medium",
                    }
                )

        if story_signals.get("goal_statements", 0) == 0:
            grammar_issues.append(
                {
                    "type": "Missing Goal Formulation",
                    "description": (
                        "Include at least one explicit learning goal statement."
                    ),
                    "severity": "high",
                }
            )

        if story_signals.get("actions_count", 0) == 0:
            grammar_issues.append(
                {
                    "type": "Missing Concrete Actions",
                    "description": "Describe concrete steps, experiments, or tasks.",
                    "severity": "high",
                }
            )

        return {
            "grammar_issues": grammar_issues,
            "issue_count": len(grammar_issues),
        }

    def _analyze_style(
        self, text: str, signals: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """HvA-oriented style analysis focused on actionability and specificity."""
        story_signals = signals or self._extract_learning_story_signals(text)
        sentences = nltk.sent_tokenize(text)
        sentence_lengths = [len(sentence.split()) for sentence in sentences]

        actions_count = story_signals.get("actions_count", 0)
        resources = story_signals.get("resource_mentions", 0)

        style_issues: List[Dict[str, Any]] = []
        if actions_count < 2:
            style_issues.append(
                {
                    "type": "Low Action Specificity",
                    "description": (
                        "Add step-by-step actions to make your learning approach concrete."
                    ),
                    "severity": "medium",
                }
            )

        if resources < 1 and story_signals.get("link_mentions", 0) < 1:
            style_issues.append(
                {
                    "type": "Missing Source Strategy",
                    "description": (
                        "Name learning resources (articles, docs, videos, mentors) or add links."
                    ),
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
        self, text: str, language: str = "en"
    ) -> Dict[str, Any]:
        """Extract HvA learning story signals (context, goals, plan, evidence)."""
        _ = language
        lowered = text.lower()

        def _count_keywords(keywords: List[str]) -> int:
            return sum(lowered.count(keyword) for keyword in keywords)

        goal_patterns = [
            r"\bals\s+[^.,\n]+?\s+wil\s+ik\s",
            r"\bik\s+wil\s+leren\b",
            r"\bas\s+a\s+student[^.,\n]+?i\s+want\s+to\s+learn\b",
            r"\bi\s+want\s+to\s+learn\b",
            r"\bals\s+student[^.,\n]+?wil\s+ik\b",
        ]
        goal_statements = sum(
            len(re.findall(pattern, lowered)) for pattern in goal_patterns
        )

        success_criteria_mentions = _count_keywords(
            [
                "succescriter",
                "acceptatiecriter",
                "definition of done",
                "klaar wanneer",
                "done wanneer",
                "behaald wanneer",
                "acceptance criteria",
                "success criteria",
            ]
        )

        context_mentions = _count_keywords(
            [
                "context",
                "situatie",
                "problem",
                "probleem",
                "opdracht",
                "assignment",
                "project",
                "rol",
                "role",
                "stakeholder",
                "klant",
                "team",
                "omgeving",
                "resultaat",
            ]
        )

        stakeholder_mentions = _count_keywords(
            ["stakeholder", "stakeholders", "klant", "opdrachtgever"]
        )

        deliverable_mentions = _count_keywords(
            [
                "deliverable",
                "oplevering",
                "artefact",
                "artefacten",
                "artifact",
                "prototype",
                "demo",
                "rapport",
                "verslag",
                "bewijs",
                "evidence",
            ]
        )

        actions_count = _count_keywords(
            [
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
            ]
        )

        resource_mentions = _count_keywords(
            [
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
                "knowledge base",
                "documentatie",
                "guideline",
                "best practice",
                "voorbeeld",
            ]
        )

        evidence_mentions = _count_keywords(
            [
                "bewijs",
                "onderbouwing",
                "reflectie",
                "feedback",
                "referentie",
                "referenties",
                "citation",
                "bronvermelding",
                "bijlage",
                "appendix",
                "logboek",
                "portfolio",
                "assessment",
                "rubric",
            ]
        )

        reflection_mentions = _count_keywords(
            [
                "reflectie",
                "terugblik",
                "lessons learned",
                "wat ging goed",
                "wat kan beter",
                "what went well",
                "what could be better",
            ]
        )

        planning_mentions = _count_keywords(
            [
                "planning",
                "tijd",
                "tijdpad",
                "sprint",
                "week",
                "deadline",
                "roadmap",
                "volgende stap",
            ]
        )

        link_mentions = len(re.findall(r"https?://", text, flags=re.IGNORECASE))

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
            "has_minimum_sources": resource_mentions >= 2 or link_mentions >= 1,
        }
