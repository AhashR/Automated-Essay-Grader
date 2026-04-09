# HvA Learning Story Feedback Agent

## Overview

This application provides AI-supported feedback for **HvA HBO-ICT learning stories**.
It is specifically tailored to the HvA rubric and evaluates submissions on:

- Context and understanding
- Learning goals and formulation
- Learning approach with concrete actions
- Substantiation and evidence quality

The app supports both **Dutch (NL)** and **English (EN)** in the UI and generated feedback.

## What Is HvA-Specific

- Rubric-driven grading based on `rubrics/learning_story.json`
- Feedback prompt tuned to HvA learning story fundamentals
- Retrieval of internal learning story examples from `learning stories/`
- Heuristic signal extraction focused on context, goals, approach, sources, and evidence

## Features

- Upload or paste a learning story (`.txt`, `.md`, `.markdown`, `.pdf`, `.docx`)
- AI feedback rendered as Markdown
- Criterion breakdown and overall score
- NL/EN interface switch
- Internal retrieval grounding with curated learning story examples

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Configure environment variables in `.env`:

```env
GEMINI_API_KEY=your_gemini_api_key_here
SECRET_KEY=change-me-in-production
```

3. Run the app:

```bash
python app.py
```

4. Optional debug mode:

```bash
python -m flask --app app.py --debug run
```

## Project Structure

```text
HvA-Feedback-Agent/
├── app.py
├── requirements.txt
├── README.md
├── learning stories/
├── rubrics/
│   └── learning_story.json
├── src/
│   ├── essay_analyzer.py
│   ├── feedback_generator.py
│   ├── grading_engine.py
│   ├── retrieval.py
│   └── utils.py
├── templates/
│   ├── index.html
│   └── index_nl.html
└── static/
    └── styles.css
```

## Notes

- The grading engine is intentionally scoped to HvA learning stories.
- If no vector JSON exists, retrieval falls back to the local `learning stories/` folder.
- Feedback language follows the selected UI language.
- If `models/learning_story_good_bad.joblib` exists, scoring uses a conservative quality adjustment based on learned good/bad patterns.

## Classifier-Assisted Scoring

The app now combines:

- rubric/signal-based base score
- learned good/bad classifier signal from your curated stories

Final score logic:

- base score from rubric criteria
- plus a bounded confidence-based adjustment from the classifier

You can override the model path with:

```env
LEARNING_STORY_QUALITY_MODEL_PATH=models/learning_story_good_bad.joblib
```

## Train Good-vs-Bad Classifier From Markdown

You can train a simple classifier directly from the files in `learning stories/`.
No JSON dataset is required.

Folder naming is used for labels by default:

- folders/files containing `good` -> label `good`
- folders/files containing `bad` -> label `bad`

Run a dry run to verify discovered labels:

```bash
python scripts/train_markdown_classifier.py --dry-run
```

Train and export model + metrics summary:

```bash
python scripts/train_markdown_classifier.py
```

For very small labeled datasets, train on all discovered files (no test split):

```bash
python scripts/train_markdown_classifier.py --test-size 0
```

Outputs:

- `models/learning_story_good_bad.joblib`
- `models/learning_story_good_bad_summary.json`

If your folder names are different, pass a custom mapping:

```bash
python scripts/train_markdown_classifier.py --label-map "excellent=good,poor=bad"
```

### Auto-Label From `all` And Retrain

To classify files from `learning stories/all` into `learning stories/good` or
`learning stories/bad`, then retrain on the expanded set:

```bash
python scripts/train_markdown_classifier.py --auto-label-from "learning stories/all" --route-mode move --test-size 0
```

Use `--route-mode copy` if you want to keep originals in `all`.

To preview operations without moving files:

```bash
python scripts/train_markdown_classifier.py --auto-label-from "learning stories/all" --route-mode move --dry-run
```
