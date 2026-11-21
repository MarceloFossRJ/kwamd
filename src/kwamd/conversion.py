"""Conversion of a Source into Markdown text.

This is the only module that knows about PyMuPDF4LLM, so the converter can be
swapped or augmented (e.g. with OCR) without touching the CLI.
"""

from pathlib import Path

import pymupdf
import pymupdf4llm


def convert(source: Path, password: str | None = None) -> str:
    """Return the Markdown for the whole Source as one continuous document."""
    with pymupdf.open(source) as doc:
        if password is not None:
            doc.authenticate(password)
        markdown: str = pymupdf4llm.to_markdown(
            doc,
            write_images=False,
            embed_images=False,
            page_separators=False,
            use_ocr=False,
            show_progress=False,
        )
    return markdown
