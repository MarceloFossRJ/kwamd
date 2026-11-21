"""Conversion of a Source into Markdown text.

This is the only module that knows about PyMuPDF4LLM, so the converter can be
swapped or augmented (e.g. with OCR) without touching the CLI.
"""

from pathlib import Path

import pymupdf4llm


def convert(source: Path) -> str:
    """Return the Markdown for the whole Source as one continuous document."""
    markdown: str = pymupdf4llm.to_markdown(
        str(source),
        write_images=False,
        embed_images=False,
        page_separators=False,
        use_ocr=False,
        show_progress=False,
    )
    return markdown
