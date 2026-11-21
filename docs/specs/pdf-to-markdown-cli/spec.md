# Spec: PDF to Markdown CLI (v1)

Status: ready-for-agent

## Problem Statement

I have PDF documents whose content I want as Markdown: to keep in notes, put under version control, or feed to an LLM. Copy-pasting out of a PDF viewer loses headings, lists and tables, and produces broken line wraps. I want a single shell command that turns a PDF into a reasonably structured Markdown file, without having to think about where it lands or worry that it will clobber a file I already have.

## Solution

A command-line tool, `kwamd`, invoked as `kwamd <source> [target]`.

- It reads the **Source** (a PDF) and writes a **Target** (a Markdown file) containing the Source's text, with headings, emphasis, lists, code blocks and tables preserved as well as PyMuPDF4LLM can infer them.
- When the Target is omitted, it is written to the current folder, named after the Source's stem with a `.md` extension.
- kwamd never overwrites an existing file. If the intended Target exists, it writes `<stem> (n)<ext>` using the lowest free `n`, the way browsers name repeated downloads.
- On success it prints exactly one line to stdout: the path of the Target it actually wrote.
- It warns (but still succeeds) when the Source looks like a **Scanned Source**, and fails with a clear one-line message when the Source is missing, not a PDF, encrypted, or has no pages.

## User Stories

1. As a user, I want to run `kwamd report.pdf`, so that I get `report.md` in my current folder without typing a second path.
2. As a user, I want the default Target to land in my current folder rather than next to the Source, so that I can pull PDFs from anywhere (e.g. Downloads) into the folder I am working in.
3. As a user, I want to run `kwamd report.pdf notes.md`, so that I can choose the Target's name.
4. As a user, I want to run `kwamd report.pdf some/folder/`, so that `report.md` is written inside that existing folder.
5. As a user, I want an explicit Target path to be used exactly as I typed it, including a non-`.md` extension or no extension, so that kwamd never second-guesses me.
6. As a user, I want kwamd to fail with a clear message when the Target's parent folder does not exist, so that typos in a path don't silently create stray folder trees.
7. As a user, I want kwamd to never overwrite an existing file, so that I never lose a hand-edited Markdown file by re-running a conversion.
8. As a user, I want a colliding Target to be named `report (1).md`, then `report (2).md`, and so on, so that repeated conversions behave like repeated browser downloads.
9. As a user, I want numbering to pick the lowest free number, so that if `report (1).md` was deleted, the next conversion reuses `(1)`.
10. As a user, I want the same numbering rule to apply to explicit Targets and folder Targets as to the default Target, so that there is one rule to remember.
11. As a user, I want a colliding extension-less Target such as `notes` to become `notes (1)`, so that numbering works for any name.
12. As a user, I want kwamd to print the final Target path on stdout, always as an absolute path, so that I know where the file went even when it was renumbered. Relative Source and Target paths are read against the current folder.
13. As a script author, I want stdout to contain only the Target path, so that I can capture it with `$(kwamd file.pdf)` and use it in the next command.
14. As a script author, I want warnings and errors on stderr, so that they don't pollute captured stdout.
15. As a script author, I want exit code `0` on success, so that I can chain kwamd with `&&`.
16. As a script author, I want exit code `1` when the Source or Target is the problem, so that I can tell a bad file from bad usage.
17. As a script author, I want exit code `2` on wrong usage (missing or extra arguments, unknown flags), so that usage mistakes are distinguishable.
18. As a user, I want a clear error when the Source does not exist, so that I can fix the path.
19. As a user, I want a clear error when the Source is not actually a PDF (e.g. a renamed `.docx`), so that I am not handed garbage Markdown.
20. As a user, I want a real PDF without a `.pdf` extension to be accepted, so that oddly named downloads still convert; its default Target is `<name>.md`.
21. As a user who has the password of a password-protected Source, I want kwamd to ask me for it with hidden input (up to three attempts, like `sudo`), so that I can convert it without the password landing in shell history; without a terminal to ask, I want a clear error instead. A Source with only an owner password (it opens without one) converts without asking.
22. As a user, I want a clear error when the Source has zero pages, so that I am not given an empty Target.
23. As a user, I want a warning when the Source looks like a Scanned Source (fewer than half its pages have extractable text), so that I understand why the Markdown is nearly empty.
24. As a user, I want the Target still to be written for a Scanned Source, so that I keep whatever text was extracted.
25. As a user, I want a mostly-text PDF with a few scanned pages to convert without a warning, so that I am not nagged about normal documents.
26. As a user, I want the Markdown to preserve headings, so that the document's structure survives.
27. As a user, I want bold, italics, lists, code blocks and tables preserved where detectable, so that the Markdown is usable without cleanup.
28. As a user, I want the whole document as one continuous Markdown document with no page separators, so that it reads naturally.
29. As a user, I want images in the PDF to be dropped, so that the result is always exactly one Markdown file.
30. As a user, I want the Target written as UTF-8, so that non-ASCII text survives.
31. As a user, I want `kwamd --help`, so that I can see the usage.
32. As a user, I want `kwamd --version`, so that I can report which version I am running.
33. As a maintainer, I want the PDF-to-Markdown conversion isolated behind kwamd's own small conversion module, so that PyMuPDF4LLM can be swapped or augmented (e.g. OCR) without touching the CLI.
34. As a maintainer, I want PyMuPDF4LLM to be the only runtime dependency, so that installation stays light.
35. As a packager, I want the package metadata to declare `AGPL-3.0-or-later` and include the LICENSE file, so that the license shows up on package indexes.

## Implementation Decisions

- **Entry point.** The package entry function becomes `main(argv: list[str] | None = None) -> int`. `argv=None` means "read the real command line". It returns the exit code; the `kwamd` console script exits with that code. Behaviour does not change for the shell user.
- **Argument parsing.** Standard-library `argparse`. Two positionals (`source`, optional `target`), plus `--help` and `--version`. No other flags in v1 (notably no overwrite/force flag).
- **Modules.**
  - *CLI*: parses arguments, orchestrates, maps outcomes to stdout/stderr and exit codes. The only module that prints or knows about exit codes.
  - *Source checking*: opens the Source and classifies it: missing, not a PDF, encrypted, zero pages, Scanned Source, or OK. Classification is by content, never by extension.
  - *Target resolution*: given the Source and the optional target argument (and the current folder), produces the final Target path, including folder handling and browser-style numbering.
  - *Conversion*: a small interface along the lines of "Source path in, Markdown text out", implemented with PyMuPDF4LLM. Images are not extracted; no page separators.
- **Target resolution rules.**
  - No target argument → `<source stem>.md` in the current working folder.
  - Target argument is an existing folder → `<source stem>.md` inside it.
  - Any other target argument → used exactly as given; no extension is added or changed.
  - Parent folder of the Target missing → error (exit 1); folders are never created.
  - If the resolved path exists → `<stem> (<n>)<ext>` with a single space before the parenthesis, `n` starting at 1, choosing the lowest `n` that does not exist. Applies to every kind of Target.
- **Scanned Source rule.** A Source is a Scanned Source when fewer than half of its pages have any extractable text (judged with PyMuPDF's page text before conversion). It is converted and written anyway, with a one-line warning on stderr; exit 0.
- **Source failures.** Missing file, a folder, unreadable, not a PDF, zero pages: each yields a distinct one-line stderr message and exit 1. Nothing is written.
- **Password-protected Source** (one that cannot be opened without a password). If stdin is a terminal, kwamd prompts `Password for <name>: ` with hidden input. On a wrong password it prints `kwamd: wrong password, try again` to stderr and asks again, up to three attempts in total. After the third wrong password it fails with exit 1. With no terminal it fails at once with exit 1. There is no password flag or environment variable. A Source encrypted with only an owner password opens without one and converts without asking.
- **Target write failure** (e.g. permission denied) → one-line stderr message, exit 1.
- **Paths.** Relative Source and Target arguments are read against the current folder. The Target path is normalised (`sub/../notes.md` → `notes.md`) and printed as an absolute path.
- **Output contract.** Success: stdout is exactly one line, the final Target path (absolute). Warnings and errors only on stderr. Exit codes: 0 success (including the Scanned Source warning), 1 Source/Target failure, 2 usage error.
- **Encoding.** Target written as UTF-8.
- **Packaging.** Add `pymupdf4llm` as the sole runtime dependency. Declare `license = "AGPL-3.0-or-later"` and `license-files = ["LICENSE"]` in the project metadata. Fill in the project description.

## Testing Decisions

- **One seam: the CLI entry function.** Every test calls `main(argv)` in-process, with the working folder set to a temporary directory, and asserts only on externally visible behaviour: the returned exit code, captured stdout and stderr, and the files present on disk (names and Markdown content). Internal modules (source checking, target resolution, conversion) are not tested directly, so they can be refactored freely.
- **No mocking of PyMuPDF4LLM.** Tests run the real conversion so that they exercise what users get.
- **Fixture PDFs are generated in the tests with PyMuPDF**: a text PDF with headings, a multi-page PDF, an image-only PDF (Scanned Source), a mostly-text PDF with one image-only page (no warning), password-protected and owner-password-only PDFs, a zero-page PDF where PyMuPDF allows one, and a non-PDF file with a `.pdf` extension. Commit a real-world PDF only if a future bug requires one.
- **Content assertions are tolerant**: assert that key text and heading markers appear, not byte-exact Markdown, so that PyMuPDF4LLM upgrades don't break tests needlessly.
- **What a good test looks like**: named after a user-visible behaviour (e.g. "colliding target gets lowest free number"), sets up files, runs `main` with the words a user would type, and checks exit code, streams and files.
- **The terminal is the one faked boundary**: password tests replace `sys.stdin.isatty` and `getpass.getpass` to stand in for the person typing. They still go through `main(argv)`.
- **Prior art**: none yet; the codebase is a skeleton. These tests establish the pattern. Use pytest (`tmp_path`, `monkeypatch.chdir`, `capsys`).

## Out of Scope

- OCR for Scanned Sources.
- Extracting or embedding images.
- Multiple Sources per run, globbing, or directory recursion.
- Reading the Source from stdin or writing the Markdown to stdout.
- Page ranges or page separators.
- Configuration files.
- Overwriting an existing Target (no `--force`).
- Supplying a password non-interactively (no `--password` flag, no environment variable).
- Creating missing parent folders for the Target.

## Further Notes

- Vocabulary follows `GLOSSARY.md`: **Source**, **Target**, **Scanned Source**. Avoid "input/output" in code, messages and tests.
- No ADRs were recorded. The project's AGPL-3.0 license was chosen independently of the PyMuPDF dependency, though the two are compatible.
- Python is pinned to 3.14. Confirm that PyMuPDF wheels install cleanly on it when adding the dependency.
