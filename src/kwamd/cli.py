"""The ``kwamd`` command: argument parsing, orchestration and exit codes.

Exit codes: 0 success, 1 Source or Target failure, 2 usage error (argparse).
This is the only module that prints.
"""

import argparse
import getpass
import sys
from collections.abc import Sequence
from importlib.metadata import version
from pathlib import Path

from kwamd.conversion import convert
from kwamd.errors import KwamdError, PasswordRequired, WrongPassword
from kwamd.source import CheckedSource, check_source
from kwamd.target import resolve_target, write_target


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="kwamd",
        description="Convert a PDF document into a Markdown file.",
        allow_abbrev=False,
    )
    parser.add_argument("source", type=Path, help="the PDF to convert")
    parser.add_argument(
        "target",
        nargs="?",
        help="where to write the Markdown (default: <source name>.md in the current folder)",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {version('kwamd')}")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    try:
        args = _parser().parse_args(argv)
    except SystemExit as stop:
        # argparse exits on --help/--version (0) and on usage errors (2).
        return stop.code if isinstance(stop.code, int) else 2
    try:
        target = _run(args.source, args.target)
    except KwamdError as error:
        print(f"kwamd: error: {error}", file=sys.stderr)
        return 1
    print(target)
    return 0


PASSWORD_ATTEMPTS = 3


def _run(source: Path, requested: str | None) -> Path:
    try:
        checked = check_source(source)
    except PasswordRequired:
        checked = _check_with_password_from_prompt(source)
    target = resolve_target(source, requested, Path.cwd())
    write_target(target, convert(source, checked.password))
    if checked.scanned:
        print(
            f"kwamd: warning: Source looks scanned (most pages have no text): {source}; "
            "OCR is not supported yet, so the Target may be nearly empty",
            file=sys.stderr,
        )
    return target


def _check_with_password_from_prompt(source: Path) -> CheckedSource:
    """Ask the person at the terminal for the Source's password, like sudo does."""
    if not sys.stdin.isatty():
        raise KwamdError(
            f"Source is password-protected and there is no terminal to ask for it: {source}"
        )
    for attempt in range(1, PASSWORD_ATTEMPTS + 1):
        try:
            password = getpass.getpass(f"Password for {source.name}: ")
        except EOFError:
            raise KwamdError(f"No password given for Source: {source}") from None
        try:
            return check_source(source, password)
        except WrongPassword:
            if attempt == PASSWORD_ATTEMPTS:
                raise
            print("kwamd: wrong password, try again", file=sys.stderr)
    raise AssertionError("unreachable")
