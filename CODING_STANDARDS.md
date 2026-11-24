# Coding standards

Judgement-call rules for review. Mechanical rules live in tooling instead (ruff, mypy, the pre-commit hooks and CI), so they are not repeated here.

## Failure contract

kwamd talks to scripts as well as people, so every way a run can end is part of its interface (see the spec's stream contract).

- **One line per failure.** Every failure path ends in exactly one `kwamd: error: …` line on stderr and a defined exit code (1 Source/Target, 2 usage, 130 interrupted). A Python traceback reaching the user is a defect. Text from a library error is flattened to one line before it is shown.
- **Library calls behind the boundary.** Every call into PyMuPDF, PyMuPDF4LLM or markdown-it-py sits in the module that owns it (`source.py`, `conversion.py`, `rendering.py`). That module translates the library's failures into `KwamdError`, because the libraries document no stable exception types.
- **Created files are cleaned up on any exception.** When kwamd creates a file and a later step fails, including `KeyboardInterrupt`, the file is removed: clean up on `BaseException`, not just `OSError`. The rule a Target must keep: nothing partial is left behind.
- **Existence checks count every directory entry.** Checks that decide whether a path is free use `os.path.lexists`, so a dangling symlink counts as taken. `Path.exists()` follows links and reports a dangling one as free.
- **Check before asking.** Validate everything that can be checked without the person (the Target path, the arguments) before prompting them, for example for a password.

## Tests

- **Behaviour through `main(argv)`.** Tests use the one agreed seam: they call `main` and check the exit code, stdout, stderr and the files on disk. Fakes stand only at the system boundary (the terminal) and for the library-failure paths the spec lists.
- **Check the kwamd line, not all of stderr.** Split stderr with `stderr_lines(err, tmp_path)` from `tests/conftest.py`, which shows the temp folder as `<tmp>`, and check the line you expect by its `kwamd: error:` or `kwamd: warning:` start. Paths in messages include pytest's temp folder, which is named after the test, so searching all of stderr for a bare word matches the test's own name.
- **Use glossary words in names.** Test names, ids and fixtures use Source, Target and Scanned Source (`GLOSSARY.md`).
- **Read a PDF Target through the `tests/conftest.py` helpers.** Check its text with `pdf_text`, which NFKC-normalises it: raw `get_text()` returns ligatures such as "ﬁ" for "fi", so a check for "first" fails on a correct PDF. Use `page_of`, `link_pages` and `image_count` for pages, links and images; Story makes one link area per word, so compare where links go, not how many there are.
- **A test written after its fix must be seen failing.** Undo the fix, run the test and watch it fail, then restore the fix. A test that passes either way, for example because it searches text that always contains the words, proves nothing.
