"""Recognising and reading a Source: a PDF Source by content, a Markdown Source by
extension (read as text, without its front matter)."""

from collections.abc import Iterable
from pathlib import Path
from types import TracebackType
from typing import Literal, Self

import pymupdf

from kwamd.errors import KwamdError
from kwamd.mupdf import quiet_mupdf


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
    """Open the PDF Source at ``path``, or raise ``KwamdError`` saying why it cannot be converted.

    ``path`` has already passed ``source_kind``, so it is a readable file.
    ``passwords`` is only consumed for a password-protected Source: each one is
    tried in turn until one opens it. It may be lazy (e.g. prompting a person).
    """
    quiet_mupdf()
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


type SourceKind = Literal["pdf", "markdown"]

TARGET_SUFFIX: dict[SourceKind, str] = {"pdf": ".md", "markdown": ".pdf"}
"""The default Target's extension for each kind of Source."""

MARKDOWN_SUFFIXES = (".md", ".markdown")
PDF_SIGNATURE = b"%PDF-"
SIGNATURE_WINDOW = 1024
"""PDF readers accept a signature anywhere in the first kilobyte."""


def source_kind(path: Path) -> SourceKind:
    """Say which kind of Source ``path`` is, without opening it as a document.

    A PDF Source is known by its content, a Markdown Source by its extension.
    """
    if path.is_dir():
        raise KwamdError(f"Source is a folder, not a PDF: {path}")
    if not path.exists():
        raise KwamdError(f"Source does not exist: {path}")
    try:
        with path.open("rb") as file:
            head = file.read(SIGNATURE_WINDOW)
    except OSError as error:
        raise _read_failure(path, error) from None
    is_markdown_name = path.suffix.lower() in MARKDOWN_SUFFIXES
    # Markdown can mention "%PDF-" in its text, so a Markdown-named file only
    # counts as a PDF when the signature is its very first bytes (ADR 0001).
    if head.startswith(PDF_SIGNATURE) or (not is_markdown_name and PDF_SIGNATURE in head):
        return "pdf"
    if is_markdown_name:
        return "markdown"
    raise KwamdError(f"Source is neither a PDF nor Markdown: {path}")


def read_markdown_source(path: Path) -> str:
    """Return the text of a Markdown Source, without its front matter."""
    try:
        content = path.read_bytes()
    except OSError as error:
        raise _read_failure(path, error) from None
    try:
        text = content.decode("utf-8-sig")  # a leading byte-order mark is fine
    except UnicodeDecodeError:
        raise KwamdError(f"Source is not UTF-8 text: {path}") from None
    text = _without_front_matter(text)
    if not text.strip():
        raise KwamdError(f"Source is empty: {path}")
    return text


def _without_front_matter(markdown: str) -> str:
    """``markdown`` without YAML front matter: when the first line is exactly
    ``---``, everything up to and including the next such line. Without a
    closing ``---`` it is returned whole.

    Lines end only at ``\n`` (optionally after ``\r``), as in Markdown, not at
    every character ``str.splitlines`` treats as a break.
    """
    lines = markdown.split("\n")
    if lines[0].removesuffix("\r") != "---":
        return markdown
    for index, line in enumerate(lines[1:], start=1):
        if line.removesuffix("\r") == "---":
            return "\n".join(lines[index + 1 :])
    return markdown


def _read_failure(path: Path, error: OSError) -> KwamdError:
    return KwamdError(f"Cannot read Source {path}: {error.strerror}")
