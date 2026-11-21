"""Opening a Source, judged by content, never by extension."""

from collections.abc import Iterable
from pathlib import Path
from types import TracebackType
from typing import Self

import pymupdf

from kwamd.errors import KwamdError


class Source:
    """An opened, unlocked Source, ready to convert. Use it as a context manager."""

    def __init__(self, path: Path, document: pymupdf.Document) -> None:
        self.path = path
        self.document = document
        page_count: int = document.page_count
        pages_with_text = sum(
            1 for i in range(page_count) if str(document.load_page(i).get_text()).strip()
        )
        self.scanned = pages_with_text * 2 < page_count
        """Whether it is a Scanned Source: fewer than half its pages have extractable text."""

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.document.close()


def open_source(path: Path, passwords: Iterable[str]) -> Source:
    """Open ``path`` as a Source, or raise ``KwamdError`` saying why it cannot be converted.

    ``passwords`` is only consumed for a password-protected Source: each one is
    tried in turn until one opens it. It may be lazy (e.g. prompting a person).
    """
    if path.is_dir():
        raise KwamdError(f"Source is a folder, not a PDF: {path}")
    if not path.exists():
        raise KwamdError(f"Source does not exist: {path}")
    try:
        path.open("rb").close()
    except OSError as error:
        raise KwamdError(f"Cannot read Source {path}: {error.strerror}") from None

    # MuPDF otherwise prints its own diagnostics to stderr for unreadable files.
    pymupdf.TOOLS.mupdf_display_errors(False)
    try:
        document = pymupdf.open(path)
    except pymupdf.FileDataError:
        raise KwamdError(f"Source is not a PDF: {path}") from None
    try:
        if not document.is_pdf:
            raise KwamdError(f"Source is not a PDF: {path}")
        if document.needs_pass and not any(document.authenticate(p) for p in passwords):
            raise KwamdError(f"Wrong password for Source: {path}")
        if document.page_count == 0:
            raise KwamdError(f"Source has no pages: {path}")
        return Source(path, document)
    except BaseException:
        document.close()
        raise
