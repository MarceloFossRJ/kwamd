"""Rendering of Markdown text into a PDF document.

This is the only module that knows about markdown-it-py and PyMuPDF's Story
(see docs/adr/0002-markdown-rendering-engine.md).
"""

import re
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
    quiet_mupdf()
    try:
        return _layout(_html(markdown), source_path.parent)
    except Exception as error:
        # Neither markdown-it-py nor Story documents its exception types, so
        # any failure is reported as the Source's.
        raise KwamdError(f"Cannot render Source {source_path}: {one_line(error)}") from None


def _html(markdown: str) -> str:
    tokens = MARKDOWN.parse(markdown)
    _resolve_anchor_links(tokens, _add_heading_ids(tokens))
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
    for token in tokens:
        for child in token.children or []:
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
