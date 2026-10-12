"""Local, explainable PDF review helpers for DisclosureAI.

This module reports structural document cues only. It never attempts to infer
whether text was AI-generated or whether a student used AI.
"""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
import re

from pypdf import PdfReader


MAX_PDF_BYTES = 10 * 1024 * 1024
MAX_PDF_PAGES = 60


class DocumentReviewError(ValueError):
    """A PDF cannot be safely or usefully reviewed in the current session."""


@dataclass(frozen=True)
class DocumentInsights:
    """Non-judgmental, document-derived facts and reflection prompts."""

    filename: str
    page_count: int
    word_count: int
    extracted_characters: int
    text_detected: bool
    code_like_content: bool
    references_section: bool
    heading_count: int
    observations: tuple[str, ...]
    reflection_prompts: tuple[str, ...]


def analyze_document_text(text: str, filename: str, page_count: int) -> DocumentInsights:
    """Analyze extracted text for explainable document structure, not AI use."""
    cleaned_text = "\n".join(line.rstrip() for line in (text or "").splitlines()).strip()
    words = re.findall(r"[\w'-]+", cleaned_text, flags=re.UNICODE)
    word_count = len(words)
    code_like_content = bool(
        re.search(
            r"(?im)^\s*(?:def |class |import |from |function |const |let |public |private |"
            r"#include|select\s|create\s+table|for\s*\(|while\s*\(|if\s*\()",
            cleaned_text,
        )
    ) or cleaned_text.count("{") >= 2
    references_section = bool(
        re.search(r"(?im)^\s*(?:references|bibliography|works cited)\s*$", cleaned_text)
    )
    heading_count = len(
        re.findall(
            r"(?m)^\s*(?:\d+(?:\.\d+)*[.)]?\s+|[A-Z][A-Za-z ]{2,58}$)",
            cleaned_text,
        )
    )

    observations: list[str] = []
    prompts: list[str] = [
        "Use your own recollection—not this review—to disclose AI assistance accurately."
    ]
    if code_like_content:
        observations.append("Code-like structure was found.")
        prompts.append(
            "If AI helped write, explain, debug, or refactor code, consider selecting Coding."
        )
    if references_section:
        observations.append("A references or bibliography heading was found.")
        prompts.append(
            "If AI helped find, compare, explain, or summarize sources, consider Research or Summarization."
        )
    if heading_count >= 3:
        observations.append(f"{heading_count} section-like headings were found.")
        prompts.append(
            "If AI helped reorganize or revise these sections, consider selecting Editing."
        )
    if word_count >= 800:
        observations.append("This is a longer document.")
        prompts.append(
            "Consider whether AI assistance was isolated or repeated across several parts before choosing extent."
        )
    if not observations:
        observations.append("No specific structural cues were found.")

    return DocumentInsights(
        filename=filename,
        page_count=page_count,
        word_count=word_count,
        extracted_characters=len(cleaned_text),
        text_detected=bool(cleaned_text),
        code_like_content=code_like_content,
        references_section=references_section,
        heading_count=heading_count,
        observations=tuple(observations),
        reflection_prompts=tuple(prompts),
    )


def review_pdf(file_bytes: bytes, filename: str) -> DocumentInsights:
    """Extract a small text-based PDF in memory and return structural insights."""
    if not file_bytes:
        raise DocumentReviewError("The uploaded PDF is empty.")
    if len(file_bytes) > MAX_PDF_BYTES:
        raise DocumentReviewError("Choose a PDF smaller than 10 MB for this local review.")

    try:
        reader = PdfReader(BytesIO(file_bytes), strict=False)
        if reader.is_encrypted and not reader.decrypt(""):
            raise DocumentReviewError("This PDF is password-protected and cannot be reviewed.")
        page_count = len(reader.pages)
        if page_count > MAX_PDF_PAGES:
            raise DocumentReviewError("Choose a PDF with 60 pages or fewer for this review.")
        extracted_text = "\n".join(page.extract_text() or "" for page in reader.pages)
    except DocumentReviewError:
        raise
    except Exception as error:
        raise DocumentReviewError("This file could not be read as a PDF.") from error

    return analyze_document_text(extracted_text, filename, page_count)


def extent_from_scope(scope: str) -> str | None:
    """Map an explicit student self-assessment to an editable extent suggestion."""
    scope_to_extent = {
        "One isolated supporting task or section": "Limited",
        "Several described tasks or sections": "Moderate",
        "Major sections or repeated work": "Substantial",
    }
    return scope_to_extent.get(scope)
