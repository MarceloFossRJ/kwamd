"""The ``kwamd`` command: argument parsing, orchestration and exit codes.

Exit codes: 0 success, 1 Source or Target failure, 2 usage error (argparse),
130 interrupted (Ctrl-C).
This is the only module that talks to the person: it prints and prompts.
"""

import argparse
import getpass
import sys
from collections.abc import Iterator, Sequence
from importlib.metadata import version
from pathlib import Path

from kwamd.conversion import convert
from kwamd.errors import KwamdError
from kwamd.source import open_source
from kwamd.target import resolve_target, write_target

PASSWORD_ATTEMPTS = 3


def _non_empty(value: str) -> str:
    if not value:
        raise argparse.ArgumentTypeError("must not be empty")
    return value


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="kwamd",
        description="Convert a PDF document into a Markdown file.",
        allow_abbrev=False,
    )
    parser.add_argument("source", type=_non_empty, help="the PDF to convert")
    parser.add_argument(
        "target",
        type=_non_empty,
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
        target = _run(Path(args.source), args.target)
    except KwamdError as error:
        print(f"kwamd: error: {error}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("kwamd: interrupted", file=sys.stderr)
        return 130
    print(target)
    return 0


def _run(source_path: Path, requested_target: str | None) -> Path:
    # Check the Target first, so nobody types a password only to hit a bad path.
    target = resolve_target(source_path, requested_target, Path.cwd())
    with open_source(source_path, _passwords_from_prompt(source_path)) as source:
        write_target(target, convert(source))
        if source.scanned:
            print(
                f"kwamd: warning: Source looks scanned (most pages have no text): {source.path}; "
                "OCR is not supported yet, so the Target may be nearly empty",
                file=sys.stderr,
            )
    return target


def _passwords_from_prompt(source_path: Path) -> Iterator[str]:
    """Ask the person at the terminal for the Source's password, like sudo does.

    Lazy: nothing is asked unless the Source turns out to be password-protected.
    """
    if not sys.stdin.isatty():
        raise KwamdError(
            f"Source is password-protected and there is no terminal to ask for it: {source_path}"
        )
    for attempt in range(PASSWORD_ATTEMPTS):
        if attempt:
            print("kwamd: wrong password, try again", file=sys.stderr)
        try:
            yield getpass.getpass(f"Password for {source_path.name}: ")
        except EOFError:
            raise KwamdError(f"No password given for Source: {source_path}") from None
