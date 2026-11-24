"""Rendering of Markdown text into a PDF document.

This is the only module that knows about markdown-it-py and PyMuPDF's Story
(see docs/adr/0002-markdown-rendering-engine.md).
"""

import re
from collections import Counter
from itertools import pairwise
from pathlib import Path

import pymupdf
from markdown_it import MarkdownIt
from markdown_it.token import Token

from kwamd.errors import KwamdError, one_line

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

# Raw HTML is shown as text: Story supports only part of HTML (ADR 0002).
MARKDOWN = MarkdownIt("commonmark", {"html": False}).enable(["table", "strikethrough"])


def render_pdf(markdown: str, source_path: Path) -> bytes:
    """Return a PDF of the Markdown Source text ``markdown``.

    Relative resources, such as images, are read from the Source's folder.
    """
    # MuPDF otherwise prints its own diagnostics to stderr.
    pymupdf.TOOLS.mupdf_display_errors(False)
    try:
        return _layout(_html(markdown), source_path.parent)
    except Exception as error:
        # Neither markdown-it-py nor Story documents its exception types, so
        # any failure is reported as the Source's.
        raise KwamdError(f"Cannot render Source {source_path}: {one_line(error)}") from None


def _html(markdown: str) -> str:
    tokens = MARKDOWN.parse(markdown)
    _unlink_missing_anchors(tokens, _add_heading_ids(tokens))
    html: str = MARKDOWN.renderer.render(tokens, MARKDOWN.options, {})
    return html


def _layout(html: str, folder: Path) -> bytes:
    story = pymupdf.Story(html, user_css=STYLE, archive=pymupdf.Archive(str(folder)))
    document = story.write_with_links(lambda _n, _filled: (PAGE, CONTENT, None))
    try:
        pdf: bytes = document.tobytes()
        return pdf
    finally:
        document.close()


def _add_heading_ids(tokens: list[Token]) -> set[str]:
    """Give each heading the id GitHub would, so ``[x](#some-heading)`` links work.

    Returns the ids given.
    """
    seen: Counter[str] = Counter()
    ids = set()
    for opening, inline in pairwise(tokens):
        if opening.type != "heading_open":
            continue
        slug = _slug(inline.content)
        heading_id = f"{slug}-{seen[slug]}" if seen[slug] else slug
        opening.attrSet("id", heading_id)
        ids.add(heading_id)
        seen[slug] += 1
    return ids


def _unlink_missing_anchors(tokens: list[Token], ids: set[str]) -> None:
    """Turn a link to a heading that doesn't exist into plain text.

    Story raises on a link whose target id is missing.
    """
    for token in tokens:
        for child in token.children or []:
            href = child.attrGet("href")
            if (
                child.type == "link_open"
                and isinstance(href, str)
                and href.startswith("#")
                and href[1:] not in ids
            ):
                del child.attrs["href"]


def _slug(heading: str) -> str:
    """GitHub's heading anchor: lowercase, punctuation dropped, spaces as hyphens."""
    return re.sub(r"[^\w\- ]", "", heading.strip().lower()).replace(" ", "-")
