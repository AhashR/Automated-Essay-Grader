from __future__ import annotations

from pathlib import Path

import markdown
from markupsafe import Markup, escape


def derive_subject(content: str, uploaded_filename: str = "") -> str:
    """Build a compact title from the first non-empty line or filename."""
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        cleaned = line.lstrip("#*- ").strip()
        if cleaned:
            return cleaned[:90]

    if uploaded_filename:
        return Path(uploaded_filename).stem[:90]
    return "Untitled learning story"


def render_feedback_markdown(text: str) -> Markup:
    if not text:
        return Markup("")

    safe_text = str(escape(text))
    rendered = markdown.markdown(
        safe_text,
        extensions=["extra", "sane_lists", "nl2br"],
        output_format="html5",
    )
    return Markup(rendered)