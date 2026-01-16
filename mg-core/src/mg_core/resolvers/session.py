"""Resolver for session identifiers.

Converts a session identifier (short_id or UUID) to a Session object.
"""

from mg._infrastructure.resolvers import ResolverContext
from mg.errors import CommandError
from mg.helpers.sessions import Session, get_session


class SessionNotFoundError(CommandError):
    """Raised when a session cannot be found."""

    def __init__(self, identifier: str):
        self.identifier = identifier
        super().__init__(f"Session not found: {identifier}")


def resolve(value: str, ctx: ResolverContext) -> Session:
    """Resolve a session identifier to a Session object.

    Args:
        value: Session identifier - either short_id (e.g., "3") or partial/full UUID.
        ctx: Resolver context with paths.

    Returns:
        Session object.

    Raises:
        SessionNotFoundError: If no matching session found.
    """
    session = get_session(ctx.paths.user.sessions_file, value)
    if session is None:
        raise SessionNotFoundError(value)
    return session
