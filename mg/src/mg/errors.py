"""mg error types.

These are user-facing, expected failures - not internal bugs.
"""


class CommandError(Exception):
    """Raised when a command fails in an expected way.

    Examples: missing required flag, invalid input, precondition not met.
    """

    pass


class GitError(CommandError):
    """Raised when a git command fails.

    Attributes:
        stderr: The stderr output from the git command.
    """

    def __init__(self, message: str, stderr: str = ""):
        super().__init__(message)
        self.stderr = stderr
