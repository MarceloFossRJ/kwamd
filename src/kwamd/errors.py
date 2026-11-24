"""Failures that stop a conversion and are reported to the user."""


class KwamdError(Exception):
    """A Source or Target problem; its message is shown to the user as-is."""


def one_line(error: BaseException) -> str:
    """A library error's text flattened to one line, so a report stays one line."""
    return " ".join(str(error).split())
