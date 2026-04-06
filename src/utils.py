"""
Utilities Module

Utility functions for document processing and file handling.
"""

import os
import zipfile
from pathlib import Path
from typing import Dict, Optional

# Document processing imports
try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False

try:
    import pdfplumber

    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

try:
    from docx import Document

    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

PDF_AVAILABLE = PYPDF2_AVAILABLE or PDFPLUMBER_AVAILABLE


def _get_uploaded_file_name(uploaded_file) -> str:
    """Return a best-effort filename across Streamlit and Flask file objects."""
    filename = getattr(uploaded_file, "filename", None)
    if filename:
        return os.path.basename(filename)

    fallback_name = getattr(uploaded_file, "name", "")
    return os.path.basename(fallback_name) if fallback_name else ""


def _get_uploaded_file_stream(uploaded_file):
    """Return a seekable stream for upload objects when available."""
    return getattr(uploaded_file, "stream", uploaded_file)


def _peek_upload_bytes(uploaded_file, byte_count: int = 8) -> bytes:
    """Read leading bytes without changing the current stream position."""
    stream = _get_uploaded_file_stream(uploaded_file)

    if not hasattr(stream, "read"):
        return b""

    if hasattr(stream, "tell") and hasattr(stream, "seek"):
        current_position = stream.tell()
        stream.seek(0)
        header = stream.read(byte_count) or b""
        stream.seek(current_position)
        return header

    return b""


def _looks_like_docx(uploaded_file) -> bool:
    """Heuristic check for DOCX package structure."""
    stream = _get_uploaded_file_stream(uploaded_file)
    if not hasattr(stream, "tell") or not hasattr(stream, "seek"):
        return False

    current_position = stream.tell()
    stream.seek(0)
    try:
        with zipfile.ZipFile(stream) as archive:
            names = set(archive.namelist())
            return "[Content_Types].xml" in names and any(
                name.startswith("word/") for name in names
            )
    except (OSError, zipfile.BadZipFile, RuntimeError):
        return False
    finally:
        stream.seek(current_position)


def _detect_file_extension(uploaded_file) -> str:
    """Detect file extension from metadata and content signatures."""
    allowed_extensions = {"txt", "pdf", "docx", "doc"}

    filename_candidates = []
    for attr_name in ("filename", "name"):
        value = getattr(uploaded_file, attr_name, "")
        if value:
            filename_candidates.append(os.path.basename(value))

    for candidate in filename_candidates:
        extension = Path(candidate).suffix.lower().lstrip(".")
        if extension in allowed_extensions:
            return extension

    mime_type = (
        getattr(uploaded_file, "mimetype", None)
        or getattr(uploaded_file, "content_type", None)
        or ""
    ).split(";")[0].strip().lower()

    mime_to_extension = {
        "text/plain": "txt",
        "application/pdf": "pdf",
        "application/msword": "doc",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    }
    if mime_type in mime_to_extension:
        return mime_to_extension[mime_type]

    header = _peek_upload_bytes(uploaded_file)
    if header.startswith(b"%PDF"):
        return "pdf"
    if header.startswith(b"\xD0\xCF\x11\xE0"):
        return "doc"
    if header.startswith(b"PK\x03\x04"):
        # DOCX is a ZIP container; accept ZIP signature as DOCX fallback when
        # filename metadata is unreliable.
        return "docx"

    return ""


def _get_uploaded_file_size(uploaded_file) -> int:
    """Return uploaded file size across Streamlit and Flask file objects."""
    if hasattr(uploaded_file, "size") and uploaded_file.size is not None:
        return int(uploaded_file.size)

    stream = _get_uploaded_file_stream(uploaded_file)
    current_position = stream.tell()
    stream.seek(0, os.SEEK_END)
    file_size = stream.tell()
    stream.seek(current_position)
    return int(file_size)


def load_document(uploaded_file) -> str:
    """
    Load and extract text from uploaded document.

    Args:
        uploaded_file: Streamlit or Flask uploaded file object

    Returns:
        Extracted text content

    Raises:
        Exception: If file cannot be processed
    """
    try:
        file_extension = _detect_file_extension(uploaded_file)

        if file_extension == "txt":
            return _load_text_file(uploaded_file)
        elif file_extension == "pdf":
            return _load_pdf_file(uploaded_file)
        elif file_extension in ["docx", "doc"]:
            return _load_docx_file(uploaded_file)
        else:
            raise ValueError("Unsupported or unknown file format")

    except Exception as e:
        raise Exception(f"Error loading document: {str(e)}")


def _load_text_file(uploaded_file) -> str:
    """Load text from TXT file."""
    try:
        # Try UTF-8 first
        content = uploaded_file.read().decode("utf-8")
        return content
    except UnicodeDecodeError:
        # Fallback to other encodings
        uploaded_file.seek(0)
        try:
            content = uploaded_file.read().decode("latin-1")
            return content
        except UnicodeDecodeError:
            uploaded_file.seek(0)
            content = uploaded_file.read().decode("cp1252")
            return content


def _load_pdf_file(uploaded_file) -> str:
    """Load text from PDF file."""
    if not PDF_AVAILABLE:
        raise Exception(
            "PDF processing libraries not installed. Please install PyPDF2 and pdfplumber."
        )

    text_content = ""

    try:
        # Try with pdfplumber first (better text extraction)
        if PDFPLUMBER_AVAILABLE:
            with pdfplumber.open(uploaded_file) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_content += page_text + "\n"
    except Exception:
        # Fallback to PyPDF2
        if PYPDF2_AVAILABLE:
            uploaded_file.seek(0)
            pdf_reader = PyPDF2.PdfReader(uploaded_file)

            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text_content += page.extract_text() + "\n"

    if not text_content.strip() and PYPDF2_AVAILABLE:
        try:
            uploaded_file.seek(0)
            pdf_reader = PyPDF2.PdfReader(uploaded_file)

            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text_content += page.extract_text() + "\n"
        except Exception as e:
            raise Exception(f"Could not extract text from PDF: {str(e)}")

    if not text_content.strip():
        raise Exception("No text could be extracted from the PDF file.")

    return text_content


def _load_docx_file(uploaded_file) -> str:
    """Load text from DOCX file."""
    if not DOCX_AVAILABLE:
        raise Exception(
            "Document processing libraries not installed. Please install python-docx."
        )

    try:
        doc = Document(uploaded_file)
        text_content = ""

        for paragraph in doc.paragraphs:
            text_content += paragraph.text + "\n"

        if not text_content.strip():
            raise Exception("No text could be extracted from the document.")

        return text_content

    except Exception as e:
        raise Exception(f"Could not extract text from DOCX file: {str(e)}")


def validate_file(uploaded_file, return_error: bool = False):
    """
    Validate uploaded file for size and format.

    Args:
        uploaded_file: Streamlit or Flask uploaded file object
        return_error: Whether to return a tuple with an error message

    Returns:
        bool when return_error=False
        (bool, error_message) when return_error=True
    """
    def _result(valid: bool, error_message: Optional[str] = None):
        if return_error:
            return valid, error_message
        return valid

    # Check file size (max 10MB)
    max_size = 10 * 1024 * 1024  # 10MB in bytes
    file_size = _get_uploaded_file_size(uploaded_file)
    if file_size > max_size:
        return _result(
            False,
            f"File size ({file_size / 1024 / 1024:.1f}MB) exceeds maximum allowed size (10MB).",
        )

    # Check file extension (with metadata and signature fallback)
    allowed_extensions = ["txt", "pdf", "docx", "doc"]
    file_extension = _detect_file_extension(uploaded_file)

    if file_extension not in allowed_extensions:
        display_value = file_extension or _get_uploaded_file_name(uploaded_file) or "unknown"
        return _result(
            False,
            f"File format '{display_value}' is not supported. Allowed formats: {', '.join(allowed_extensions)}",
        )

    return _result(True, None)


def format_score_display(score: float, max_score: float = 100) -> str:
    """
    Format score for display.

    Args:
        score: The score value
        max_score: Maximum possible score

    Returns:
        Formatted score string
    """
    percentage = (score / max_score) * 100 if max_score > 0 else 0
    return f"{score:.1f}/{max_score} ({percentage:.1f}%)"


def get_performance_color(percentage: float) -> str:
    """
    Get color code based on performance percentage.

    Args:
        percentage: Performance percentage (0-100)

    Returns:
        Color code for display
    """
    if percentage >= 90:
        return "#28a745"  # Green
    elif percentage >= 80:
        return "#17a2b8"  # Blue
    elif percentage >= 70:
        return "#ffc107"  # Yellow
    elif percentage >= 60:
        return "#fd7e14"  # Orange
    else:
        return "#dc3545"  # Red


def truncate_text(text: str, max_length: int = 100) -> str:
    """
    Truncate text to specified length.

    Args:
        text: Text to truncate
        max_length: Maximum length

    Returns:
        Truncated text with ellipsis if needed
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


def clean_text_for_analysis(text: str) -> str:
    """
    Clean text for analysis by removing extra whitespace and formatting.

    Args:
        text: Raw text input

    Returns:
        Cleaned text
    """
    # Remove extra whitespace
    text = " ".join(text.split())

    # Remove multiple newlines
    text = "\n".join(line.strip() for line in text.split("\n") if line.strip())

    return text


def get_workspace_info() -> Dict[str, str]:
    """
    Get workspace attribution information.

    Returns:
        Dictionary with workspace information
    """
    return {
        "workspace": "HvA Feedback Agent",
        "author": "HvA Feedback Agent Team",
        "version": "1.0.0",
        "description": "AI-Powered Essay Grading System",
    }
