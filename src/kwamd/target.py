"""Resolution and writing of the Target a conversion writes to."""

import os
from itertools import count
from pathlib import Path

from kwamd.errors import KwamdError


def resolve_target(source_path: Path, requested_target: str | None, cwd: Path, suffix: str) -> Path:
    """Return the path the Target should be written to.

    ``suffix`` (``.md`` or ``.pdf``) names the default Target: ``<source stem><suffix>``.

    ``requested_target`` is the target argument exactly as typed, so that a
    trailing separator (``out/``) still means "a folder". A relative one is read
    against ``cwd``; the returned path is always absolute and normalised.

    Nothing that exists is ever chosen, not even a dangling symlink: like a
    browser download, the first free ``<stem> (<n>)<suffix>`` is used instead,
    with the lowest ``n`` from 1.
    """
    default_name = f"{source_path.stem}{suffix}"
    if requested_target is None:
        wanted = cwd / default_name
    else:
        requested_path = Path(os.path.abspath(cwd / requested_target))
        if requested_target.endswith(("/", os.sep)) or requested_path.is_dir():
            if os.path.lexists(requested_path) and not requested_path.is_dir():
                raise KwamdError(f"Target is not a folder: {requested_path}")
            wanted = requested_path / default_name
        else:
            wanted = requested_path
    if not wanted.parent.is_dir():
        raise KwamdError(f"Target folder does not exist: {wanted.parent}")
    return _first_free(wanted)


def _first_free(wanted: Path) -> Path:
    """Return ``wanted`` if nothing is there, else its lowest free numbered variant."""
    if not os.path.lexists(wanted):
        return wanted
    for n in count(1):
        candidate = wanted.with_name(f"{wanted.stem} ({n}){wanted.suffix}")
        if not os.path.lexists(candidate):
            return candidate
    raise AssertionError("unreachable")


def write_target(target: Path, content: str | bytes) -> None:
    """Create ``target`` with ``content`` (text is written as UTF-8), refusing to replace
    an existing file.

    On failure no partial Target is left behind.
    """
    if isinstance(content, str):
        try:
            content = content.encode("utf-8")
        except UnicodeEncodeError as error:
            raise _write_failure(target, f"text is not valid UTF-8 ({error.reason})") from None
    try:
        file = target.open("xb")
    except OSError as error:
        raise _write_failure(target, error.strerror) from None
    try:
        with file:
            file.write(content)
    except OSError as error:
        target.unlink(missing_ok=True)
        raise _write_failure(target, error.strerror) from None


def _write_failure(target: Path, reason: str | None) -> KwamdError:
    return KwamdError(f"Cannot write Target {target}: {reason}")
