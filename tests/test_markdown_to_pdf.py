"""Behaviour of ``kwamd`` for a Markdown Source, tested through ``main(argv)``."""

import unicodedata
from pathlib import Path
from typing import Any

import markdown_it
import pymupdf
import pytest

from kwamd import main

from .conftest import MakeSource, assert_failed_with_one_line, stderr_lines


def pdf_text(path: Path) -> str:
    """The PDF's text, NFKC-normalised: ligatures such as "ﬁ" and Arabic
    presentation forms come back as the plain characters that were written."""
    with pymupdf.open(path) as doc:
        return unicodedata.normalize("NFKC", "".join(str(page.get_text()) for page in doc))


def test_markdown_source_becomes_pdf_target_in_current_folder(
    workdir: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    elsewhere = tmp_path / "notes-folder"
    elsewhere.mkdir()
    source = elsewhere / "notes.md"
    source.write_text("# Meeting notes\n\nWe agreed on the plan.\n", encoding="utf-8")

    exit_code = main([str(source)])

    target = workdir / "notes.pdf"
    assert exit_code == 0
    assert capsys.readouterr().out == f"{target}\n"
    text = pdf_text(target)
    assert "Meeting notes" in text
    assert "We agreed on the plan." in text
    assert not (elsewhere / "notes.pdf").exists()


def test_markdown_source_that_is_not_utf8_fails(
    workdir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = workdir / "notes.md"
    source.write_bytes("# Café\n".encode("latin-1"))

    exit_code = main([str(source)])

    assert exit_code == 1
    assert_failed_with_one_line(capsys, workdir, "not UTF-8 text", "notes.md", target_glob="*.pdf")


@pytest.mark.parametrize("content", ["", " \n\t\n"], ids=["empty", "whitespace"])
def test_empty_markdown_source_fails(
    workdir: Path, capsys: pytest.CaptureFixture[str], content: str
) -> None:
    source = workdir / "notes.md"
    source.write_text(content, encoding="utf-8")

    exit_code = main([str(source)])

    assert exit_code == 1
    assert_failed_with_one_line(capsys, workdir, "Source is empty", "notes.md", target_glob="*.pdf")


def test_byte_order_mark_is_accepted_and_not_rendered(workdir: Path) -> None:
    source = workdir / "notes.md"
    source.write_bytes(b"\xef\xbb\xbf# Agenda\n\nItems.\n")

    exit_code = main([str(source)])

    assert exit_code == 0
    text = pdf_text(workdir / "notes.pdf")
    assert "Agenda" in text
    assert "#" not in text
    assert "﻿" not in text


@pytest.mark.parametrize("name", ["NOTES.MD", "notes.markdown", "Notes.Markdown"])
def test_markdown_extension_is_case_insensitive(workdir: Path, name: str) -> None:
    source = workdir / name
    source.write_text("Hello\n", encoding="utf-8")

    exit_code = main([str(source)])

    assert exit_code == 0
    assert "Hello" in pdf_text(workdir / f"{source.stem}.pdf")


def test_existing_pdf_target_is_never_overwritten_and_gets_numbered(
    workdir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = workdir / "notes.md"
    source.write_text("Fresh\n", encoding="utf-8")
    (workdir / "notes.pdf").write_bytes(b"keep me")

    exit_code = main([str(source)])

    assert exit_code == 0
    assert (workdir / "notes.pdf").read_bytes() == b"keep me"
    numbered = workdir / "notes (1).pdf"
    assert "Fresh" in pdf_text(numbered)
    assert capsys.readouterr().out == f"{numbered}\n"


def test_folder_and_explicit_targets_follow_v1_rules(workdir: Path) -> None:
    source = workdir / "notes.md"
    source.write_text("Hello\n", encoding="utf-8")
    folder = workdir / "out"
    folder.mkdir()

    assert main([str(source), str(folder)]) == 0
    assert main([str(source), str(folder / "report.txt")]) == 0

    assert sorted(p.name for p in folder.iterdir()) == ["notes.pdf", "report.txt"]
    assert "Hello" in pdf_text(folder / "report.txt")


def test_pdf_named_like_markdown_converts_to_markdown(
    workdir: Path, make_source: MakeSource, capsys: pytest.CaptureFixture[str]
) -> None:
    source = make_source(workdir / "report.md", ["Hello world"])

    exit_code = main([str(source)])

    target = workdir / "report (1).md"
    assert exit_code == 0
    assert "Hello world" in target.read_text(encoding="utf-8")
    assert capsys.readouterr().out == f"{target}\n"


@pytest.mark.parametrize("name", ["notes.txt", "notes.docx", "README"])
def test_text_source_without_markdown_extension_fails(
    workdir: Path, capsys: pytest.CaptureFixture[str], name: str
) -> None:
    source = workdir / name
    source.write_text("# Looks like Markdown\n", encoding="utf-8")

    exit_code = main([str(source)])

    assert exit_code == 1
    assert_failed_with_one_line(
        capsys, workdir, "neither a PDF nor Markdown", name, target_glob="*.pdf"
    )
    assert sorted(p.name for p in workdir.iterdir()) == [name]


def test_source_kind_is_checked_before_target(
    workdir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = workdir / "notes.txt"
    source.write_text("Hello\n", encoding="utf-8")

    exit_code = main([str(source), "missing/out.pdf"])

    assert exit_code == 1
    assert_failed_with_one_line(capsys, workdir, "neither a PDF nor Markdown", target_glob="*.pdf")


def test_target_is_checked_before_markdown_is_read(
    workdir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = workdir / "notes.md"
    source.write_bytes(b"\xff\xfe not utf-8")

    exit_code = main([str(source), "missing/out.pdf"])

    assert exit_code == 1
    assert_failed_with_one_line(capsys, workdir, "folder does not exist", target_glob="*.pdf")


def test_table_renders_as_a_table(workdir: Path) -> None:
    source = workdir / "notes.md"
    source.write_text(
        "| Name | Role |\n| ---- | ---- |\n| Ana | Lead |\n| Bo | Dev |\n", encoding="utf-8"
    )

    assert main([str(source)]) == 0

    text = pdf_text(workdir / "notes.pdf")
    for cell in ["Name", "Role", "Ana", "Lead", "Bo", "Dev"]:
        assert cell in text
    assert "|" not in text
    assert "----" not in text


def test_strikethrough_renders_without_its_markers(workdir: Path) -> None:
    source = workdir / "notes.md"
    source.write_text("The ~~old~~ new plan.\n", encoding="utf-8")

    assert main([str(source)]) == 0

    text = pdf_text(workdir / "notes.pdf")
    assert "old" in text
    assert "~~" not in text


def test_raw_html_shows_as_literal_text(workdir: Path) -> None:
    source = workdir / "notes.md"
    source.write_text(
        'Before <span style="color:red">inline</span> after.\n\n<div>block</div>\n',
        encoding="utf-8",
    )

    assert main([str(source)]) == 0

    text = pdf_text(workdir / "notes.pdf")
    assert '<span style="color:red">inline</span>' in text
    assert "<div>block</div>" in text


def test_commonmark_elements_render_without_their_markers(workdir: Path) -> None:
    source = workdir / "notes.md"
    source.write_text(
        "## Section\n\n"
        "Some **bold**, *italic* and `inline()` text.\n\n"
        "- first item\n- second item\n\n"
        "1. step one\n2. step two\n\n"
        "> quoted words\n\n"
        "---\n\n"
        "```\ndef block():\n    return 1\n```\n",
        encoding="utf-8",
    )

    assert main([str(source)]) == 0

    text = pdf_text(workdir / "notes.pdf")
    for words in [
        "Section",
        "bold",
        "italic",
        "inline()",
        "first item",
        "step two",
        "quoted words",
        "def block():",
        "return 1",
    ]:
        assert words in text
    for marker in ["##", "**", "`", "> "]:
        assert marker not in text


def test_text_in_any_script_renders(workdir: Path) -> None:
    lines = ["Café über straße", "Ελληνικά", "Привет мир", "日本語の文章", "中文内容", "مرحبا"]
    source = workdir / "notes.md"
    source.write_text("\n\n".join(lines) + "\n", encoding="utf-8")

    assert main([str(source)]) == 0

    text = pdf_text(workdir / "notes.pdf")
    for line in lines:
        assert line in text


def test_web_links_and_heading_links_are_clickable(workdir: Path) -> None:
    source = workdir / "notes.md"
    source.write_text(
        "See [the site](https://example.org/docs) and [the plan](#next-steps).\n\n"
        + "Filler paragraph.\n\n" * 80
        + "## Next steps\n\nShip it.\n",
        encoding="utf-8",
    )

    assert main([str(source)]) == 0

    with pymupdf.open(workdir / "notes.pdf") as doc:
        links = doc[0].get_links()
        [heading_page] = [p.number for p in doc if "Next steps" in str(p.get_text())]
    assert heading_page > 0
    # Story adds one link area per word, so compare where the links go, not how many.
    assert {link["uri"] for link in links if link["kind"] == pymupdf.LINK_URI} == {
        "https://example.org/docs"
    }
    assert {link["page"] for link in links if link["kind"] == pymupdf.LINK_GOTO} == {heading_page}


def test_link_to_a_missing_heading_renders_as_plain_text(
    workdir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = workdir / "notes.md"
    source.write_text("See [the plan](#nowhere).\n\n## Somewhere\n", encoding="utf-8")

    exit_code = main([str(source)])

    assert exit_code == 0
    assert capsys.readouterr().err == ""
    with pymupdf.open(workdir / "notes.pdf") as doc:
        assert "the plan" in str(doc[0].get_text())
        assert doc[0].get_links() == []


def _spans(path: Path) -> dict[str, dict[str, Any]]:
    """Each text span on the first page, keyed by its text."""
    with pymupdf.open(path) as doc:
        blocks = doc[0].get_text("dict")["blocks"]
    return {
        span["text"].strip(): span
        for block in blocks
        for line in block.get("lines", [])
        for span in line["spans"]
        if span["text"].strip()
    }


def test_pdf_has_the_fixed_look(workdir: Path) -> None:
    source = workdir / "notes.md"
    source.write_text("# Title\n\nBody text.\n\n```\ncode_here()\n```\n", encoding="utf-8")

    assert main([str(source)]) == 0

    target = workdir / "notes.pdf"
    with pymupdf.open(target) as doc:
        assert doc[0].rect == pymupdf.paper_rect("a4")
    spans = _spans(target)
    two_cm = 72 * 2 / 2.54
    body = spans["Body text."]
    assert body["size"] == pytest.approx(11, abs=0.1)
    assert "Charis" in str(body["font"])
    assert body["bbox"][0] == pytest.approx(two_cm, abs=1)
    assert spans["Title"]["size"] > body["size"]
    assert spans["Title"]["flags"] & pymupdf.TEXT_FONT_BOLD
    assert "Mono" in str(spans["code_here()"]["font"])


@pytest.mark.parametrize(
    "library", [(pymupdf, "Story"), (markdown_it.MarkdownIt, "parse")], ids=["layout", "parse"]
)
def test_rendering_failure_is_one_line_and_leaves_no_target(
    workdir: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    library: tuple[object, str],
) -> None:
    def broken(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("layout exploded\nwith a second line")

    monkeypatch.setattr(*library, broken)
    source = workdir / "notes.md"
    source.write_text("Hello\n", encoding="utf-8")

    exit_code = main([str(source)])

    assert exit_code == 1
    assert_failed_with_one_line(
        capsys, workdir, "Cannot render Source", "layout exploded", target_glob="*.pdf"
    )


def test_markdown_that_mentions_the_pdf_signature_is_still_markdown(workdir: Path) -> None:
    source = workdir / "notes.md"
    source.write_text("# File formats\n\nEvery PDF starts with `%PDF-1.7`.\n", encoding="utf-8")

    exit_code = main([str(source)])

    assert exit_code == 0
    assert "Every PDF starts with" in pdf_text(workdir / "notes.pdf")


def test_arabic_with_ligatures_is_drawn_in_an_arabic_font(workdir: Path) -> None:
    source = workdir / "notes.md"
    source.write_text("اللغة العربية\n", encoding="utf-8")

    assert main([str(source)]) == 0

    # Text extraction garbles the lam-alef ligature (U+FEFB becomes U+01C4
    # under NFKC), so check that a font able to shape Arabic drew it.
    with pymupdf.open(workdir / "notes.pdf") as doc:
        fonts = [font[3] for font in doc[0].get_fonts()]
    assert any("Arabic" in font for font in fonts), fonts


def test_interrupted_markdown_conversion_leaves_no_target(
    workdir: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    def interrupted(*_args: object, **_kwargs: object) -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr(pymupdf, "Story", interrupted)
    source = workdir / "notes.md"
    source.write_text("Hello\n", encoding="utf-8")

    exit_code = main([str(source)])

    assert exit_code == 130
    captured = capsys.readouterr()
    assert captured.out == ""
    assert stderr_lines(captured.err, workdir.parent) == ["kwamd: interrupted"]
    assert not list(workdir.glob("*.pdf"))


def _link_pages(path: Path) -> dict[str, int]:
    """Where each in-document link on the first page goes, keyed by its text."""
    with pymupdf.open(path) as doc:
        page = doc[0]
        return {
            str(page.get_textbox(link["from"])).strip(): link["page"]
            for link in page.get_links()
            if link["kind"] == pymupdf.LINK_GOTO
        }


def _page_of(path: Path, text: str) -> int:
    with pymupdf.open(path) as doc:
        [number] = [int(page.number) for page in doc if text in str(page.get_text())]
    return number


@pytest.mark.parametrize(
    ("link", "heading"),
    [("#café-menu", "Café menu"), ("#Next-Steps", "Next steps")],
    ids=["accented", "capitalised"],
)
def test_heading_links_match_like_github(workdir: Path, link: str, heading: str) -> None:
    source = workdir / "notes.md"
    source.write_text(
        f"Go [there]({link}).\n\n" + "Filler.\n\n" * 80 + f"## {heading}\n\nDone.\n",
        encoding="utf-8",
    )

    assert main([str(source)]) == 0

    target = workdir / "notes.pdf"
    assert _link_pages(target) == {"there": _page_of(target, heading)}


def test_repeated_headings_get_distinct_ids_like_github(workdir: Path) -> None:
    source = workdir / "notes.md"
    source.write_text(
        "[a](#plan) [b](#plan-1) [c](#plan-2)\n\n"
        "## Plan\n\nFirst.\n\n"
        + "Filler.\n\n" * 60
        + "## Plan-1\n\nSecond.\n\n"
        + "Filler.\n\n" * 60
        + "## Plan\n\nThird.\n",
        encoding="utf-8",
    )

    assert main([str(source)]) == 0

    target = workdir / "notes.pdf"
    assert _link_pages(target) == {
        "a": _page_of(target, "First."),
        "b": _page_of(target, "Second."),
        "c": _page_of(target, "Third."),
    }
