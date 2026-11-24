# Markdown rendering: markdown-it-py with PyMuPDF Story

A Markdown Source is parsed to HTML with markdown-it-py and laid out as a PDF with PyMuPDF's `Story`. PyMuPDF is already installed through PyMuPDF4LLM, and markdown-it-py is pure Python, so `uv tool install .` stays the whole install. The cost is plain-looking output and only part of CSS.

## Considered Options

- **WeasyPrint.** Much better CSS and typography. Rejected because it needs Pango installed on the system (e.g. `brew install pango`), which breaks the one-command install.
- **Pandoc with LaTeX.** The best typesetting. Rejected because it needs external programs measured in gigabytes.

## Consequences

Raw HTML in Markdown is not rendered, because `Story` supports only part of HTML and unsupported markup could break the layout without warning. Non-Latin scripts rely on MuPDF's built-in fallback fonts.
