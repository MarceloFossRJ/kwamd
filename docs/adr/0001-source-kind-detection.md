# Source kind: PDF by content, Markdown by extension

kwamd converts in whichever direction the Source implies. A PDF has a signature, so a PDF Source is recognised by its content wherever the file is named, as in v1. Markdown has no signature, so a Markdown Source is recognised by its `.md` or `.markdown` extension (case-insensitive), and any other file is rejected.

## Considered Options

- **Treat any non-PDF UTF-8 text as Markdown.** Rejected: `notes.txt`, `README` or a config file would silently become a PDF, where a clear error is more useful.
- **A `--to pdf` flag.** Rejected: the Source already says which way to go, and the flag would be one more thing to type every time.

## Consequences

Content wins for PDFs: a real PDF named `report.md` converts to Markdown. Its default Target collides with the Source itself, so it is written as `report (1).md`.
