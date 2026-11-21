"""Behaviour of the ``kwamd`` command, tested through ``main(argv)``."""

import getpass
import sys
from pathlib import Path

import pytest

from kwamd import main

from .conftest import MakePdf


@pytest.fixture
def workdir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    cwd = tmp_path / "cwd"
    cwd.mkdir()
    monkeypatch.chdir(cwd)
    return cwd


def test_default_target_is_source_stem_in_current_folder(
    workdir: Path, tmp_path: Path, make_pdf: MakePdf, capsys: pytest.CaptureFixture[str]
) -> None:
    elsewhere = tmp_path / "downloads"
    elsewhere.mkdir()
    source = make_pdf(elsewhere / "report.pdf", ["Hello world"])

    exit_code = main([str(source)])

    target = workdir / "report.md"
    assert exit_code == 0
    assert "Hello world" in target.read_text(encoding="utf-8")
    assert not (elsewhere / "report.md").exists()
    out = capsys.readouterr().out
    assert out == f"{target}\n"


@pytest.mark.parametrize("name", ["notes.md", "notes.txt", "notes"])
def test_explicit_target_is_used_exactly_as_given(
    workdir: Path, make_pdf: MakePdf, capsys: pytest.CaptureFixture[str], name: str
) -> None:
    source = make_pdf(workdir / "report.pdf", ["Hello world"])
    target_folder = workdir / "out"
    target_folder.mkdir()

    exit_code = main([str(source), str(target_folder / name)])

    assert exit_code == 0
    assert sorted(p.name for p in target_folder.iterdir()) == [name]
    assert "Hello world" in (target_folder / name).read_text(encoding="utf-8")
    assert capsys.readouterr().out == f"{target_folder / name}\n"


def test_folder_target_gets_source_stem_inside_it(
    workdir: Path, make_pdf: MakePdf, capsys: pytest.CaptureFixture[str]
) -> None:
    source = make_pdf(workdir / "report.pdf", ["Hello world"])
    target_folder = workdir / "out"
    target_folder.mkdir()

    exit_code = main([str(source), str(target_folder)])

    assert exit_code == 0
    assert "Hello world" in (target_folder / "report.md").read_text(encoding="utf-8")
    assert capsys.readouterr().out == f"{target_folder / 'report.md'}\n"


def test_existing_target_is_never_overwritten_and_gets_numbered(
    workdir: Path, make_pdf: MakePdf, capsys: pytest.CaptureFixture[str]
) -> None:
    source = make_pdf(workdir / "report.pdf", ["Hello world"])
    (workdir / "report.md").write_text("hand edited", encoding="utf-8")

    exit_code = main([str(source)])

    assert exit_code == 0
    assert (workdir / "report.md").read_text(encoding="utf-8") == "hand edited"
    numbered = workdir / "report (1).md"
    assert "Hello world" in numbered.read_text(encoding="utf-8")
    assert capsys.readouterr().out == f"{numbered}\n"


@pytest.mark.parametrize(
    ("existing", "requested", "expected"),
    [
        # lowest free number is reused, even with a gap
        (["report.md", "report (2).md"], None, "report (1).md"),
        (["report.md", "report (1).md", "report (2).md"], None, "report (3).md"),
        # explicit Target is numbered the same way
        (["notes.md"], "notes.md", "notes (1).md"),
        # extension-less Target
        (["notes"], "notes", "notes (1)"),
        # folder Target
        (["out/report.md"], "out", "out/report (1).md"),
    ],
)
def test_numbering_picks_lowest_free_number_for_every_kind_of_target(
    workdir: Path,
    make_pdf: MakePdf,
    capsys: pytest.CaptureFixture[str],
    existing: list[str],
    requested: str | None,
    expected: str,
) -> None:
    source = make_pdf(workdir / "report.pdf", ["Hello world"])
    (workdir / "out").mkdir()
    for name in existing:
        (workdir / name).write_text("keep me", encoding="utf-8")

    argv = [str(source)] if requested is None else [str(source), requested]
    exit_code = main(argv)

    assert exit_code == 0
    for name in existing:
        assert (workdir / name).read_text(encoding="utf-8") == "keep me"
    assert "Hello world" in (workdir / expected).read_text(encoding="utf-8")
    assert capsys.readouterr().out.strip().endswith(expected)


def test_target_in_missing_folder_fails_without_creating_it(
    workdir: Path, make_pdf: MakePdf, capsys: pytest.CaptureFixture[str]
) -> None:
    source = make_pdf(workdir / "report.pdf", ["Hello world"])

    exit_code = main([str(source), "missing/dir/notes.md"])

    assert exit_code == 1
    assert not (workdir / "missing").exists()
    _assert_failed_with_one_line(capsys, workdir, "folder does not exist", "missing")


def _assert_failed_with_one_line(
    capsys: pytest.CaptureFixture[str], workdir: Path, *fragments: str
) -> None:
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.count("\n") == 1
    for fragment in fragments:
        assert fragment in captured.err
    assert not list(workdir.glob("*.md"))


def test_missing_source_fails(workdir: Path, capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["nope.pdf"])

    assert exit_code == 1
    _assert_failed_with_one_line(capsys, workdir, "does not exist", "nope.pdf")


@pytest.mark.parametrize(
    "content",
    [b"PK\x03\x04 this is really a docx", b"just some text\n", b""],
    ids=["zip", "text", "empty-file"],
)
def test_source_that_is_not_a_pdf_fails(
    workdir: Path, capsys: pytest.CaptureFixture[str], content: bytes
) -> None:
    fake = workdir / "fake.pdf"
    fake.write_bytes(content)

    exit_code = main([str(fake)])

    assert exit_code == 1
    _assert_failed_with_one_line(capsys, workdir, "not a PDF", "fake.pdf")


def test_real_pdf_without_pdf_extension_is_accepted(workdir: Path, make_pdf: MakePdf) -> None:
    source = make_pdf(workdir / "download", ["Hello world"])

    exit_code = main([str(source)])

    assert exit_code == 0
    assert "Hello world" in (workdir / "download.md").read_text(encoding="utf-8")


class FakeTerminal:
    """Stands in for the person at the terminal: answers password prompts in order."""

    def __init__(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self.answers: list[str] = []
        self.prompts: list[str] = []
        monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
        monkeypatch.setattr(getpass, "getpass", self._getpass)

    def _getpass(self, prompt: str = "Password: ", stream: object = None) -> str:
        self.prompts.append(prompt)
        return self.answers.pop(0)


@pytest.fixture
def terminal(monkeypatch: pytest.MonkeyPatch) -> FakeTerminal:
    return FakeTerminal(monkeypatch)


def test_password_protected_source_converts_with_the_password_typed_at_the_prompt(
    workdir: Path, make_pdf: MakePdf, terminal: FakeTerminal, capsys: pytest.CaptureFixture[str]
) -> None:
    source = make_pdf(workdir / "secret.pdf", ["Hello world"], password="hunter2")
    terminal.answers = ["hunter2"]

    exit_code = main([str(source)])

    assert exit_code == 0
    assert terminal.prompts == ["Password for secret.pdf: "]
    assert "Hello world" in (workdir / "secret.md").read_text(encoding="utf-8")
    assert capsys.readouterr().out == f"{workdir / 'secret.md'}\n"


def test_wrong_password_is_asked_again(
    workdir: Path, make_pdf: MakePdf, terminal: FakeTerminal, capsys: pytest.CaptureFixture[str]
) -> None:
    source = make_pdf(workdir / "secret.pdf", ["Hello world"], password="hunter2")
    terminal.answers = ["nope", "", "hunter2"]

    exit_code = main([str(source)])

    assert exit_code == 0
    assert len(terminal.prompts) == 3
    assert "Hello world" in (workdir / "secret.md").read_text(encoding="utf-8")
    assert capsys.readouterr().err.count("try again") == 2


def test_three_wrong_passwords_fail(
    workdir: Path, make_pdf: MakePdf, terminal: FakeTerminal, capsys: pytest.CaptureFixture[str]
) -> None:
    source = make_pdf(workdir / "secret.pdf", ["Hello world"], password="hunter2")
    terminal.answers = ["a", "b", "c", "hunter2"]

    exit_code = main([str(source)])

    assert exit_code == 1
    assert len(terminal.prompts) == 3
    err = capsys.readouterr().err
    assert err.splitlines()[-1].startswith("kwamd: error: Wrong password")
    assert "secret.pdf" in err.splitlines()[-1]
    assert not list(workdir.glob("*.md"))


def test_password_protected_source_fails_without_a_terminal_to_ask(
    workdir: Path,
    make_pdf: MakePdf,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    source = make_pdf(workdir / "secret.pdf", ["Hello world"], password="hunter2")
    monkeypatch.setattr(sys.stdin, "isatty", lambda: False)

    def no_prompt(*args: object, **kwargs: object) -> str:
        raise AssertionError("must not prompt without a terminal")

    monkeypatch.setattr(getpass, "getpass", no_prompt)

    exit_code = main([str(source)])

    assert exit_code == 1
    _assert_failed_with_one_line(capsys, workdir, "password-protected", "terminal", "secret.pdf")


def test_source_with_only_an_owner_password_converts_without_asking(
    workdir: Path, make_pdf: MakePdf, terminal: FakeTerminal
) -> None:
    source = make_pdf(workdir / "locked.pdf", ["Hello world"], owner_password="owner")

    exit_code = main([str(source)])

    assert exit_code == 0
    assert terminal.prompts == []
    assert "Hello world" in (workdir / "locked.md").read_text(encoding="utf-8")


# PyMuPDF refuses to save a document with zero pages, so write one by hand.
ZERO_PAGE_PDF = (
    b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
    b"2 0 obj\n<< /Type /Pages /Kids [] /Count 0 >>\nendobj\n"
    b"trailer\n<< /Root 1 0 R >>\n%%EOF\n"
)


def test_source_with_no_pages_fails(workdir: Path, capsys: pytest.CaptureFixture[str]) -> None:
    source = workdir / "blank.pdf"
    source.write_bytes(ZERO_PAGE_PDF)

    exit_code = main([str(source)])

    assert exit_code == 1
    _assert_failed_with_one_line(capsys, workdir, "no pages", "blank.pdf")


@pytest.mark.parametrize(
    "pages",
    [[None], [None, None, "Hello world"]],
    ids=["image-only", "one-of-three-pages-has-text"],
)
def test_scanned_source_is_converted_with_a_warning(
    workdir: Path,
    make_pdf: MakePdf,
    capsys: pytest.CaptureFixture[str],
    pages: list[str | None],
) -> None:
    source = make_pdf(workdir / "scan.pdf", pages)

    exit_code = main([str(source)])

    assert exit_code == 0
    target = workdir / "scan.md"
    assert target.exists()
    captured = capsys.readouterr()
    assert captured.out == f"{target}\n"
    assert captured.err.count("\n") == 1
    assert "scanned" in captured.err
    assert "OCR" in captured.err


@pytest.mark.parametrize(
    "pages",
    [["Hello world"], ["Hello world", None], ["One", "Two", "Three", None]],
    ids=["all-text", "half-the-pages-have-text", "one-scanned-page-of-four"],
)
def test_source_with_mostly_text_converts_without_warning(
    workdir: Path,
    make_pdf: MakePdf,
    capsys: pytest.CaptureFixture[str],
    pages: list[str | None],
) -> None:
    source = make_pdf(workdir / "doc.pdf", pages)

    exit_code = main([str(source)])

    assert exit_code == 0
    assert capsys.readouterr().err == ""


def test_markdown_keeps_headings_and_joins_pages_into_one_document(
    workdir: Path, make_pdf: MakePdf
) -> None:
    source = make_pdf(
        workdir / "doc.pdf",
        ["# Introduction\nFirst page body.", "Second page body."],
    )

    assert main([str(source)]) == 0

    markdown = (workdir / "doc.md").read_text(encoding="utf-8")
    heading_lines = [line for line in markdown.splitlines() if line.startswith("#")]
    assert any("Introduction" in line for line in heading_lines)
    assert markdown.index("First page body.") < markdown.index("Second page body.")


def test_images_are_dropped_so_only_one_markdown_file_is_written(
    workdir: Path, make_pdf: MakePdf
) -> None:
    source = make_pdf(workdir / "doc.pdf", ["Text page", None, "More text"])

    assert main([str(source)]) == 0

    assert sorted(p.name for p in workdir.iterdir()) == ["doc.md", "doc.pdf"]
    assert "![" not in (workdir / "doc.md").read_text(encoding="utf-8")


def test_non_ascii_text_survives_as_utf8(workdir: Path, make_pdf: MakePdf) -> None:
    source = make_pdf(workdir / "doc.pdf", ["Olá, ação e coração"])

    assert main([str(source)]) == 0

    assert "Olá, ação e coração" in (workdir / "doc.md").read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "argv", [[], ["a.pdf", "b.md", "c.md"], ["--force", "a.pdf"]], ids=["none", "extra", "unknown-flag"]
)
def test_wrong_usage_exits_2_with_usage_on_stderr(
    workdir: Path, capsys: pytest.CaptureFixture[str], argv: list[str]
) -> None:
    exit_code = main(argv)

    assert exit_code == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "usage: kwamd" in captured.err


def test_help_describes_usage(workdir: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--help"]) == 0
    assert "usage: kwamd" in capsys.readouterr().out


def test_version_prints_the_package_version(
    workdir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["--version"]) == 0
    assert capsys.readouterr().out == "kwamd 0.1.0\n"


def test_unwritable_target_folder_fails(
    workdir: Path, make_pdf: MakePdf, capsys: pytest.CaptureFixture[str]
) -> None:
    source = make_pdf(workdir / "report.pdf", ["Hello world"])
    locked = workdir / "locked"
    locked.mkdir()
    locked.chmod(0o500)
    try:
        exit_code = main([str(source), str(locked)])
    finally:
        locked.chmod(0o700)

    assert exit_code == 1
    _assert_failed_with_one_line(capsys, workdir, "Cannot write Target")
    assert not list(locked.iterdir())


def test_missing_folder_target_with_trailing_slash_fails(
    workdir: Path, make_pdf: MakePdf, capsys: pytest.CaptureFixture[str]
) -> None:
    source = make_pdf(workdir / "report.pdf", ["Hello world"])

    exit_code = main([str(source), "nope/"])

    assert exit_code == 1
    assert not (workdir / "nope").exists()
    _assert_failed_with_one_line(capsys, workdir, "folder does not exist", "nope")


def test_scanned_source_warning_is_not_shown_when_the_conversion_fails(
    workdir: Path, make_pdf: MakePdf, capsys: pytest.CaptureFixture[str]
) -> None:
    source = make_pdf(workdir / "scan.pdf", [None])

    exit_code = main([str(source), "missing/scan.md"])

    assert exit_code == 1
    err = capsys.readouterr().err
    assert "kwamd: warning:" not in err
    assert err.startswith("kwamd: error:")
    assert err.count("\n") == 1


def test_folder_given_as_source_fails(workdir: Path, capsys: pytest.CaptureFixture[str]) -> None:
    (workdir / "papers").mkdir()

    exit_code = main(["papers"])

    assert exit_code == 1
    _assert_failed_with_one_line(capsys, workdir, "is a folder", "papers")


def test_unreadable_source_fails(
    workdir: Path, make_pdf: MakePdf, capsys: pytest.CaptureFixture[str]
) -> None:
    source = make_pdf(workdir / "report.pdf", ["Hello world"])
    source.chmod(0o000)
    try:
        exit_code = main([str(source)])
    finally:
        source.chmod(0o600)

    assert exit_code == 1
    _assert_failed_with_one_line(capsys, workdir, "Cannot read Source", "report.pdf")


@pytest.mark.parametrize(
    ("argv", "expected"),
    [
        (["report.pdf"], "report.md"),
        (["report.pdf", "notes.md"], "notes.md"),
        (["report.pdf", "sub/notes.md"], "sub/notes.md"),
        (["report.pdf", "sub"], "sub/report.md"),
        (["report.pdf", "sub/../notes.md"], "notes.md"),
        (["./report.pdf", "./sub/"], "sub/report.md"),
    ],
)
def test_relative_paths_are_read_against_current_folder_and_target_is_printed_absolute(
    workdir: Path,
    make_pdf: MakePdf,
    capsys: pytest.CaptureFixture[str],
    argv: list[str],
    expected: str,
) -> None:
    make_pdf(workdir / "report.pdf", ["Hello world"])
    (workdir / "sub").mkdir()

    exit_code = main(argv)

    assert exit_code == 0
    target = workdir / expected
    assert "Hello world" in target.read_text(encoding="utf-8")
    assert capsys.readouterr().out == f"{target}\n"
