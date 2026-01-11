"""mg error types.

These are user-facing, expected failures - not internal bugs.
"""


class CommandError(Exception):
    """Raised when a command fails in an expected way.

    Examples: missing required flag, invalid input, precondition not met.
    """

    pass
