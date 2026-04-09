from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from joblib import load


class StoryQualityModel:
    """Wrapper around the trained good-vs-bad classifier artifact."""

    def __init__(self, model_path: str | Path):
        self.model_path = Path(model_path).resolve()
        self.pipeline = None
        self.classes = []
        self.available = False
        self.error: Optional[str] = None
        self._load_model()

    def _load_model(self) -> None:
        if not self.model_path.exists():
            self.error = f"Model file not found at {self.model_path}"
            return

        try:
            payload = load(self.model_path)
            if isinstance(payload, dict) and payload.get("model") is not None:
                self.pipeline = payload.get("model")
                self.classes = list(payload.get("classes", []))
            else:
                self.pipeline = payload
                self.classes = []

            self.available = self.pipeline is not None
        except Exception as exc:
            self.error = str(exc)
            self.available = False

    def predict(self, text: str) -> Dict[str, Any]:
        """Return a quality prediction payload used by grading and feedback."""
        if not text or not text.strip():
            return {
                "available": self.available,
                "label": None,
                "confidence": None,
                "error": "Empty text",
            }

        if not self.available or self.pipeline is None:
            return {
                "available": False,
                "label": None,
                "confidence": None,
                "error": self.error or "Model unavailable",
            }

        try:
            label = str(self.pipeline.predict([text])[0])
            confidence = None

            if hasattr(self.pipeline, "predict_proba"):
                probs = self.pipeline.predict_proba([text])[0]
                confidence = float(max(probs))

            return {
                "available": True,
                "label": label,
                "confidence": confidence,
                "error": None,
                "model_path": str(self.model_path),
            }
        except Exception as exc:
            return {
                "available": False,
                "label": None,
                "confidence": None,
                "error": str(exc),
                "model_path": str(self.model_path),
            }