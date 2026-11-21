"""Checking that a Source can be converted, judged by content, never by extension."""

from dataclasses import dataclass
from pathlib import Path

import pymupdf

from kwamd.errors import KwamdError, PasswordRequired, WrongPassword


@dataclass(frozen=True)
class CheckedSource:
    """A Source that can be converted."""

    scanned: bool
    """Whether it is a Scanned Source: fewer than half its pages have extractable text."""

    password: str | None
    """The password that opened it, if it needed one."""


def check_source(source: Path, password: str | None = None) -> CheckedSource:
    """Raise ``KwamdError`` if ``source`` cannot be converted.

    A password-protected Source raises ``PasswordRequired`` when ``password``
    is ``None`` and ``WrongPassword`` when it does not open the Source.
    """
    if source.is_dir():
        raise KwamdError(f"Source is a folder, not a PDF: {source}")
    if not source.exists():
        raise KwamdError(f"Source does not exist: {source}")
    try:
        source.open("rb").close()
    except OSError as error:
        raise KwamdError(f"Cannot read Source {source}: {error.strerror}") from None

    # MuPDF otherwise prints its own diagnostics to stderr for unreadable files.
    pymupdf.TOOLS.mupdf_display_errors(False)
    try:
        doc = pymupdf.open(source)
    except pymupdf.FileDataError:
        doc = None
    if doc is None or not doc.is_pdf:
        raise KwamdError(f"Source is not a PDF: {source}")
    with doc:
        if doc.needs_pass:
            if password is None:
                raise PasswordRequired(f"Source is password-protected: {source}")
            if not doc.authenticate(password):
                raise WrongPassword(f"Wrong password for Source: {source}")
        else:
            password = None
        page_count: int = doc.page_count
        if page_count == 0:
            raise KwamdError(f"Source has no pages: {source}")
        pages_with_text = sum(
            1 for i in range(page_count) if str(doc.load_page(i).get_text()).strip()
        )
    return CheckedSource(scanned=pages_with_text * 2 < page_count, password=password)
