# 04: README, description and version 0.2.0

Status: ready-for-agent
Blocked by: 01

## Problem

The docs and package metadata describe only PDF to Markdown. See `../spec.md` (story 19, Packaging).

## Acceptance criteria

- `pyproject.toml` has version `0.2.0`, and its description matches the `GLOSSARY.md` summary line.
- `kwamd --help` says "Convert a PDF to Markdown, or Markdown to a PDF.", and the help for each argument covers both directions.
- The README's opening line and Usage section show a Markdown example (`kwamd notes.md` writes `notes.pdf`) next to the PDF one.
- `kwamd --version` prints `kwamd 0.2.0`.
