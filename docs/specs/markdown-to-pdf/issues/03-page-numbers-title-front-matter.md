# 03: Page numbers, title and front matter

Status: ready-for-agent
Blocked by: 01

## Problem

The PDF needs page numbers and a title, and front matter in the Markdown must not appear in it. See `../spec.md` (stories 15–17).

## Acceptance criteria

- Every page has its number centred in the bottom margin, and the number can be extracted from the PDF.
- The PDF's title metadata is the first non-empty top-level h1 (`#` or setext `===`) as plain text (formatting dropped, an image as its alt text, line breaks and repeated spaces as one space; headings in a quote or list don't count), or the Source's stem when there is no such heading.
- When the first line is exactly `---`, everything up to and including the next line that is exactly `---` is left out of the PDF. With no closing `---`, the whole Source renders. A Source that is only front matter fails with "Source is empty" (exit 1).
