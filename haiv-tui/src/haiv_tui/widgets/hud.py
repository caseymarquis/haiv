"""HUD widget — displays info about the active mind.

Subscribes to active_mind_changed and sessions_changed signals.
Widget renders HudView DTOs assembled from raw data.
"""

from __future__ import annotations

from dataclasses import dataclass

from textual.widgets import Static

from haiv.helpers.tui.TuiModel import ActiveMindRaw, SessionsRaw

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from haiv_tui.store import TuiStore


# ---------------------------------------------------------------------------
# Widget
# ---------------------------------------------------------------------------


class HudWidget(Static):
    """Head-up display showing active mind details."""

    DEFAULT_CSS = """
    HudWidget {
        height: 5;
        border: solid yellow;
        padding: 0 1;
    }
    """

    def __init__(self, *, store: TuiStore, **kwargs) -> None:
        super().__init__(**kwargs)
        self._store = store
        self._active_mind: ActiveMindRaw | None = None
        self._sessions: SessionsRaw | None = None

    def on_mount(self) -> None:
        self._store.active_mind_changed.connect(self._on_active_mind_changed)
        self._store.sessions_changed.connect(self._on_sessions_changed)
        if self._store.snapshot is not None:
            self._active_mind = self._store.snapshot.active_mind
            self._sessions = self._store.snapshot.sessions
            self._refresh_hud()

    def _on_active_mind_changed(self, sender) -> None:
        self._active_mind = sender
        self._refresh_hud()

    def _on_sessions_changed(self, sender) -> None:
        self._sessions = sender
        self._refresh_hud()

    def _refresh_hud(self) -> None:
        view = build_hud_view(self._active_mind, self._sessions)
        self.update(
            f"Worktree: {view.worktree}\n"
            f"Summary: {view.summary}\n"
            f"Session: {view.session_display}"
        )


# ---------------------------------------------------------------------------
# DTO
# ---------------------------------------------------------------------------


@dataclass
class HudView:
    """What the HUD widget needs to render."""

    worktree: str
    summary: str
    session_display: str


# ---------------------------------------------------------------------------
# Assembly
# ---------------------------------------------------------------------------


def build_hud_view(
    active_mind: ActiveMindRaw | None,
    sessions: SessionsRaw | None,
) -> HudView:
    """Assemble HUD display from raw data.

    Pure function — raw data in, DTO out. Testable without Textual.
    """
    mind_name = active_mind.mind if active_mind else ""
    if not mind_name:
        return HudView(worktree="—", summary="—", session_display="—")

    session = None
    if sessions:
        for entry in sessions.entries:
            if entry.mind == mind_name:
                session = entry
                break

    return HudView(
        worktree=session.branch or "—" if session else "—",
        summary=session.task or "—" if session else "—",
        session_display=f"{mind_name} [{session.short_id}]" if session else mind_name,
    )
