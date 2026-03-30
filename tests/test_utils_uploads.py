"""Regression tests for Flask/Streamlit upload filename handling."""

import io
import sys
import zipfile
from pathlib import Path

src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from utils import _get_uploaded_file_name, validate_file


class FakeUpload(io.BytesIO):
    """Simple upload-like object used for utility tests."""

    def __init__(
        self,
        content: bytes,
        *,
        name: str = "",
        filename: str = "",
        mimetype: str = "",
        content_type: str = "",
    ):
        super().__init__(content)
        if name:
            self.name = name
        if filename:
            self.filename = filename
        if mimetype:
            self.mimetype = mimetype
        if content_type:
            self.content_type = content_type


def _minimal_docx_bytes() -> bytes:
    """Build a minimal DOCX-like zip structure for signature tests."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", "<Types></Types>")
        archive.writestr("word/document.xml", "<w:document></w:document>")
    return buffer.getvalue()


def test_validate_file_prefers_flask_filename_over_field_name():
    """Flask FileStorage objects should use the real uploaded filename extension."""
    uploaded = FakeUpload(
        b"dummy-docx-content",
        name="essay_file",
        filename="learning_story.docx",
    )

    is_valid, error_message = validate_file(uploaded, return_error=True)

    assert _get_uploaded_file_name(uploaded) == "learning_story.docx"
    assert is_valid is True
    assert error_message is None


def test_filename_falls_back_to_name_for_streamlit_uploads():
    """Streamlit-style uploads without filename should still work via name."""
    uploaded = FakeUpload(b"plain text", name="essay.txt")

    is_valid, error_message = validate_file(uploaded, return_error=True)

    assert _get_uploaded_file_name(uploaded) == "essay.txt"
    assert is_valid is True
    assert error_message is None


def test_validate_file_accepts_docx_when_filename_metadata_is_bad():
    """Validation should still pass when filename is the form field name."""
    uploaded = FakeUpload(
        _minimal_docx_bytes(),
        name="essay_file",
        filename="essay_file",
        mimetype="application/octet-stream",
    )

    is_valid, error_message = validate_file(uploaded, return_error=True)

    assert is_valid is True
    assert error_message is None


def test_validate_file_accepts_zip_signature_when_metadata_is_bad():
    """DOCX fallback should accept Office ZIP signatures when filename metadata is unusable."""
    payload = bytes([0x50, 0x4B, 0x03, 0x04]) + b"office-package"
    uploaded = FakeUpload(
        payload,
        name="essay_file",
        filename="essay_file",
        mimetype="application/octet-stream",
    )

    is_valid, error_message = validate_file(uploaded, return_error=True)

    assert is_valid is True
    assert error_message is None
