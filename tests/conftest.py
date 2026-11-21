"""Shared fixtures: build Source PDFs on the fly with PyMuPDF."""

from collections.abc import Callable, Sequence
from pathlib import Path

import pymupdf
import pytest

type PageSpec = str | None
"""Text for one page; ``None`` means an image-only page with no text."""

type MakePdf = Callable[..., Path]


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
def make_pdf() -> MakePdf:
    def _make(
        path: Path,
        pages: Sequence[PageSpec] = ("Hello world",),
        *,
        password: str | None = None,
    ) -> Path:
        doc = pymupdf.open()
        for spec in pages:
            if spec is None:
                _image_only_page(doc)
            else:
                _text_page(doc, spec)
        if password is None:
            doc.save(path)
        else:
            doc.save(
                path,
                encryption=pymupdf.PDF_ENCRYPT_AES_256,
                owner_pw=password,
                user_pw=password,
            )
        doc.close()
        return path

    return _make
