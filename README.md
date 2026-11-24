# kwamd

A command-line tool that converts a PDF document into a Markdown file, or a Markdown file
into a PDF document. It uses [PyMuPDF4LLM](https://github.com/pymupdf/pymupdf4llm) for PDF to
Markdown, and [markdown-it-py](https://github.com/executablebooks/markdown-it-py) with
[PyMuPDF](https://github.com/pymupdf/PyMuPDF) for Markdown to PDF.

## Install

kwamd installs with [uv](https://docs.astral.sh/uv/). From a clone of this repository:

```sh
uv tool install .
```

This puts `kwamd` in uv's tool folder, `~/.local/bin` by default (`uv tool dir --bin` shows
it). uv fetches the required Python (3.14) itself. If your shell then says `command not found: kwamd`, run `uv tool update-shell` and open a new terminal.

After pulling new changes, reinstall with `uv tool install --reinstall .`. To remove it:
`uv tool uninstall kwamd`.

## Usage

```sh
kwamd <source> [target]
```

The Source decides the direction: a PDF (recognised by its content, whatever its name)
becomes Markdown, and a `.md` or `.markdown` file becomes a PDF. Any other file is refused.

- `kwamd report.pdf` writes `report.md` in the **current folder**.
- `kwamd notes.md` writes `notes.pdf` in the **current folder**.
- `kwamd report.pdf summary.md` writes `summary.md` (the path is used exactly as given).
- `kwamd notes.md some/folder/` writes `some/folder/notes.pdf`.

kwamd never overwrites a file: if the Target exists, it writes `report (1).md`,
`report (2).md`, … using the lowest free number. On success it prints the path
it wrote to stdout, as an absolute path; warnings and errors go to stderr.
Relative paths are read against the current folder.

Exit codes: `0` success, `1` Source or Target problem, `2` wrong usage, `130` interrupted (Ctrl-C).

### PDF to Markdown

For a password-protected PDF, kwamd asks for the password at the terminal
(hidden input, three attempts). Without a terminal it fails.

A Scanned Source (pages that are only images) is converted with a warning; OCR is
not supported yet. Images are not extracted.

### Markdown to PDF

The PDF is A4 with 2 cm margins, page numbers, and one fixed look. It renders CommonMark
plus tables and strikethrough; raw HTML is shown as text. The PDF's title is the first
`#` heading, or the file name without its extension. YAML front matter at the top of
the file is left out.

- **Images:** local images (PNG, JPEG, GIF, BMP, TIFF, SVG) are embedded, with paths read
  against the Markdown file's folder. Remote images are never downloaded, and an image
  that can't be used shows its alt text; each case prints a warning, and the PDF is
  still written.
- **Links:** web (`http`, `https`), `mailto:` and `#heading` links are clickable. Any
  other link, such as a relative path or `file:`, appears as plain text.

## Development

Every clone needs the git hooks installed once:

```sh
uv run pre-commit install
```

The hook blocks commits to `main` and runs the same checks as CI. To run them on demand:

```sh
uv run pre-commit run --all-files   # everything below, in one go
uv run ruff check
uv run ruff format --check
uv run mypy
uv run pytest
```

To have `kwamd` on your PATH always run your working tree, install it in editable mode:

```sh
uv tool install --editable .
```

## License

AGPL-3.0-or-later. See [LICENSE](LICENSE).
