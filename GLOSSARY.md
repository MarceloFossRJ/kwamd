# kwamd

A command-line tool that converts a PDF document into a Markdown file.

## Language

**Source**:
The PDF document a conversion reads from. Identified by its content, not its file extension.
_Avoid_: input, input file, pdf file

**Target**:
The Markdown file a conversion writes to. An existing file is never overwritten.
_Avoid_: output, destination, md file

**Scanned Source**:
A Source whose pages are images with no extractable text, so a conversion yields little or no Markdown.
_Avoid_: image PDF, OCR PDF
