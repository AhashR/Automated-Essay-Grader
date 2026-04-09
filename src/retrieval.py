from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, cast

logger = logging.getLogger(__name__)

try:
    from docx import Document

    DOCX_AVAILABLE = True
except ImportError:
    Document = None
    DOCX_AVAILABLE = False

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
        self.data_path = (
            Path(data_path)
            if data_path
            else Path(__file__).resolve().parent.parent
            / "data"
            / "examples"
            / "learning_stories.json"
        )
        self.data_path = self.data_path.resolve(strict=False)
        self.repo_root = Path(__file__).resolve().parent.parent
        self.fallback_examples_dir = self.repo_root / "learning stories"
        self.top_k = top_k
        self.min_score = min_score
        self.examples: List[Dict[str, Any]] = []
        self.vectorizer = None
        self.matrix = None
        self.available = TfidfVectorizer is not None and cosine_similarity is not None
        self._load_index()

    def _load_examples(self) -> List[Dict[str, Any]]:
        source_path = self._resolve_source_path()

        if source_path.is_file() and source_path.suffix.lower() == ".json":
            return self._load_examples_from_json(source_path)

        if source_path.is_dir():
            return self._load_examples_from_directory(source_path)

        logger.info("Learning story examples not found at %s", source_path)
        return []

    def _resolve_source_path(self) -> Path:
        """Resolve the best available example source."""
        if self.data_path.exists():
            return self.data_path

        default_json_path = (
            self.repo_root / "data" / "examples" / "learning_stories.json"
        ).resolve(strict=False)

        if self.data_path == default_json_path and self.fallback_examples_dir.exists():
            logger.info(
                "Learning story JSON not found at %s, falling back to %s",
                self.data_path,
                self.fallback_examples_dir,
            )
            return self.fallback_examples_dir

        return self.data_path

    def _load_examples_from_json(self, source_path: Path) -> List[Dict[str, Any]]:
        try:
            with source_path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
            if isinstance(data, list):
                return data
            logger.warning("Learning story file is not a list: falling back to empty index")
            return []
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Failed to load learning stories: %s", exc)
            return []

    def _load_examples_from_directory(self, source_dir: Path) -> List[Dict[str, Any]]:
        if not source_dir.exists():
            return []

        examples: List[Dict[str, Any]] = []
        for file_path in sorted(source_dir.iterdir()):
            if not file_path.is_file():
                continue

            suffix = file_path.suffix.lower()
            text = ""

            if suffix in {".txt", ".md"}:
                try:
                    text = file_path.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    text = file_path.read_text(encoding="latin-1", errors="ignore")
            elif suffix == ".docx" and DOCX_AVAILABLE:
                text = self._extract_docx_text(file_path)
            else:
                continue

            clean_text = text.strip()
            if not clean_text:
                continue

            examples.append(
                {
                    "id": file_path.stem,
                    "title": file_path.stem,
                    "summary": _shorten(clean_text, 320),
                    "text": clean_text,
                    "source_path": str(file_path),
                }
            )

        if not examples:
            logger.info("No indexable learning story documents found in %s", source_dir)

        return examples

    def _extract_docx_text(self, file_path: Path) -> str:
        if not DOCX_AVAILABLE:
            logger.warning("python-docx is unavailable; skipping %s", file_path)
            return ""

        try:
            document_cls = cast(Any, Document)
            document = document_cls(str(file_path))
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Failed to open DOCX file %s: %s", file_path, exc)
            return ""

        paragraphs = [paragraph.text.strip() for paragraph in document.paragraphs]
        return "\n".join(paragraph for paragraph in paragraphs if paragraph)

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

        vectorizer_cls = cast(Any, TfidfVectorizer)
        self.vectorizer = vectorizer_cls(stop_words="english", max_features=4096)
        self.matrix = self.vectorizer.fit_transform(corpus)

    def search(self, query: str, top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        if not query or self.matrix is None or self.vectorizer is None:
            return []

        k = top_k or self.top_k
        try:
            query_vec = self.vectorizer.transform([query])
            similarity_fn = cast(Any, cosine_similarity)
            sims = similarity_fn(query_vec, self.matrix).flatten()
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
            example["snippet"] = _shorten(
                example.get("summary") or example.get("text", "")
            )
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
            score_str = (
                f" (score {score:.2f})" if isinstance(score, (int, float)) else ""
            )
            lines.append(f"- {title}{score_str}: {snippet}")
        return "\n".join(lines)
