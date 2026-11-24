"""Settings kwamd applies to MuPDF, shared by every module that calls PyMuPDF."""

import pymupdf


def quiet_mupdf() -> None:
    """Stop MuPDF printing its own diagnostics to stderr, so every failure stays
    one ``kwamd:`` line. The setting is process-wide, which suits a one-shot CLI."""
    pymupdf.TOOLS.mupdf_display_errors(False)
