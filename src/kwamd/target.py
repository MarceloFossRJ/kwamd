"""Resolution and writing of the Target a conversion writes to."""

import os
from itertools import count
from pathlib import Path

from kwamd.errors import KwamdError


def resolve_target(source: Path, requested: str | None, cwd: Path) -> Path:
    """Return the path the Markdown should be written to.

    ``requested`` is the target argument exactly as typed, so that a trailing
    separator (``out/``) still means "a folder". A relative ``requested`` is
    read against ``cwd``; the returned path is always absolute and normalised.

    An existing file is never chosen: like a browser download, the first free
    ``<stem> (<n>)<suffix>`` is used instead, with the lowest ``n`` from 1.
    """
    default_name = f"{source.stem}.md"
    if requested is None:
        wanted = cwd / default_name
    else:
        requested_path = Path(os.path.abspath(cwd / requested))
        if requested.endswith(("/", os.sep)) or requested_path.is_dir():
            if not requested_path.is_dir():
                raise KwamdError(f"Target folder does not exist: {requested_path}")
            wanted = requested_path / default_name
        else:
            wanted = requested_path
    if not wanted.parent.is_dir():
        raise KwamdError(f"Target folder does not exist: {wanted.parent}")
    return _first_free(wanted)


def _first_free(wanted: Path) -> Path:
    """Return ``wanted`` if nothing exists there, else its lowest free numbered variant."""
    if not wanted.exists():
        return wanted
    for n in count(1):
        candidate = wanted.with_name(f"{wanted.stem} ({n}){wanted.suffix}")
        if not candidate.exists():
            return candidate
    raise AssertionError("unreachable")


def write_target(target: Path, markdown: str) -> None:
    """Create ``target`` with ``markdown`` as UTF-8, refusing to replace an existing file."""
    try:
        with target.open("x", encoding="utf-8") as file:
            file.write(markdown)
    except OSError as error:
        raise KwamdError(f"Cannot write Target {target}: {error.strerror}") from None
