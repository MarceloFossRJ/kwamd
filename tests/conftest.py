"""Shared fixtures: build Sources (and invalid ones) on the fly with PyMuPDF."""

import unicodedata
from collections.abc import Sequence
from pathlib import Path
from typing import Protocol

import pymupdf
import pytest

type PageSpec = str | None
"""Text for one page; ``None`` means an image-only page with no text."""


class MakeSource(Protocol):
    """Build a PDF at ``path`` with one page per entry of ``pages``; return ``path``.

    ``password`` is needed to open the PDF; ``owner_password`` alone encrypts it
    but lets anyone open it.
    """

    def __call__(
        self,
        path: Path,
        pages: Sequence[PageSpec] = ...,
        *,
        password: str | None = None,
        owner_password: str | None = None,
    ) -> Path: ...


def _image_only_page(doc: pymupdf.Document) -> None:
    page = doc.new_page()
    pix = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 64, 64), False)
    pix.set_rect(pix.irect, (200, 30, 30))
    page.insert_image(pymupdf.Rect(72, 72, 300, 300), pixmap=pix)


def _text_page(doc: pymupdf.Document, text: str) -> None:
    page = doc.new_page()
    y = 72.0
    for line in text.splitlines():
        if line.startswith("# "):
            page.insert_text((72, y), line[2:], fontsize=24, fontname="hebo")
            y += 36
        else:
            page.insert_text((72, y), line, fontsize=11)
            y += 16


@pytest.fixture
def make_source() -> MakeSource:
    def _make(
        path: Path,
        pages: Sequence[PageSpec] = ("Hello world",),
        *,
        password: str | None = None,
        owner_password: str | None = None,
    ) -> Path:
        doc = pymupdf.open()
        for spec in pages:
            if spec is None:
                _image_only_page(doc)
            else:
                _text_page(doc, spec)
        if password is None and owner_password is None:
            doc.save(path)
        else:
            # ``password`` is needed to open it; ``owner_password`` only restricts editing.
            doc.save(
                path,
                encryption=pymupdf.PDF_ENCRYPT_AES_256,
                owner_pw=owner_password or password,
                user_pw=password or "",
            )
        doc.close()
        return path

    return _make


def stderr_lines(err: str, tmp_path: Path) -> list[str]:
    """Split captured stderr into lines, with ``tmp_path`` shown as ``<tmp>``.

    pytest names ``tmp_path`` after the test, so without this a check like
    ``"scanned" in line`` would also match a test whose name says "scanned".
    """
    return err.replace(str(tmp_path), "<tmp>").splitlines()


@pytest.fixture
def workdir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A fresh current folder for the run, inside ``tmp_path``."""
    cwd = tmp_path / "cwd"
    cwd.mkdir()
    monkeypatch.chdir(cwd)
    return cwd


def assert_failed_with_one_line(
    capsys: pytest.CaptureFixture[str], workdir: Path, *fragments: str, target_glob: str = "*.md"
) -> None:
    """Check the run failed with one ``kwamd: error:`` line containing ``fragments``,
    printed nothing on stdout, and left no Target matching ``target_glob`` behind."""
    captured = capsys.readouterr()
    assert captured.out == ""
    [line] = stderr_lines(captured.err, workdir.parent)
    assert line.startswith("kwamd: error: ")
    for fragment in fragments:
        assert fragment in line
    assert not list(workdir.glob(target_glob))


# Reading a PDF Target back. Assert on its text through pdf_text: raw
# get_text() returns ligatures such as "ﬁ" and Arabic presentation forms.


def pdf_text(path: Path) -> str:
    """The PDF's text, NFKC-normalised: ligatures such as "ﬁ" and Arabic
    presentation forms come back as the plain characters that were written."""
    with pymupdf.open(path) as doc:
        return unicodedata.normalize("NFKC", "".join(str(page.get_text()) for page in doc))


def link_pages(path: Path) -> dict[str, int]:
    """Where each in-document link on the first page goes, keyed by its text."""
    with pymupdf.open(path) as doc:
        page = doc[0]
        return {
            str(page.get_textbox(link["from"])).strip(): link["page"]
            for link in page.get_links()
            if link["kind"] == pymupdf.LINK_GOTO
        }


def page_of(path: Path, text: str) -> int:
    with pymupdf.open(path) as doc:
        [number] = [int(page.number) for page in doc if text in str(page.get_text())]
    return number


def image_count(path: Path) -> int:
    with pymupdf.open(path) as doc:
        return sum(len(page.get_images()) for page in doc)
