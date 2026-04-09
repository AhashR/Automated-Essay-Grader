from __future__ import annotations

import argparse
import json
import shutil
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from joblib import dump
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline


DEFAULT_LABEL_PATTERNS: Dict[str, str] = {
    "good": "good",
    "bad": "bad",
}


def parse_label_map(raw: str) -> Dict[str, str]:
    """Parse CLI mapping like 'good=good,bad=bad'."""
    parsed: Dict[str, str] = {}
    chunks = [chunk.strip() for chunk in (raw or "").split(",") if chunk.strip()]
    for chunk in chunks:
        if "=" not in chunk:
            raise ValueError(
                f"Invalid label map entry '{chunk}'. Expected format: pattern=label"
            )
        pattern, label = [part.strip().lower() for part in chunk.split("=", 1)]
        if not pattern or not label:
            raise ValueError(
                f"Invalid label map entry '{chunk}'. Pattern and label cannot be empty."
            )
        parsed[pattern] = label
    if not parsed:
        raise ValueError("Label map cannot be empty.")
    return parsed


def iter_story_files(stories_dir: Path, extensions: Iterable[str]) -> Iterable[Path]:
    allowed = {ext.strip().lower() for ext in extensions if ext.strip()}
    for file_path in stories_dir.rglob("*"):
        if not file_path.is_file():
            continue
        if file_path.suffix.lower() in allowed:
            yield file_path


def read_text(file_path: Path) -> str:
    try:
        return file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return file_path.read_text(encoding="latin-1", errors="ignore")


def infer_label(file_path: Path, label_patterns: Dict[str, str]) -> Optional[str]:
    parts = [part.lower() for part in file_path.parts]
    for pattern, label in label_patterns.items():
        if any(pattern in part for part in parts):
            return label
    return None


def load_labeled_dataset(
    stories_dir: Path, label_patterns: Dict[str, str], extensions: Iterable[str]
) -> Tuple[List[str], List[str], List[Dict[str, str]], List[str]]:
    texts: List[str] = []
    labels: List[str] = []
    rows: List[Dict[str, str]] = []
    skipped: List[str] = []

    for file_path in sorted(iter_story_files(stories_dir, extensions)):
        label = infer_label(file_path, label_patterns)
        if label is None:
            skipped.append(str(file_path))
            continue

        text = read_text(file_path).strip()
        if not text:
            skipped.append(f"{file_path} (empty)")
            continue

        texts.append(text)
        labels.append(label)
        rows.append(
            {
                "source_file": str(file_path),
                "label": label,
                "char_count": str(len(text)),
            }
        )

    return texts, labels, rows, skipped


def build_pipeline() -> Pipeline:
    return Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    lowercase=True,
                    ngram_range=(1, 2),
                    max_features=12000,
                    min_df=1,
                ),
            ),
            (
                "clf",
                LogisticRegression(
                    max_iter=3000,
                    class_weight="balanced",
                    solver="liblinear",
                ),
            ),
        ]
    )


def train_with_optional_eval(
    texts: List[str],
    labels: List[str],
    test_size: float,
    random_state: int,
) -> Tuple[Pipeline, bool, Optional[float], Optional[Dict[str, Any]], Optional[Any]]:
    label_counts = Counter(labels)
    min_class_count = min(label_counts.values()) if label_counts else 0
    can_evaluate = test_size > 0 and min_class_count >= 2 and len(texts) >= 4

    model = build_pipeline()
    if can_evaluate:
        x_train, x_test, y_train, y_test = train_test_split(
            texts,
            labels,
            test_size=test_size,
            random_state=random_state,
            stratify=labels,
        )
        model.fit(x_train, y_train)

        preds = model.predict(x_test)
        acc = float(accuracy_score(y_test, preds))
        report = classification_report(y_test, preds, output_dict=True, zero_division=0)
        matrix = confusion_matrix(y_test, preds, labels=sorted(label_counts.keys()))
        return model, can_evaluate, acc, report, matrix

    model.fit(texts, labels)
    return model, can_evaluate, None, None, None


def predict_with_confidence(model: Pipeline, text: str) -> Tuple[str, Optional[float]]:
    prediction = str(model.predict([text])[0])
    confidence: Optional[float] = None

    if hasattr(model, "predict_proba"):
        probabilities = model.predict_proba([text])[0]
        confidence = float(max(probabilities))

    return prediction, confidence


def unique_target_path(target_dir: Path, file_name: str) -> Path:
    candidate = target_dir / file_name
    if not candidate.exists():
        return candidate

    stem = Path(file_name).stem
    suffix = Path(file_name).suffix
    counter = 1
    while True:
        candidate = target_dir / f"{stem}__auto_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def auto_label_and_route(
    model: Pipeline,
    source_dir: Path,
    destination_root: Path,
    extensions: Iterable[str],
    mode: str,
    confidence_threshold: float,
    skip_below_threshold: bool,
    dry_run: bool,
) -> Dict[str, Any]:
    operations: List[Dict[str, Any]] = []
    moved_count = 0
    skipped_count = 0

    source_resolved = source_dir.resolve()
    destination_resolved = destination_root.resolve()

    if not source_resolved.exists():
        raise FileNotFoundError(f"Auto-label source directory not found: {source_resolved}")

    for file_path in sorted(iter_story_files(source_resolved, extensions)):
        text = read_text(file_path).strip()
        if not text:
            skipped_count += 1
            operations.append(
                {
                    "source": str(file_path),
                    "status": "skipped_empty",
                }
            )
            continue

        predicted_label, confidence = predict_with_confidence(model, text)
        if skip_below_threshold and confidence is not None and confidence < confidence_threshold:
            skipped_count += 1
            operations.append(
                {
                    "source": str(file_path),
                    "status": "skipped_low_confidence",
                    "predicted_label": predicted_label,
                    "confidence": confidence,
                }
            )
            continue

        target_dir = destination_resolved / predicted_label
        target_path = unique_target_path(target_dir, file_path.name)

        if not dry_run:
            target_dir.mkdir(parents=True, exist_ok=True)
            if mode == "move":
                shutil.move(str(file_path), str(target_path))
            else:
                shutil.copy2(file_path, target_path)

        moved_count += 1
        operations.append(
            {
                "source": str(file_path),
                "target": str(target_path),
                "status": "planned" if dry_run else mode,
                "predicted_label": predicted_label,
                "confidence": confidence,
            }
        )

    return {
        "source_dir": str(source_resolved),
        "destination_root": str(destination_resolved),
        "mode": mode,
        "moved_or_copied_count": moved_count,
        "skipped_count": skipped_count,
        "operations": operations,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Train a good-vs-bad learning story classifier directly from markdown/text files."
        )
    )
    parser.add_argument(
        "--stories-dir",
        default="learning stories",
        help="Root directory containing learning story files.",
    )
    parser.add_argument(
        "--output-model",
        default="models/learning_story_good_bad.joblib",
        help="Path to save trained model artifact.",
    )
    parser.add_argument(
        "--output-summary",
        default="models/learning_story_good_bad_summary.json",
        help="Path to save training summary metrics.",
    )
    parser.add_argument(
        "--extensions",
        default=".md,.markdown,.txt",
        help="Comma-separated file extensions to include.",
    )
    parser.add_argument(
        "--label-map",
        default="good=good,bad=bad",
        help="Comma-separated mapping of folder/file patterns to labels.",
    )
    parser.add_argument(
        "--test-size",
        type=float,
        default=0.25,
        help="Proportion of data reserved for evaluation. Use 0 to train on all data.",
    )
    parser.add_argument(
        "--random-state",
        type=int,
        default=42,
        help="Random state for reproducible splits.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview discovered labeled files without training.",
    )
    parser.add_argument(
        "--auto-label-from",
        default="",
        help=(
            "Optional folder with unlabeled stories to classify and route to label folders. "
            "Example: 'learning stories/all'"
        ),
    )
    parser.add_argument(
        "--destination-root",
        default="learning stories",
        help="Root folder containing label subfolders (for example learning stories/good).",
    )
    parser.add_argument(
        "--route-mode",
        choices=["move", "copy"],
        default="move",
        help="Whether auto-labeled files are moved or copied to destination label folders.",
    )
    parser.add_argument(
        "--confidence-threshold",
        type=float,
        default=0.0,
        help="Optional confidence threshold between 0 and 1 for routing.",
    )
    parser.add_argument(
        "--skip-below-threshold",
        action="store_true",
        help="Skip routing for files whose confidence is below --confidence-threshold.",
    )

    args = parser.parse_args()
    stories_dir = Path(args.stories_dir).resolve()
    output_model = Path(args.output_model).resolve()
    output_summary = Path(args.output_summary).resolve()
    destination_root = Path(args.destination_root).resolve()
    auto_label_from = Path(args.auto_label_from).resolve() if args.auto_label_from else None
    extensions = [ext.strip().lower() for ext in args.extensions.split(",") if ext.strip()]
    label_patterns = parse_label_map(args.label_map)

    if not stories_dir.exists():
        raise FileNotFoundError(f"Stories directory not found: {stories_dir}")

    texts, labels, rows, skipped = load_labeled_dataset(
        stories_dir=stories_dir,
        label_patterns=label_patterns,
        extensions=extensions,
    )

    label_counts = Counter(labels)
    print(f"Stories scanned: {len(rows) + len(skipped)}")
    print(f"Stories labeled: {len(rows)}")
    print(f"Label distribution: {dict(label_counts)}")
    if skipped:
        print(f"Stories skipped (no label or empty): {len(skipped)}")

    if args.dry_run:
        for row in rows:
            print(f"- {row['label']}: {row['source_file']}")
        if auto_label_from is None:
            return

    if len(label_counts) < 2:
        raise ValueError(
            "Need at least 2 classes. Check --label-map and folder naming."
        )

    model, can_evaluate, acc, report, matrix = train_with_optional_eval(
        texts=texts,
        labels=labels,
        test_size=args.test_size,
        random_state=args.random_state,
    )

    auto_label_summary = None
    if auto_label_from is not None:
        auto_label_summary = auto_label_and_route(
            model=model,
            source_dir=auto_label_from,
            destination_root=destination_root,
            extensions=extensions,
            mode=args.route_mode,
            confidence_threshold=args.confidence_threshold,
            skip_below_threshold=args.skip_below_threshold,
            dry_run=args.dry_run,
        )

        print(
            "Auto-label routing complete: "
            f"{auto_label_summary['moved_or_copied_count']} routed, "
            f"{auto_label_summary['skipped_count']} skipped."
        )

        if not args.dry_run:
            texts, labels, rows, skipped = load_labeled_dataset(
                stories_dir=stories_dir,
                label_patterns=label_patterns,
                extensions=extensions,
            )
            label_counts = Counter(labels)

            model, can_evaluate, acc, report, matrix = train_with_optional_eval(
                texts=texts,
                labels=labels,
                test_size=args.test_size,
                random_state=args.random_state,
            )

    output_model.parent.mkdir(parents=True, exist_ok=True)
    dump(
        {
            "model": model,
            "label_map": label_patterns,
            "extensions": extensions,
            "classes": list(sorted(label_counts.keys())),
        },
        output_model,
    )

    summary = {
        "stories_dir": str(stories_dir),
        "labeled_count": len(rows),
        "skipped_count": len(skipped),
        "label_distribution": dict(label_counts),
        "test_size": args.test_size,
        "random_state": args.random_state,
        "evaluation_available": can_evaluate,
        "accuracy": acc,
        "classification_report": report,
        "confusion_matrix": matrix.tolist() if matrix is not None else None,
        "labels_in_matrix_order": list(sorted(label_counts.keys())),
        "auto_labeling": auto_label_summary,
    }
    output_summary.parent.mkdir(parents=True, exist_ok=True)
    output_summary.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"Model saved to: {output_model}")
    print(f"Summary saved to: {output_summary}")
    if can_evaluate and acc is not None:
        print(f"Test accuracy: {acc:.3f}")
    else:
        print(
            "Evaluation skipped: add more labeled files per class or set --test-size > 0 once data grows."
        )


if __name__ == "__main__":
    main()