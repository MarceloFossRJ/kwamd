# Spec: Markdown to PDF (v2)

Status: ready-for-agent

## Problem Statement

kwamd turns a PDF into Markdown. I also write documents in Markdown that I need to send or print as a PDF. I want the same command to go the other way: `kwamd notes.md` should give me `notes.pdf`, with the same predictable rules for where the file lands and the same promise never to overwrite anything.

## Solution

`kwamd <source> [target]` now converts in either direction, decided by the kind of **Source** (see `GLOSSARY.md`):

- A **PDF Source** (recognised by content) converts to Markdown exactly as in v1 (`docs/specs/pdf-to-markdown-cli/spec.md`).
- A **Markdown Source** (a `.md` or `.markdown` file) converts to a PDF document.
- Anything else fails with a one-line message.

Every Target rule, the stream contract and the exit codes from v1 carry over unchanged, with `.pdf` in place of `.md` for a Markdown Source.

## User Stories

1. As a user, I want to run `kwamd notes.md`, so that I get `notes.pdf` in my current folder.
2. As a user, I want `kwamd notes.md some/folder/` and `kwamd notes.md out.pdf` to behave like their v1 counterparts, so that there is one set of Target rules to remember.
3. As a user, I want an existing PDF never to be overwritten: a colliding Target becomes `notes (1).pdf`, with the lowest free number.
4. As a user, I want `NOTES.MD` and `notes.markdown` to count as Markdown, so that capitalisation and the long extension don't matter.
5. As a user, I want a real PDF to convert to Markdown even when it is named `something.md`, so that content always wins for PDFs. Its default Target then gets a number, because the Source itself occupies `something.md`.
6. As a user, I want a clear error when the Source is neither a PDF nor Markdown (e.g. `notes.txt`, a renamed `.docx`), so that I am not handed a strange PDF.
7. As a user, I want a clear error when a Markdown Source is not valid UTF-8, or is empty or only whitespace, so that I am not given a blank or garbled PDF. A leading byte-order mark is fine.
8. As a user, I want headings, bold, italics, strikethrough, inline code, lists, block quotes, horizontal rules, code blocks and tables rendered, so that the PDF reflects the document's structure.
9. As a user, I want links to be clickable, both web links and links to headings in the same document. A link to a heading that doesn't exist shows as plain text.
10. As a user, I want raw HTML in the Markdown to appear as literal text, so that it can never quietly break the layout.
11. As a user, I want local images (relative paths read against the Markdown file's folder) embedded in the PDF.
12. As a user, I want a remote image (`http://` or `https://`) shown as its alt text with one warning, so that kwamd never makes a network call.
13. As a user, I want a missing or unreadable local image shown as its alt text with a warning, and the PDF still written (exit 0).
14. As a user, I want text in any script (accented Latin, Greek, Cyrillic, CJK, Arabic, emoji) to render, so that non-English documents work.
15. As a user, I want A4 pages with 2 cm margins and a centred page number at the bottom of each page.
16. As a user, I want the PDF's title to be the first top-level heading, or the Source's stem if there is none, so that viewers show a sensible name.
17. As a user, I want YAML front matter (when the very first line is `---`) left out of the PDF.
18. As a script author, I want the same stream contract as v1: one absolute Target path on stdout, warnings and errors on stderr, exit codes 0/1/2/130.
19. As a user, I want `kwamd --help` to describe both directions.
20. As a maintainer, I want the runtime dependencies to be PyMuPDF4LLM and markdown-it-py only (this revises v1 story 34), so that `uv tool install .` stays the whole install.

## Implementation Decisions

- **Source kind** (ADR 0001). Read the first kilobyte: a PDF signature means a PDF Source. For a file with a Markdown extension the signature must be its very first bytes, because Markdown text can mention `%PDF-`. Otherwise a `.md`/`.markdown` suffix (case-insensitive) means a Markdown Source. Otherwise: `Source is neither a PDF nor Markdown: <path>`, exit 1. Missing, folder and unreadable Sources keep their v1 messages, checked before the kind. Detecting the kind never prompts.
- **Order of checks.** 1) Source kind, 2) resolve and check the Target (default extension from the kind), 3) open the Source (unlock a PDF, possibly prompting; or read and decode Markdown), 4) convert and write. Every v1 guarantee about checking before asking still holds.
- **Rendering** (ADR 0002). markdown-it-py (CommonMark preset, plus the `table` and `strikethrough` rules, `html` disabled) produces HTML. PyMuPDF `Story` lays it out with `write_with_links`, so links stay clickable. No other runtime dependency.
- **Fixed look.**
  - Page and type: A4 with 2 cm margins; body text in MuPDF's default serif (Charis SIL) at 11 pt; headings bold, sized down from H1 to H6.
  - Code and blocks: code in Nimbus Mono on a light grey background; tables with thin borders; quotes with a grey left bar.
  - Colour: black on white, except links, which stay MuPDF's underlined blue so they read as clickable.
  - Fonts: MuPDF's built-in fallback fonts cover non-Latin scripts and emoji, so none are bundled.
  - Flags: no styling or page-size flags.
- **Images.**
  - Local image paths are resolved against the Source's folder and served to `Story` through a `pymupdf.Archive` of that folder.
  - Remote images are replaced by their alt text, with one warning per run: `kwamd: warning: remote images are not downloaded; showing alt text instead: <n> image(s)`.
  - Missing or unreadable local images are replaced by alt text, with one warning each naming the path.
  - Warnings never change the exit code.
- **Links to a missing heading** (`[x](#nowhere)`) render as plain text, silently. Story cannot lay out a link to an id that doesn't exist.
- **Page numbers.** A centred number at the bottom margin of every page, drawn after layout.
- **Metadata.** PDF title is the text of the first `#` heading, else the Source's stem. No author.
- **Front matter.** If the first line is exactly `---`, everything up to and including the next line that is exactly `---` is dropped before rendering. Without a closing `---`, nothing is dropped.
- **Modules.**
  - *Source checking* gains the kind check and the Markdown Source (read, decode UTF-8 with an optional BOM, reject empty).
  - *Target resolution* takes the default extension from the kind.
  - A new *rendering* module is the only one that knows markdown-it-py and `Story`: Markdown text in, PDF bytes out.
  - *Target writing* accepts bytes as well as text, with the same no-partial-file guarantee.
  - Library failures are translated to `KwamdError` at their module boundary (see `CODING_STANDARDS.md`).
- **Packaging.** Add `markdown-it-py` as a runtime dependency. Bump the version to 0.2.0. Update the package description and `--help` to "Convert a PDF to Markdown, or Markdown to a PDF."

## Testing Decisions

- The same one seam as v1: tests call `main(argv)` and assert on the exit code, stdout, stderr and the files on disk.
- Markdown fixtures are written in each test. The resulting PDF is read back with PyMuPDF to check extracted text, page count, links, embedded images, the title metadata and page-number text. Content assertions are tolerant: no byte-exact PDF comparisons.
- Remote images need no fake, because they are never fetched.

## Out of Scope

- Styling, theme or page-size flags.
- Downloading remote images.
- Rendering raw HTML.
- Syntax highlighting.
- Task lists, footnotes, maths.
- Reading the Source from stdin.

## Issues

- [01: Markdown Source to PDF, core rendering](issues/01-markdown-to-pdf-core.md)
- [02: Images in a Markdown Source](issues/02-images.md)
- [03: Page numbers, title and front matter](issues/03-page-numbers-title-front-matter.md)
- [04: README, description and version 0.2.0](issues/04-docs-and-version.md)
