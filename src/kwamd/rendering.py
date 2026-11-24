"""Rendering of Markdown text into a PDF document.

This is the only module that knows about markdown-it-py and PyMuPDF's Story
(see docs/adr/0002-markdown-rendering-engine.md).
"""

import re
from dataclasses import dataclass
from itertools import pairwise
from pathlib import Path
from urllib.parse import unquote

import pymupdf
from markdown_it import MarkdownIt
from markdown_it.token import Token

from kwamd.errors import KwamdError, one_line
from kwamd.mupdf import quiet_mupdf

PAGE = pymupdf.paper_rect("a4")
MARGIN = 72 * 2 / 2.54  # 2 cm in points
CONTENT = pymupdf.Rect(MARGIN, MARGIN, PAGE.width - MARGIN, PAGE.height - MARGIN)
PAGE_NUMBER_FONT = "tiro"  # MuPDF's built-in Times, to sit with the serif body
PAGE_NUMBER_SIZE = 9
PAGE_NUMBER_BASELINE = PAGE.height - MARGIN / 2 + PAGE_NUMBER_SIZE / 3
"""Puts the number's middle in the middle of the bottom margin: a digit's
middle sits about a third of the font size above its baseline."""

# The one fixed look (see docs/specs/markdown-to-pdf/spec.md). MuPDF's default
# serif is Charis SIL and its monospace is Nimbus Mono; its fallback fonts cover
# other scripts and emoji.
STYLE = """
body { margin: 0; font-size: 11pt; color: black; background-color: white; }
h1 { font-size: 22pt; } h2 { font-size: 18pt; } h3 { font-size: 15pt; }
h4 { font-size: 13pt; } h5 { font-size: 12pt; } h6 { font-size: 11pt; }
h1, h2, h3, h4, h5, h6 { font-weight: bold; }
code, pre { font-family: monospace; background-color: #eeeeee; }
pre { padding: 6pt; }
table { border-collapse: collapse; }
th, td { border: 0.5pt solid #888888; padding: 3pt 6pt; }
blockquote { border-left: 3pt solid #bbbbbb; padding-left: 8pt; margin-left: 0; }
"""


class _Markdown(MarkdownIt):
    """markdown-it, letting every link and image address through.

    markdown-it would leave a ``file:``, ``data:`` or ``javascript:`` address
    as raw Markdown text. kwamd vets every address itself instead: see
    ``_vet_links`` and ``_collect_images``.
    """

    def validateLink(self, url: str) -> bool:
        return True


# Raw HTML is shown as text: Story supports only part of HTML (ADR 0002).
MARKDOWN = _Markdown("commonmark", {"html": False}).enable(["table", "strikethrough"])


@dataclass
class Rendering:
    """A rendered PDF, and the warnings to show the person about it."""

    pdf: bytes
    warnings: list[str]


_REMOTE_ADDRESS = re.compile(r"(https?:)?//", re.IGNORECASE)
_LINK_ADDRESS = re.compile(r"(https?:|mailto:)", re.IGNORECASE)
"""Links that stay clickable, besides ``#heading`` links. Anything else, such
as ``file:`` (which would make the PDF open a file) or ``javascript:``,
renders as plain text."""
_ADDRESS_SCHEME = re.compile(r"([a-z][a-z0-9+.-]+):", re.IGNORECASE)
"""An address scheme such as ``file:``; two letters at least, so ``C:`` isn't one."""


@dataclass
class _Parsed:
    """A Markdown Source turned into what Story and the PDF need."""

    html: str
    images: dict[str, bytes]
    """Image content by the name its ``src`` now uses."""
    warnings: list[str]
    title: str | None
    """The first top-level heading as plain text, if there is one."""


class _UnusableImage(Exception):
    """A local image that can't be embedded."""

    def __init__(self, reason: str, where: str) -> None:
        super().__init__(f"{reason}, showing alt text instead: {where}")


def render_pdf(markdown: str, source_path: Path) -> Rendering:
    """Render the Markdown Source text ``markdown`` as a PDF.

    Relative image paths are read against the Source's folder. An image that
    can't be embedded never fails the run: it shows its alt text, and the
    returned ``Rendering.warnings`` say why.
    """
    quiet_mupdf()
    try:
        parsed = _parse(markdown, source_path.parent)
        pdf = _layout(parsed.html, parsed.images, parsed.title or source_path.stem)
        return Rendering(pdf, parsed.warnings)
    except Exception as error:
        # Neither markdown-it-py nor Story documents its exception types, so
        # any failure is reported as the Source's.
        raise KwamdError(f"Cannot render Source {source_path}: {one_line(error)}") from None


def _parse(markdown: str, folder: Path) -> _Parsed:
    tokens = MARKDOWN.parse(markdown)
    headings = _headings(tokens)
    _vet_links(tokens, _add_heading_ids(headings))
    images, warnings = _collect_images(tokens, folder)
    html: str = MARKDOWN.renderer.render(tokens, MARKDOWN.options, {})
    return _Parsed(html, images, warnings, _title(headings))


def _headings(tokens: list[Token]) -> list[tuple[Token, Token]]:
    """Each heading's opening token and the inline token holding its text."""
    return [
        (opening, inline) for opening, inline in pairwise(tokens) if opening.type == "heading_open"
    ]


def _title(headings: list[tuple[Token, Token]]) -> str | None:
    """The first top-level ``#`` heading as plain text, ignoring headings in a
    quote or list."""
    for opening, inline in headings:
        if opening.tag == "h1" and opening.level == 0:
            return _plain_text(inline) or None
    return None


def _plain_text(inline: Token) -> str:
    """An inline token's text without its formatting: an image counts as its
    alt text, and line breaks and runs of spaces (no-break ones too) as one
    space."""
    parts = []
    for child in inline.children or []:
        if child.type in ("text", "code_inline", "image"):
            parts.append(child.content)
        elif child.type in ("softbreak", "hardbreak"):
            parts.append(" ")
    return " ".join("".join(parts).split())


def _collect_images(tokens: list[Token], folder: Path) -> tuple[dict[str, bytes], list[str]]:
    """Read each local image and point its ``src`` at a name in the archive.

    Paths are read against ``folder``; ``../`` and absolute paths are allowed,
    which Story's own archive of the folder couldn't reach. An image that is
    remote (never downloaded) or unusable is replaced by its alt text, with a
    warning. Returns the image content by name, and the warnings.
    """
    images: dict[str, bytes] = {}
    warnings: list[str] = []
    remote = 0
    for children, index, image in _images_in(tokens):
        src = str(image.attrGet("src"))
        try:
            if _REMOTE_ADDRESS.match(src):
                remote += 1
            else:
                content = _local_image(src, folder)
                name = f"image-{len(images)}{Path(src).suffix}"
                images[name] = content
                image.attrSet("src", name)
                continue
        except _UnusableImage as unusable:
            warnings.append(one_line(unusable))
        children[index] = Token("text", "", 0, content=image.content)  # its alt text
    if remote:
        warnings.append(
            f"remote images are not downloaded; showing alt text instead: {remote} image(s)"
        )
    return images, warnings


def _images_in(tokens: list[Token]) -> list[tuple[list[Token], int, Token]]:
    """Each image token, with the list holding it and its index there, so it
    can be replaced."""
    return [
        (children, index, child)
        for token in tokens
        for children in [token.children or []]
        for index, child in enumerate(children)
        if child.type == "image"
    ]


def _local_image(src: str, folder: Path) -> bytes:
    """The content of the image at ``src``, read against ``folder``, or
    ``_UnusableImage`` saying why it can't be embedded."""
    if scheme := _ADDRESS_SCHEME.match(src):
        raise _UnusableImage("unsupported image address", f"{scheme.group(1)}:…")
    path = folder / unquote(src)
    if not path.exists():
        raise _UnusableImage("image not found", str(path))
    try:
        content = path.read_bytes()
    except IsADirectoryError:
        raise _UnusableImage("not a usable image", str(path)) from None
    except OSError as error:
        reason = f"cannot read image ({error.strerror or error})"
        raise _UnusableImage(reason, str(path)) from None
    if not _decodes_cleanly(content, path.suffix.lower() == ".svg"):
        raise _UnusableImage("not a usable image", str(path))
    return content


def _decodes_cleanly(content: bytes, svg: bool) -> bool:
    """Whether MuPDF decodes ``content`` as an image without complaint.

    MuPDF decodes some cut-off images with only a warning, padding the rest,
    so its warning log is cleared first and checked after. Nothing else
    decodes in between, because kwamd does one thing at a time.
    """
    pymupdf.TOOLS.mupdf_warnings(reset=True)
    try:
        if svg:
            pymupdf.open(stream=content, filetype="svg").close()
        else:
            pymupdf.Pixmap(content)
    except Exception:
        # PyMuPDF documents no exception type for an unknown or broken image.
        return False
    return not pymupdf.TOOLS.mupdf_warnings(reset=True)


def _inline_children(tokens: list[Token]) -> list[Token]:
    return [child for token in tokens for child in token.children or []]


def _layout(html: str, images: dict[str, bytes], title: str) -> bytes:
    archive = pymupdf.Archive()
    for name, content in images.items():
        archive.add((content, name))
    story = pymupdf.Story(html, user_css=STYLE, archive=archive)
    document = story.write_with_links(lambda _n, _filled: (PAGE, CONTENT, None))
    try:
        _number_pages(document)
        document.set_metadata({"title": title})
        pdf: bytes = document.tobytes()
        return pdf
    finally:
        document.close()


def _number_pages(document: pymupdf.Document) -> None:
    """Draw each page's number, centred in the middle of the bottom margin."""
    for index in range(document.page_count):
        page = document.load_page(index)
        number = str(index + 1)
        width = pymupdf.get_text_length(
            number, fontname=PAGE_NUMBER_FONT, fontsize=PAGE_NUMBER_SIZE
        )
        page.insert_text(
            ((PAGE.width - width) / 2, PAGE_NUMBER_BASELINE),
            number,
            fontname=PAGE_NUMBER_FONT,
            fontsize=PAGE_NUMBER_SIZE,
        )


def _add_heading_ids(headings: list[tuple[Token, Token]]) -> set[str]:
    """Give each heading the id GitHub would, so ``[x](#some-heading)`` links work.

    A repeated slug gets the lowest free ``-<n>``, skipping ids an earlier
    heading already took (a heading named "Plan-1" takes ``plan-1``).
    Returns the ids given.
    """
    ids: set[str] = set()
    for opening, inline in headings:
        slug = heading_id = _slug(inline.content)
        n = 0
        while heading_id in ids:
            n += 1
            heading_id = f"{slug}-{n}"
        opening.attrSet("id", heading_id)
        ids.add(heading_id)
    return ids


def _vet_links(tokens: list[Token], ids: set[str]) -> None:
    """Keep a link clickable only when it goes to a web or mail address, or to
    a heading; any other link renders as plain text.

    A ``#…`` link matches its heading the way GitHub does: markdown-it
    percent-encodes it (``#café`` arrives as ``#caf%C3%A9``) and GitHub
    ignores case, so both are undone first. A link to a heading that doesn't
    exist becomes plain text too, because Story raises on a link whose target
    id is missing.
    """
    for child in _inline_children(tokens):
        href = child.attrGet("href")
        if child.type != "link_open" or not isinstance(href, str):
            continue
        if href.startswith("#") and (wanted := unquote(href[1:]).lower()) in ids:
            child.attrSet("href", f"#{wanted}")
        elif href.startswith("#") or not _LINK_ADDRESS.match(href):
            del child.attrs["href"]


def _slug(heading: str) -> str:
    """GitHub's heading anchor: lowercase, punctuation dropped, spaces as hyphens."""
    return re.sub(r"[^\w\- ]", "", heading.strip().lower()).replace(" ", "-")
