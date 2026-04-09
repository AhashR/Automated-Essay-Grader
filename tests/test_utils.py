from io import BytesIO

import pytest

from src.utils import load_document, validate_file


class DummyUpload:
    def __init__(self, filename: str, content: bytes, mimetype: str = "") -> None:
        self.filename = filename
        self.name = filename
        self.mimetype = mimetype
        self.content_type = mimetype
        self.stream = BytesIO(content)

    def read(self, *args, **kwargs):
        return self.stream.read(*args, **kwargs)

    def seek(self, *args, **kwargs):
        return self.stream.seek(*args, **kwargs)

    def tell(self):
        return self.stream.tell()


@pytest.mark.parametrize(
    ("filename", "mimetype"),
    [
        ("learning-story.md", "text/markdown"),
        ("learning-story.markdown", "text/x-markdown"),
    ],
)
def test_validate_file_accepts_markdown(filename: str, mimetype: str) -> None:
    uploaded_file = DummyUpload(filename, b"# Title\n\nMarkdown content", mimetype=mimetype)

    assert validate_file(uploaded_file) is True


@pytest.mark.parametrize(
    ("filename", "mimetype"),
    [
        ("learning-story.md", "text/markdown"),
        ("learning-story.markdown", "text/x-markdown"),
    ],
)
def test_load_document_reads_markdown_as_text(filename: str, mimetype: str) -> None:
    uploaded_file = DummyUpload(filename, b"# Title\n\nMarkdown content", mimetype=mimetype)

    assert load_document(uploaded_file) == "# Title\n\nMarkdown content"
