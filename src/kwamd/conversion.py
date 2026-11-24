"""Conversion of a Source into Markdown text.

This is the only module that knows about PyMuPDF4LLM, so the converter can be
swapped or augmented (e.g. with OCR) without touching the CLI.
"""

import pymupdf4llm

from kwamd.errors import KwamdError, one_line
from kwamd.source import Source


def convert(source: Source) -> str:
    """Return the Markdown for the whole Source as one continuous document."""
    try:
        markdown: str = pymupdf4llm.to_markdown(
            source.document,
            write_images=False,
            embed_images=False,
            page_separators=False,
            use_ocr=False,
            show_progress=False,
        )
    except Exception as error:
        # PyMuPDF4LLM documents no exception types; any failure is the Source's.
        raise KwamdError(f"Cannot convert Source {source.path}: {one_line(error)}") from None
    return markdown
