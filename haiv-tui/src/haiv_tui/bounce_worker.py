"""Bounce worker — cycles to the next session.

Reads the current model to find bounce-eligible sessions, picks the
next one after the active mind, and launches it.
"""

from __future__ import annotations

from pathlib import Path

from haiv.helpers.tui import helpers
from haiv.helpers.tui.protocol import ModelClient
from haiv.helpers.tui.terminal import TerminalManager
from haiv.wrappers.git import Git


class BounceWorker:
    """Handles bounce commands by switching to the next session."""

    def __init__(
        self,
        *,
        client: ModelClient,
        terminal: TerminalManager | None,
        sessions_file: Path,
        haiv_root: Path,
        git: Git | None,
    ) -> None:
        self._client = client
        self._terminal = terminal
        self._sessions_file = sessions_file
        self._haiv_root = haiv_root
        self._git = git

    def handle(self) -> None:
        """Switch to the next session in ID order."""
        snapshot = self._client.read()
        if not snapshot.sessions or not snapshot.sessions.entries:
            return

        entries = sorted(
            [e for e in snapshot.sessions.entries if e.bounce],
            key=lambda e: e.mind,
        )
        if not entries:
            return

        active = snapshot.active_mind.mind if snapshot.active_mind else None
        if active is None:
            target = entries[0]
        else:
            active_idx = next(
                (i for i, e in enumerate(entries) if e.mind == active),
                None,
            )
            if active_idx is None:
                target = entries[0]
            else:
                target = entries[(active_idx + 1) % len(entries)]

        if self._terminal is not None:
            helpers.mind_launch(
                self._terminal,
                self._client,
                self._sessions_file,
                target.mind,
                self._haiv_root,
                git=self._git,
            )
