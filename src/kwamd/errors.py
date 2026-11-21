"""Failures that stop a conversion and are reported to the user."""


class KwamdError(Exception):
    """A Source or Target problem; its message is shown to the user as-is."""
