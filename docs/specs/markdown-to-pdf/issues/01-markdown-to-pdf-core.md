# 01: Markdown Source to PDF, core rendering

Status: ready-for-agent

## Problem

kwamd only converts a PDF Source to Markdown. A Markdown Source should convert to a PDF document with the same Target rules. See `../spec.md` (stories 1–10, 14, 18, 20) and ADRs 0001 and 0002.

## Acceptance criteria

- `kwamd notes.md` writes `notes.pdf` in the current folder and prints its absolute path. Folder Targets, explicit Targets and `(n)` numbering behave as in v1.
- `NOTES.MD` and `notes.markdown` are Markdown Sources. A real PDF named `x.md` converts to Markdown, as `x (1).md`.
- `notes.txt` and a renamed `.docx` fail with `kwamd: error: Source is neither a PDF nor Markdown: <path>` (exit 1).
- A Markdown Source that isn't valid UTF-8 fails with "Source is not UTF-8 text" (exit 1). One that is empty or only whitespace fails with "Source is empty" (exit 1). A leading BOM is accepted. No Target is left behind.
- The Source kind is checked before the Target is resolved, and the Target is resolved before a Source is opened.
- The PDF is A4 with 2 cm margins, in the fixed look from the spec.
- Headings, bold, italics, strikethrough, inline code, lists, quotes, rules, code blocks and tables render: their text can be extracted from the PDF.
- Web links and links to headings in the same document are clickable.
- Raw HTML shows as literal text.
- Greek, Cyrillic, CJK and Arabic text can be extracted from the PDF.
- A rendering failure gives one `kwamd: error:` line, exit 1, and no partial Target.
- The runtime dependencies are `pymupdf4llm` and `markdown-it-py` only. All v1 tests still pass.
