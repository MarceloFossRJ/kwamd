# kwamd

A command-line tool that converts a PDF document into a Markdown file, or a Markdown file into a PDF document.

## Language

**Source**:
The file a conversion reads from: a PDF Source or a Markdown Source.
_Avoid_: input, input file

**PDF Source**:
A Source that is a PDF document, identified by its content, not its file extension. Converts to Markdown.
_Avoid_: pdf file

**Markdown Source**:
A Source that is a Markdown file, identified by its `.md` or `.markdown` extension. Converts to a PDF document.
_Avoid_: md file, text file

**Target**:
The file a conversion writes to, in the other format from its Source. An existing file is never overwritten.
_Avoid_: output, destination

**Scanned Source**:
A PDF Source whose pages are images with no extractable text, so a conversion yields little or no Markdown.
_Avoid_: image PDF, OCR PDF
