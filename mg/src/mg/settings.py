"""Settings for mg projects."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class MgSettings:
    """Settings for an mg project.

    Private fields hold loaded values (None = not set).
    Public properties provide effective values with fallbacks.
    """

    _default_branch: str | None = None

    @property
    def default_branch(self) -> str:
        """The default branch name. Falls back to 'main' if not set."""
        return self._default_branch if self._default_branch is not None else "main"
