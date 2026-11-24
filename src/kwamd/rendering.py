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
from markdown_it.common.normalize_url import validateLink
from markdown_it.token import Token

from kwamd.errors import KwamdError, one_line
from kwamd.mupdf import quiet_mupdf

PAGE = pymupdf.paper_rect("a4")
MARGIN = 72 * 2 / 2.54  # 2 cm in points
CONTENT = pymupdf.Rect(MARGIN, MARGIN, PAGE.width - MARGIN, PAGE.height - MARGIN)

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
    """markdown-it, but letting ``file:`` and ``data:`` addresses through.

    markdown-it drops them before kwamd sees them, leaving the raw Markdown as
    text; let through, an image with one can show its alt text instead.
    """

    def validateLink(self, url: str) -> bool:
        return validateLink(url) or url.strip().lower().startswith(("file:", "data:"))


# Raw HTML is shown as text: Story supports only part of HTML (ADR 0002).
MARKDOWN = _Markdown("commonmark", {"html": False}).enable(["table", "strikethrough"])


@dataclass
class Rendering:
    """A rendered PDF, and the warnings to show the person about it."""

    pdf: bytes
    warnings: list[str]


REMOTE = re.compile(r"(https?:)?//", re.IGNORECASE)
SCHEME = re.compile(r"([a-z][a-z0-9+.-]+):", re.IGNORECASE)
"""An address scheme such as ``file:``; two letters at least, so ``C:`` isn't one."""


class _UnusableImage(Exception):
    """A local image that can't be embedded; the message says why."""


def render_pdf(markdown: str, source_path: Path) -> Rendering:
    """Render the Markdown Source text ``markdown`` as a PDF.

    Relative image paths are read against the Source's folder. An image that
    can't be embedded never fails the run: it shows its alt text, and the
    returned ``Rendering.warnings`` say why.
    """
    quiet_mupdf()
    try:
        html, images, warnings = _html(markdown, source_path.parent)
        return Rendering(_layout(html, images), warnings)
    except Exception as error:
        # Neither markdown-it-py nor Story documents its exception types, so
        # any failure is reported as the Source's.
        raise KwamdError(f"Cannot render Source {source_path}: {one_line(error)}") from None


def _html(markdown: str, folder: Path) -> tuple[str, dict[str, bytes], list[str]]:
    """The HTML for ``markdown``, the image files it refers to, and warnings."""
    tokens = MARKDOWN.parse(markdown)
    _resolve_anchor_links(tokens, _add_heading_ids(tokens))
    images, warnings = _collect_images(tokens, folder)
    html: str = MARKDOWN.renderer.render(tokens, MARKDOWN.options, {})
    return html, images, warnings


def _collect_images(tokens: list[Token], folder: Path) -> tuple[dict[str, bytes], list[str]]:
    """Read each local image and point its ``src`` at a name in the archive.

    Paths are read against ``folder``; ``../`` and absolute paths are allowed,
    which Story's own archive of the folder couldn't reach. An image that is
    remote (never downloaded), has an unsupported address, or can't be read
    is replaced by its alt text, with a warning. Returns the image content by
    name, and the warnings.
    """
    images: dict[str, bytes] = {}
    warnings: list[str] = []
    remote = 0
    for token in tokens:
        children = token.children or []
        for index, child in enumerate(children):
            src = child.attrGet("src")
            if child.type != "image" or not isinstance(src, str):
                continue
            problem = where = ""
            if REMOTE.match(src):
                remote += 1
            elif scheme := SCHEME.match(src):
                problem, where = "unsupported image address", f"{scheme.group(1)}:…"
            else:
                path = folder / unquote(src)
                try:
                    content = _read_image(path)
                except _UnusableImage as unusable:
                    problem, where = str(unusable), str(path)
                else:
                    name = f"image-{len(images)}{path.suffix}"
                    images[name] = content
                    child.attrSet("src", name)
                    continue
            # Shown as its alt text instead.
            children[index] = Token("text", "", 0, content=child.content)
            if problem:
                warnings.append(f"{problem}, showing alt text instead: {where}")
    if remote:
        warnings.append(
            f"remote images are not downloaded; showing alt text instead: {remote} image(s)"
        )
    return images, warnings


def _read_image(path: Path) -> bytes:
    """The content of the image at ``path``, or ``_UnusableImage`` saying why not."""
    if not path.exists():
        raise _UnusableImage("image not found")
    if path.is_dir():
        raise _UnusableImage("not an image")
    try:
        content = path.read_bytes()
    except OSError as error:
        raise _UnusableImage(f"cannot read image ({error.strerror or error})") from None
    pymupdf.TOOLS.mupdf_warnings(reset=True)
    try:
        if path.suffix.lower() == ".svg":
            pymupdf.open(stream=content, filetype="svg").close()
        else:
            pymupdf.Pixmap(content)
    except Exception:
        # PyMuPDF documents no exception type for an unknown image format.
        raise _UnusableImage("not an image") from None
    # MuPDF decodes a cut-off image with only a warning, padding the rest.
    if pymupdf.TOOLS.mupdf_warnings(reset=True):
        raise _UnusableImage("damaged image")
    return content


def _inline_children(tokens: list[Token]) -> list[Token]:
    return [child for token in tokens for child in token.children or []]


def _layout(html: str, images: dict[str, bytes]) -> bytes:
    archive = pymupdf.Archive()
    for name, content in images.items():
        archive.add((content, name))
    story = pymupdf.Story(html, user_css=STYLE, archive=archive)
    document = story.write_with_links(lambda _n, _filled: (PAGE, CONTENT, None))
    try:
        pdf: bytes = document.tobytes()
        return pdf
    finally:
        document.close()


def _add_heading_ids(tokens: list[Token]) -> set[str]:
    """Give each heading the id GitHub would, so ``[x](#some-heading)`` links work.

    A repeated slug gets the lowest free ``-<n>``, skipping ids an earlier
    heading already took (a heading named "Plan-1" takes ``plan-1``).
    Returns the ids given.
    """
    ids: set[str] = set()
    for opening, inline in pairwise(tokens):
        if opening.type != "heading_open":
            continue
        slug = heading_id = _slug(inline.content)
        n = 0
        while heading_id in ids:
            n += 1
            heading_id = f"{slug}-{n}"
        opening.attrSet("id", heading_id)
        ids.add(heading_id)
    return ids


def _resolve_anchor_links(tokens: list[Token], ids: set[str]) -> None:
    """Point each ``#…`` link at its heading id, matched the way GitHub does.

    markdown-it percent-encodes link targets (``#café`` arrives as
    ``#caf%C3%A9``) and GitHub ignores case, so both are undone before
    matching. A link to a heading that doesn't exist becomes plain text,
    because Story raises on a link whose target id is missing.
    """
    for child in _inline_children(tokens):
        href = child.attrGet("href")
        if child.type != "link_open" or not isinstance(href, str) or not href.startswith("#"):
            continue
        wanted = unquote(href[1:]).lower()
        if wanted in ids:
            child.attrSet("href", f"#{wanted}")
        else:
            del child.attrs["href"]


def _slug(heading: str) -> str:
    """GitHub's heading anchor: lowercase, punctuation dropped, spaces as hyphens."""
    return re.sub(r"[^\w\- ]", "", heading.strip().lower()).replace(" ", "-")
