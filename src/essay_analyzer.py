"""
Essay Analyzer Module
From Hasif's Workspace

Core essay analysis functionality using AI models.
Author: Hasif50
"""

import os
import re
import nltk
import textstat
from typing import Dict, List, Optional, Any
from nltk.corpus import stopwords
from langchain_openai import ChatOpenAI, AzureChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import spacy

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
    Main essay analysis class that handles AI-powered text analysis.
    From Hasif's Workspace - Built for comprehensive essay evaluation.
    """

    def __init__(
        self,
        model_provider: str = "openai",
        model_name: str = "gpt-4",
        temperature: float = 0.3,
        max_tokens: int = 2000,
        language: str = "en",
    ):
        """
        Initialize the essay analyzer.

        Args:
            model_provider: AI model provider ('openai' or 'azure_openai')
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

    def _initialize_model(self):
        """Initialize the AI model based on provider."""
        try:
            if self.model_provider == "openai":
                self.llm = ChatOpenAI(
                    model_name=self.model_name,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    openai_api_key=os.getenv("OPENAI_API_KEY"),
                )
            elif self.model_provider == "azure_openai":
                self.llm = AzureChatOpenAI(
                    deployment_name=self.model_name,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    azure_endpoint=os.getenv("AZURE_ENDPOINT"),
                    api_key=os.getenv("AZURE_API_KEY"),
                    api_version=os.getenv("AZURE_API_VERSION", "2023-05-15"),
                )
            elif self.model_provider == "mock":
                # Lightweight mock for tests that should not call external LLMs.
                class _MockLLM:
                    def __call__(self, messages):
                        class _MockResponse:
                            content = "Mock analysis response"

                        return _MockResponse()

                self.llm = _MockLLM()
            else:
                raise ValueError(f"Unsupported model provider: {self.model_provider}")

        except Exception as e:
            raise Exception(f"Failed to initialize AI model: {str(e)}")

    def analyze_essay(
        self,
        essay_text: str,
        prompt: Optional[str] = None,
        enable_grammar: bool = True,
        enable_style: bool = True,
        enable_plagiarism: bool = False,
        enable_sentiment: bool = True,
        language: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Perform comprehensive essay analysis.

        Args:
            essay_text: The essay content to analyze
            prompt: Optional essay prompt/topic
            enable_grammar: Whether to perform grammar analysis
            enable_style: Whether to perform style analysis
            enable_plagiarism: Whether to perform basic plagiarism check
            enable_sentiment: Whether to perform sentiment analysis
            language: Reserved for backward compatibility. Essay language is auto-detected.

        Returns:
            Dictionary containing analysis results
        """
        if not essay_text or not essay_text.strip():
            raise ValueError("Essay text cannot be empty.")

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

        if enable_plagiarism:
            results["plagiarism"] = self._basic_plagiarism_check(essay_text)

        # AI-powered content analysis
        results["content_analysis"] = self._ai_content_analysis(
            essay_text, prompt, active_language
        )
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

    def _basic_plagiarism_check(self, text: str) -> Dict[str, Any]:
        """Perform basic plagiarism detection."""
        # This is a simplified implementation
        # In a real system, you would integrate with plagiarism detection APIs

        # Check for common phrases that might indicate copying
        suspicious_phrases = [
            "according to wikipedia",
            "as stated on the internet",
            "copy and paste",
            "source: google",
        ]

        found_phrases = []
        text_lower = text.lower()

        for phrase in suspicious_phrases:
            if phrase in text_lower:
                found_phrases.append(phrase)

        return {
            "suspicious_phrases": found_phrases,
            "risk_level": "high" if found_phrases else "low",
            "note": "This is a basic check. Professional plagiarism detection recommended.",
        }

    def _ai_content_analysis(
        self, text: str, prompt: Optional[str] = None, language: str = "en"
    ) -> Dict[str, str]:
        """Use AI to analyze content quality and relevance."""
        try:
            language_name = "Dutch" if language == "nl" else "English"
            system_message = """You are an expert essay evaluator. Analyze the given essay and provide insights on:
1. Content quality and depth
2. Argument strength and logic
3. Evidence and examples usage
4. Thesis clarity
5. Overall coherence

Provide constructive feedback in a professional tone.

Return the full analysis in {language_name}.""".format(language_name=language_name)

            user_message = f"Essay to analyze:\n\n{text}"

            if prompt:
                user_message = f"Essay prompt: {prompt}\n\n{user_message}"

            messages = [
                SystemMessage(content=system_message),
                HumanMessage(content=user_message),
            ]

            response = self.llm(messages)

            return {
                "ai_analysis": response.content,
                "analysis_provider": f"{self.model_provider}_{self.model_name}",
                "workspace_attribution": "From Hasif's Workspace",
            }

        except Exception as e:
            return {
                "ai_analysis": f"Error in AI analysis: {str(e)}",
                "analysis_provider": "error",
                "workspace_attribution": "From Hasif's Workspace",
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
