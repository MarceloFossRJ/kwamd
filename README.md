# kwamd

A command-line tool that converts a PDF document into a Markdown file, using
[PyMuPDF4LLM](https://github.com/pymupdf/pymupdf4llm).

## Usage

```sh
kwamd <source> [target]
```

- `kwamd report.pdf` writes `report.md` in the **current folder**.
- `kwamd report.pdf notes.md` writes `notes.md` (the path is used exactly as given).
- `kwamd report.pdf some/folder/` writes `some/folder/report.md`.

kwamd never overwrites a file: if the Target exists, it writes `report (1).md`,
`report (2).md`, … using the lowest free number. On success it prints the path
it wrote to stdout, as an absolute path; warnings and errors go to stderr.
Relative paths are read against the current folder.

For a password-protected PDF, kwamd asks for the password at the terminal
(hidden input, three attempts). Without a terminal it fails.

Exit codes: `0` success, `1` Source or Target problem, `2` wrong usage, `130` interrupted (Ctrl-C).

A Scanned Source (pages that are only images) is converted with a warning; OCR is
not supported yet. Images are not extracted.

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

## License

AGPL-3.0-or-later. See [LICENSE](LICENSE).
