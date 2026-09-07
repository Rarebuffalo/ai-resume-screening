import re
import logging
from pathlib import Path
from typing import Optional
from pypdf import PdfReader
from models import ExtractedCandidate

logger = logging.getLogger(__name__)

def clean_extracted_text(text: str) -> str:
    """Normalize whitespace and line breaks from extracted PDF text."""
    if not text:
        return ""
    # Replace multiple spaces with single space
    text = re.sub(r"[ \t]+", " ", text)
    # Normalize multiple newlines to at most two
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    # Strip leading/trailing whitespace
    return text.strip()

def parse_pdf(file_path: Path) -> ExtractedCandidate:
    """
    Parse a single PDF resume resiliently.
    Guarantees that an invalid or malformed PDF will never crash the caller.
    """
    file_name = file_path.name
    try:
        if not file_path.exists():
            return ExtractedCandidate(file_name=file_name, parse_error="File does not exist")

        if file_path.stat().st_size == 0:
            return ExtractedCandidate(file_name=file_name, parse_error="File is empty (0 bytes)")

        reader = PdfReader(str(file_path))
        if len(reader.pages) == 0:
            return ExtractedCandidate(file_name=file_name, parse_error="PDF contains 0 pages")

        page_texts = []
        for i, page in enumerate(reader.pages):
            try:
                page_text = page.extract_text() or ""
                page_texts.append(page_text)
            except Exception as page_err:
                logger.warning(f"Error reading page {i} of {file_name}: {page_err}")
                continue

        full_text = "\n".join(page_texts)
        cleaned_text = clean_extracted_text(full_text)

        if not cleaned_text:
            return ExtractedCandidate(
                file_name=file_name,
                parse_error="No extractable text found (scanned or image-only PDF)"
            )

        return ExtractedCandidate(
            file_name=file_name,
            raw_text=cleaned_text
        )

    except Exception as e:
        logger.error(f"Failed to parse PDF {file_name}: {e}")
        return ExtractedCandidate(
            file_name=file_name,
            parse_error=f"PDF parsing error: {type(e).__name__}: {str(e)}"
        )
