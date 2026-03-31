"""
Learning Story Analyzer Module

Core learning story analysis functionality using AI models.
"""

import os
import re
import nltk
import textstat
import logging
from typing import Dict, List, Optional, Any
from nltk.corpus import stopwords
from langchain_core.messages import HumanMessage, SystemMessage
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import spacy

logger = logging.getLogger(__name__)

# Download required NLTK data
try:
    nltk.data.find("tokenizers/punkt_tab")
except LookupError:
    try:
        nltk.download("punkt_tab")
    except:
        nltk.download("punkt")

try:
    nltk.data.find("corpora/stopwords")
except LookupError:
    nltk.download("stopwords")


class EssayAnalyzer:
    """
    Main learning story analysis class that handles AI-powered text analysis.
    """

    def __init__(
        self,
        model_provider: str = "gemini",
        model_name: str = "gemini-1.5-pro",
        temperature: float = 0.3,
        max_tokens: int = 2000,
        language: str = "en",
        retriever: Optional[Any] = None,
        retrieval_top_k: int = 3,
    ):
        """
        Initialize the learning story analyzer.

        Args:
            model_provider: AI model provider ('gemini' or 'mock')
            model_name: Specific model to use
            temperature: Model temperature for response generation
            max_tokens: Maximum tokens for model responses
            language: Language code for analysis and generated feedback ('en' or 'nl')
        """
        self.model_provider = model_provider
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.language = self._normalize_language(language)
        self.retriever = retriever
        self.retrieval_top_k = retrieval_top_k
        self.english_stopwords = set(stopwords.words("english"))
        self.dutch_stopwords = set(stopwords.words("dutch"))

        # Initialize AI model
        self._initialize_model()

        # Initialize NLP tools
        self.sentiment_analyzer = SentimentIntensityAnalyzer()

        # Load spaCy model for advanced NLP
        try:
            if self.language == "nl":
                self.nlp = spacy.load("nl_core_news_sm")
            else:
                self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("Warning: spaCy model not found for selected language. Some features may be limited.")
            self.nlp = None

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
        """Detect whether essay text is primarily English or Dutch."""
        words = [w.lower() for w in nltk.word_tokenize(text) if w.isalpha()]
        if not words:
            return "en"

        english_hits = sum(1 for w in words if w in self.english_stopwords)
        dutch_hits = sum(1 for w in words if w in self.dutch_stopwords)

        # Additional tie-breaker tokens for short essays or sparse stopword overlap.
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

    def _gather_retrieval_context(self, essay_text: str, prompt: Optional[str]) -> Dict[str, Any]:
        """Pull top matches from the internal vector store."""
        query_text = f"{prompt or ''}\n\n{essay_text}" if prompt else essay_text
        context: Dict[str, Any] = {"vector_hits": [], "notes": []}

        if self.retriever:
            try:
                context["vector_hits"] = self.retriever.search(query_text, top_k=self.retrieval_top_k)
            except Exception as exc:
                context["notes"].append(f"Vector search unavailable: {exc}")

        return context

    def _format_retrieval_blocks(self, retrieval_context: Dict[str, Any]) -> Dict[str, str]:
        """Pre-format retrieval hits for prompt injection."""
        vector_block = ""

        if retrieval_context.get("vector_hits") and hasattr(self.retriever, "build_context_block"):
            vector_block = self.retriever.build_context_block(retrieval_context.get("vector_hits", []))

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
        elif self.model_provider == "mock":
            # Lightweight mock for tests that should not call external LLMs.
            class _MockLLM:
                def __call__(self, messages):
                    class _MockResponse:
                        content = "Mock analysis response"

                    return _MockResponse()

            return _MockLLM()
        else:
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
            llm = self.llm if temperature is None and max_tokens is None else self._build_llm(
                temperature=temperature, max_tokens=max_tokens
            )
            response = llm(messages)
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
        enable_sentiment: bool = True,
        language: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Perform comprehensive learning story analysis.

        Args:
            essay_text: The learning story content to analyze
            prompt: Optional learning story prompt/context
            enable_grammar: Whether to perform grammar analysis
            enable_style: Whether to perform style analysis
            enable_sentiment: Whether to perform sentiment analysis
            language: Reserved for backward compatibility. Essay language is auto-detected.

        Returns:
            Dictionary containing analysis results
        """
        if not essay_text or not essay_text.strip():
            raise ValueError("Learning story text cannot be empty.")

        active_language = self._detect_language(essay_text)

        results = {
            "basic_stats": self._get_basic_statistics(essay_text),
            "readability": self._analyze_readability(essay_text),
            "structure": self._analyze_structure(essay_text, active_language),
            "vocabulary": self._analyze_vocabulary(essay_text),
        }

        if enable_grammar:
            results["grammar"] = self._analyze_grammar(essay_text)

        if enable_style:
            results["style"] = self._analyze_style(essay_text)

        if enable_sentiment:
            results["sentiment"] = self._analyze_sentiment(essay_text)

        retrieval_context = self._gather_retrieval_context(essay_text, prompt)
        retrieval_context = self._format_retrieval_blocks(retrieval_context)

        # AI-powered content analysis
        results["content_analysis"] = self._ai_content_analysis(
            essay_text, prompt, active_language, retrieval_context
        )
        results["learning_story_signals"] = self._extract_learning_story_signals(
            essay_text, active_language
        )
        results["retrieval_context"] = retrieval_context
        results["language"] = active_language

        return results

    def _get_basic_statistics(self, text: str) -> Dict[str, int]:
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
            "avg_sentences_per_paragraph": len(sentences) / len(paragraphs)
            if paragraphs
            else 0,
        }

    def _analyze_readability(self, text: str) -> Dict[str, float]:
        """Analyze text readability using various metrics."""
        return {
            "flesch_reading_ease": textstat.flesch_reading_ease(text),
            "flesch_kincaid_grade": textstat.flesch_kincaid_grade(text),
            "gunning_fog": textstat.gunning_fog(text),
            "automated_readability_index": textstat.automated_readability_index(text),
            "coleman_liau_index": textstat.coleman_liau_index(text),
            "reading_time_minutes": textstat.reading_time(text, ms_per_char=14.69),
        }

    def _analyze_structure(self, text: str, language: str = "en") -> Dict[str, Any]:
        """Analyze essay structure and organization."""
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

        # Analyze paragraph lengths
        paragraph_lengths = [len(p.split()) for p in paragraphs]

        # Check for introduction and conclusion patterns
        has_intro = self._check_introduction_patterns(
            paragraphs[0] if paragraphs else "", language
        )
        has_conclusion = self._check_conclusion_patterns(
            paragraphs[-1] if paragraphs else "", language
        )

        # Analyze transitions
        transition_words = self._count_transition_words(text, language)

        return {
            "paragraph_count": len(paragraphs),
            "avg_paragraph_length": sum(paragraph_lengths) / len(paragraph_lengths)
            if paragraph_lengths
            else 0,
            "min_paragraph_length": min(paragraph_lengths) if paragraph_lengths else 0,
            "max_paragraph_length": max(paragraph_lengths) if paragraph_lengths else 0,
            "has_clear_introduction": has_intro,
            "has_clear_conclusion": has_conclusion,
            "transition_word_count": transition_words,
            "paragraph_lengths": paragraph_lengths,
        }

    def _analyze_vocabulary(self, text: str) -> Dict[str, Any]:
        """Analyze vocabulary complexity and diversity."""
        words = nltk.word_tokenize(text.lower())
        words = [word for word in words if word.isalpha()]

        unique_words = set(words)

        # Calculate lexical diversity
        lexical_diversity = len(unique_words) / len(words) if words else 0

        # Analyze word lengths
        word_lengths = [len(word) for word in words]
        avg_word_length = sum(word_lengths) / len(word_lengths) if word_lengths else 0

        # Count complex words (3+ syllables)
        complex_words = [word for word in words if textstat.syllable_count(word) >= 3]

        return {
            "total_words": len(words),
            "unique_words": len(unique_words),
            "lexical_diversity": lexical_diversity,
            "avg_word_length": avg_word_length,
            "complex_word_count": len(complex_words),
            "complex_word_ratio": len(complex_words) / len(words) if words else 0,
        }

    def _analyze_grammar(self, text: str) -> Dict[str, Any]:
        """Analyze grammar and mechanics using TextBlob and spaCy."""
        blob = TextBlob(text)

        # Basic grammar check with TextBlob
        grammar_issues = []

        # Check for common issues
        sentences = nltk.sent_tokenize(text)

        for i, sentence in enumerate(sentences):
            # Check sentence length
            words = len(sentence.split())
            if words > 30:
                grammar_issues.append(
                    {
                        "type": "Long Sentence",
                        "sentence_number": i + 1,
                        "description": f"Sentence has {words} words. Consider breaking it down.",
                        "severity": "medium",
                    }
                )
            elif words < 5:
                grammar_issues.append(
                    {
                        "type": "Short Sentence",
                        "sentence_number": i + 1,
                        "description": f"Very short sentence ({words} words). Consider expanding.",
                        "severity": "low",
                    }
                )

            # Check for passive voice (basic detection)
            if self._contains_passive_voice(sentence):
                grammar_issues.append(
                    {
                        "type": "Passive Voice",
                        "sentence_number": i + 1,
                        "description": "Consider using active voice for stronger writing.",
                        "severity": "medium",
                    }
                )

        # Advanced analysis with spaCy if available
        if self.nlp:
            doc = self.nlp(text)

            # Check for sentence fragments
            for sent in doc.sents:
                if not any(token.dep_ == "ROOT" for token in sent):
                    grammar_issues.append(
                        {
                            "type": "Sentence Fragment",
                            "description": f"Possible sentence fragment: '{sent.text[:50]}...'",
                            "severity": "high",
                        }
                    )

        return {
            "grammar_issues": grammar_issues,
            "issue_count": len(grammar_issues),
            "polarity": blob.sentiment.polarity,
            "subjectivity": blob.sentiment.subjectivity,
        }

    def _analyze_style(self, text: str) -> Dict[str, Any]:
        """Analyze writing style and voice."""
        # Analyze sentence variety
        sentences = nltk.sent_tokenize(text)
        sentence_lengths = [len(sentence.split()) for sentence in sentences]

        # Calculate sentence length variance
        if len(sentence_lengths) > 1:
            avg_length = sum(sentence_lengths) / len(sentence_lengths)
            variance = sum((x - avg_length) ** 2 for x in sentence_lengths) / len(
                sentence_lengths
            )
        else:
            variance = 0

        # Check for repetitive sentence starters
        starters = [
            sentence.split()[0].lower() if sentence.split() else ""
            for sentence in sentences
        ]
        starter_variety = len(set(starters)) / len(starters) if starters else 0

        # Analyze word choice sophistication
        words = nltk.word_tokenize(text.lower())
        sophisticated_words = [
            word for word in words if len(word) > 6 and word.isalpha()
        ]

        return {
            "sentence_variety_score": variance,
            "sentence_starter_variety": starter_variety,
            "avg_sentence_length": sum(sentence_lengths) / len(sentence_lengths)
            if sentence_lengths
            else 0,
            "sophisticated_word_ratio": len(sophisticated_words) / len(words)
            if words
            else 0,
            "style_issues": self._identify_style_issues(text),
        }

    def _analyze_sentiment(self, text: str) -> Dict[str, float]:
        """Analyze sentiment and emotional tone."""
        scores = self.sentiment_analyzer.polarity_scores(text)

        # Determine overall tone
        if scores["compound"] >= 0.05:
            tone = "positive"
        elif scores["compound"] <= -0.05:
            tone = "negative"
        else:
            tone = "neutral"

        return {
            "positive": scores["pos"],
            "negative": scores["neg"],
            "neutral": scores["neu"],
            "compound": scores["compound"],
            "overall_tone": tone,
        }

    def _extract_learning_story_signals(
        self, text: str, language: str = "en"
    ) -> Dict[str, Any]:
        """Extract HvA learning story signals (context, goals, plan, evidence)."""
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
        goal_statements = sum(len(re.findall(pattern, lowered)) for pattern in goal_patterns)

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
        stakeholder_mentions = _count_keywords(["stakeholder", "stakeholders", "klant", "opdrachtgever"])
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

    def _ai_content_analysis(
        self,
        text: str,
        prompt: Optional[str] = None,
        language: str = "en",
        retrieval_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, str]:
        """Use AI to analyze content quality and relevance, grounded in retrieval context."""
        try:
            language_name = "Dutch" if language == "nl" else "English"

            vector_block = ""
            if retrieval_context:
                vector_block = retrieval_context.get("vector_block", "")

            system_message = f"""You are an expert essay evaluator. First, read the internal learning stories (highest priority) and ground your analysis in them.

Context priority:
1) Internal learning stories (treat as authoritative guidance; align feedback to these):
{vector_block or 'None retrieved; rely on the student text.'}

Use rubric and policies as guidelines, not rigid rules—adapt pragmatically to the student's situation and keep advice actionable. Focus on content quality, clarity, logic, evidence, and coherence. Return the full analysis in {language_name}."""

            user_message = f"Essay to analyze:\n\n{text}"

            if prompt:
                user_message = f"Essay prompt: {prompt}\n\n{user_message}"

            messages = [
                SystemMessage(content=system_message),
                HumanMessage(content=user_message),
            ]

            response = self.run_chat(messages)

            return {
                "ai_analysis": response.content,
                "analysis_provider": f"{self.model_provider}_{self.model_name}",
                "workspace_attribution": "HvA Feedback Agent",
            }

        except Exception as e:
            return {
                "ai_analysis": f"Error in AI analysis: {str(e)}",
                "analysis_provider": "error",
                "workspace_attribution": "HvA Feedback Agent",
            }

    def _check_introduction_patterns(self, first_paragraph: str, language: str = "en") -> bool:
        """Check if the first paragraph has introduction characteristics."""
        intro_patterns_by_language = {
            "en": [
                r"\b(in this essay|this essay will|i will discuss|this paper examines)\b",
                r"\b(introduction|background|context)\b",
                r"\b(thesis|argument|main point)\b",
            ],
            "nl": [
                r"\b(in dit essay|in deze tekst|ik zal bespreken|dit paper onderzoekt)\b",
                r"\b(inleiding|achtergrond|context)\b",
                r"\b(stelling|argument|hoofdpunt)\b",
            ],
        }

        intro_patterns = intro_patterns_by_language.get(language, intro_patterns_by_language["en"])

        text_lower = first_paragraph.lower()
        return any(re.search(pattern, text_lower) for pattern in intro_patterns)

    def _check_conclusion_patterns(self, last_paragraph: str, language: str = "en") -> bool:
        """Check if the last paragraph has conclusion characteristics."""
        conclusion_patterns_by_language = {
            "en": [
                r"\b(in conclusion|to conclude|in summary|finally)\b",
                r"\b(therefore|thus|hence|consequently)\b",
                r"\b(overall|ultimately|in the end)\b",
            ],
            "nl": [
                r"\b(concluderend|tot slot|samenvattend|ten slotte)\b",
                r"\b(daarom|dus|hierdoor|bijgevolg)\b",
                r"\b(over het algemeen|uiteindelijk|aan het einde)\b",
            ],
        }

        conclusion_patterns = conclusion_patterns_by_language.get(
            language, conclusion_patterns_by_language["en"]
        )

        text_lower = last_paragraph.lower()
        return any(re.search(pattern, text_lower) for pattern in conclusion_patterns)

    def _count_transition_words(self, text: str, language: str = "en") -> int:
        """Count transition words and phrases."""
        transitions_by_language = {
            "en": [
                "however",
                "therefore",
                "furthermore",
                "moreover",
                "additionally",
                "consequently",
                "nevertheless",
                "nonetheless",
                "meanwhile",
                "first",
                "second",
                "third",
                "finally",
                "next",
                "then",
                "for example",
                "for instance",
                "in contrast",
                "on the other hand",
                "similarly",
                "likewise",
                "in addition",
                "as a result",
            ],
            "nl": [
                "echter",
                "daarom",
                "verder",
                "bovendien",
                "daarnaast",
                "bijgevolg",
                "niettemin",
                "ondertussen",
                "ten eerste",
                "ten tweede",
                "ten derde",
                "ten slotte",
                "vervolgens",
                "daarna",
                "bijvoorbeeld",
                "daarentegen",
                "aan de andere kant",
                "eveneens",
                "ook",
                "als gevolg",
            ],
        }

        transitions = transitions_by_language.get(language, transitions_by_language["en"])

        text_lower = text.lower()
        count = 0

        for transition in transitions:
            count += text_lower.count(transition)

        return count

    def _contains_passive_voice(self, sentence: str) -> bool:
        """Basic passive voice detection."""
        passive_patterns = [
            r"\b(was|were|is|are|been|being)\s+\w+ed\b",
            r"\b(was|were|is|are|been|being)\s+\w+en\b",
            # Capture common irregular participles that appear with a by-phrase.
            r"\b(am|is|are|was|were|be|been|being)\s+\w+\s+by\b",
        ]

        return any(re.search(pattern, sentence.lower()) for pattern in passive_patterns)

    def _identify_style_issues(self, text: str) -> List[Dict[str, str]]:
        """Identify common style issues."""
        issues = []

        # Check for overuse of certain words
        words = nltk.word_tokenize(text.lower())
        word_freq = nltk.FreqDist(words)

        # Common overused words
        overused_words = ["very", "really", "quite", "just", "actually", "basically"]

        for word in overused_words:
            if word_freq[word] > 3:
                issues.append(
                    {
                        "type": "Overused Word",
                        "description": f"The word '{word}' appears {word_freq[word]} times. Consider varying your vocabulary.",
                        "severity": "medium",
                    }
                )

        # Check for clichés
        cliches = [
            "at the end of the day",
            "think outside the box",
            "in today's society",
            "since the dawn of time",
        ]

        text_lower = text.lower()
        for cliche in cliches:
            if cliche in text_lower:
                issues.append(
                    {
                        "type": "Cliché",
                        "description": f"Consider replacing the cliché '{cliche}' with more original language.",
                        "severity": "low",
                    }
                )

        return issues
