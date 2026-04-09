from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, cast

from src.language_utils import normalize_language

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
        min_score: float = 0.08,
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
        self.language_indexes: Dict[str, Dict[str, Any]] = {}
        self.available = TfidfVectorizer is not None and cosine_similarity is not None
        self._load_index()

    def _detect_language(self, text: str) -> str:
        lowered = text.lower()
        english_markers = [
            " the ",
            " and ",
            " because ",
            " this ",
            " that ",
            " with ",
            " approach ",
            " sources ",
        ]
        dutch_markers = [
            " de ",
            " het ",
            " een ",
            " omdat ",
            " deze ",
            " dit ",
            " ik ",
            " wil ",
            " leren ",
            " met ",
            " aanpak ",
            " bronnen ",
        ]

        en_hits = sum(marker in f" {lowered} " for marker in english_markers)
        nl_hits = sum(marker in f" {lowered} " for marker in dutch_markers)
        return "nl" if nl_hits > en_hits else "en"

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
        for file_path in sorted(source_dir.rglob("*")):
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
                    "language": self._detect_language(clean_text),
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
        self.vectorizer = vectorizer_cls(
            stop_words=None,
            ngram_range=(1, 2),
            max_features=8192,
            token_pattern=r"(?u)\b\w[\w\-\.]+\b",
        )
        self.matrix = self.vectorizer.fit_transform(corpus)

        for lang in ("en", "nl"):
            lang_indices = [
                idx
                for idx, example in enumerate(self.examples)
                if normalize_language(example.get("language", "en"), default="en")
                == lang
            ]
            if not lang_indices:
                continue

            lang_corpus = [corpus[idx] for idx in lang_indices]
            lang_vectorizer = vectorizer_cls(
                stop_words=None,
                ngram_range=(1, 2),
                max_features=4096,
                token_pattern=r"(?u)\b\w[\w\-\.]+\b",
            )
            self.language_indexes[lang] = {
                "vectorizer": lang_vectorizer,
                "matrix": lang_vectorizer.fit_transform(lang_corpus),
                "indices": lang_indices,
            }

    def _search_with_index(
        self,
        query: str,
        vectorizer: Any,
        matrix: Any,
        source_indices: List[int],
        top_k: int,
        min_score: float,
    ) -> List[Dict[str, Any]]:
        try:
            query_vec = vectorizer.transform([query])
            similarity_fn = cast(Any, cosine_similarity)
            sims = similarity_fn(query_vec, matrix).flatten()
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Vector search failed: %s", exc)
            return []

        if sims.size == 0:
            return []

        ranked_indices = sims.argsort()[::-1]
        top_score = float(sims[ranked_indices[0]])
        adaptive_min = max(min_score, min(0.25, top_score * 0.55))

        hits: List[Dict[str, Any]] = []
        candidate_window = max(top_k * 3, 8)
        for local_idx in ranked_indices[:candidate_window]:
            score = float(sims[local_idx])
            if score < adaptive_min:
                continue

            global_idx = source_indices[local_idx]
            example = dict(self.examples[global_idx])
            example["score"] = score
            example["snippet"] = _shorten(
                example.get("summary") or example.get("text", "")
            )
            hits.append(example)
            if len(hits) >= top_k:
                break

        if hits:
            return hits

        # Sparse corpora can produce low-but-meaningful similarities, so retry with the
        # explicit baseline threshold when adaptive filtering removed all candidates.
        for local_idx in ranked_indices[:candidate_window]:
            score = float(sims[local_idx])
            if score < min_score:
                continue

            global_idx = source_indices[local_idx]
            example = dict(self.examples[global_idx])
            example["score"] = score
            example["snippet"] = _shorten(
                example.get("summary") or example.get("text", "")
            )
            hits.append(example)
            if len(hits) >= top_k:
                break

        return hits

    def search(
        self,
        query: str,
        top_k: Optional[int] = None,
        language: Optional[str] = None,
        min_score: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        if not query or self.matrix is None or self.vectorizer is None:
            return []

        k = top_k or self.top_k
        threshold = max(self.min_score, min_score if min_score is not None else self.min_score)
        detected_language = normalize_language(language or self._detect_language(query), default="en")

        lang_index = self.language_indexes.get(detected_language)
        if lang_index:
            hits = self._search_with_index(
                query=query,
                vectorizer=lang_index["vectorizer"],
                matrix=lang_index["matrix"],
                source_indices=lang_index["indices"],
                top_k=k,
                min_score=threshold,
            )
            if hits:
                return hits

        source_indices = list(range(len(self.examples)))
        return self._search_with_index(
            query=query,
            vectorizer=self.vectorizer,
            matrix=self.matrix,
            source_indices=source_indices,
            top_k=k,
            min_score=threshold,
        )

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
