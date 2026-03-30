"""Basic Flask app route tests."""

from app import app


def test_health_endpoint():
    client = app.test_client()
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_index_page_loads():
    client = app.test_client()
    response = client.get("/")

    assert response.status_code == 200
    assert b"Automated Essay Grader" in response.data
