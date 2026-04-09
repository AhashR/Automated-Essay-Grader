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

- Upload or paste a learning story (`.txt`, `.pdf`, `.docx`)
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
