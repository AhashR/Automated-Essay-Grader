"""Basic Flask app route tests."""

from app import app, render_feedback


def test_health_endpoint():
    client = app.test_client()
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_index_page_loads():
    client = app.test_client()
    response = client.get("/")

    assert response.status_code == 200
    assert b"HvA Feedback AI" in response.data
    assert b"Strengths" not in response.data
    assert b"Areas for Improvement" not in response.data
    assert b"Suggestions" not in response.data


def test_render_feedback_renders_markdown_blocks():
    source = "## Title\n\n- Item 1\n- Item 2\n\n[Link](https://example.com)"

    html = str(render_feedback(source))

    assert "<h2>Title</h2>" in html
    assert "<ul>" in html
    assert "<li>Item 1</li>" in html
    assert 'href="https://example.com"' in html


def test_render_feedback_escapes_html_tags():
    source = "<script>alert('x')</script>\n\n**Safe**"

    html = str(render_feedback(source))

    assert "<script>" not in html
    assert "&lt;script&gt;alert" in html
    assert "<strong>Safe</strong>" in html
