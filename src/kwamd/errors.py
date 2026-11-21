"""Failures that stop a conversion and are reported to the user."""


class KwamdError(Exception):
    """A Source or Target problem; its message is shown to the user as-is."""


class PasswordRequired(KwamdError):
    """The Source can only be opened with a password, and none was given."""


class WrongPassword(KwamdError):
    """The password given does not open the Source."""
