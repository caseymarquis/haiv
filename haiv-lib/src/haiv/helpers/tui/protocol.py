"""Client protocol — unites TuiClient (remote) and TuiLocalClient (local).

Both clients provide the same read/write_raw/send_command interface.
Use this protocol as the type hint when a function accepts either client type.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from haiv._infrastructure.TuiServer._TuiIpc import TuiCommand
from haiv.helpers.tui.TuiModel import ActiveMindRaw, GitRaw, RecentCommitsRaw, RecentFilesRaw, SessionsRaw, TuiModel


@runtime_checkable
class ModelClient(Protocol):
    """Protocol for TUI model access."""

    def read(self) -> TuiModel: ...
    def write_raw(
        self,
        *,
        sessions: SessionsRaw | None = None,
        git: GitRaw | None = None,
        active_mind: ActiveMindRaw | None = None,
        recent_files: RecentFilesRaw | None = None,
        recent_commits: RecentCommitsRaw | None = None,
    ) -> None: ...
    def send_command(self, command: TuiCommand) -> None: ...
