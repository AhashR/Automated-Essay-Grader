"""
Retrieval helpers for learning story grounding and optional web search.

- LearningStoryRetriever: lightweight TF-IDF vector store over example learning stories
- WebSearcher: optional DuckDuckGo search with site filters (e.g., hva.nl)
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
except ImportError:  # Fallback when dependency is missing (tests without extras)
    TfidfVectorizer = None
    cosine_similarity = None

def _shorten(text: str, limit: int = 240) -> str:
    """Return a trimmed snippet for prompts."""
    if not text:
        return ""
    return text if len(text) <= limit else text[:limit].rstrip() + "..."


class LearningStoryRetriever:
    """Simple in-process vector store over curated learning story examples."""

    def __init__(
        self,
        data_path: Optional[str | Path] = None,
        top_k: int = 3,
        min_score: float = 0.05,
    ) -> None:
        self.data_path = Path(data_path) if data_path else Path(__file__).resolve().parent.parent / "data" / "examples" / "learning_stories.json"
        self.top_k = top_k
        self.min_score = min_score
        self.examples: List[Dict[str, Any]] = []
        self.vectorizer = None
        self.matrix = None
        self.available = TfidfVectorizer is not None and cosine_similarity is not None
        self._load_index()

    def _load_examples(self) -> List[Dict[str, Any]]:
        if not self.data_path.exists():
            logger.info("Learning story examples not found at %s", self.data_path)
            return []

        try:
            with self.data_path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
            if isinstance(data, list):
                return data
            logger.warning("Learning story file is not a list: falling back to empty index")
            return []
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Failed to load learning stories: %s", exc)
            return []

    def _load_index(self) -> None:
        self.examples = self._load_examples()
        if not self.examples or not self.available:
            self.matrix = None
            return

        corpus = []
        for example in self.examples:
            text_blob = "\n".join(
                [
                    str(example.get("title", "")),
                    str(example.get("summary", "")),
                    str(example.get("text", "")),
                ]
            )
            corpus.append(text_blob)

        self.vectorizer = TfidfVectorizer(stop_words="english", max_features=4096)
        self.matrix = self.vectorizer.fit_transform(corpus)

    def search(self, query: str, top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        if not query or self.matrix is None or self.vectorizer is None:
            return []

        k = top_k or self.top_k
        try:
            query_vec = self.vectorizer.transform([query])
            sims = cosine_similarity(query_vec, self.matrix).flatten()
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Vector search failed: %s", exc)
            return []

        ranked_indices = sims.argsort()[::-1]
        hits: List[Dict[str, Any]] = []
        for idx in ranked_indices[:k]:
            score = float(sims[idx])
            if score < self.min_score:
                continue
            example = dict(self.examples[idx])
            example["score"] = score
            example["snippet"] = _shorten(example.get("summary") or example.get("text", ""))
            hits.append(example)

        return hits

    def build_context_block(self, hits: List[Dict[str, Any]]) -> str:
        if not hits:
            return ""
        lines = []
        for hit in hits:
            title = hit.get("title") or hit.get("id") or "Example"
            snippet = hit.get("snippet") or _shorten(hit.get("text", ""))
            score = hit.get("score")
            score_str = f" (score {score:.2f})" if isinstance(score, (int, float)) else ""
            lines.append(f"- {title}{score_str}: {snippet}")
        return "\n".join(lines)
