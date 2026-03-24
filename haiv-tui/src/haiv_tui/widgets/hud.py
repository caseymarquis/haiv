"""HUD widget — always-visible panel for the active mind's session.

Shows mind name, task, branch, and action bar for the active worktree.
Subscribes to active_mind_changed and sessions_changed signals.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from haiv.helpers.tui.TuiModel import ActiveMindRaw, SessionsRaw
from haiv.settings import HaivSettings
from haiv_tui.widgets.recent_files import RecentFilesWidget
from haiv_tui.widgets.sessions import SessionActionBar

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from haiv_tui.store import TuiStore


# ---------------------------------------------------------------------------
# Widget
# ---------------------------------------------------------------------------


class HudWidget(Horizontal):
    """Head-up display for the active mind — always visible."""

    DEFAULT_CSS = """
    HudWidget {
        height: 1fr;
    }
    HudWidget #hud-action-bar {
        width: auto;
        height: 1fr;
        padding: 1 1 0 1;
        border-right: solid $surface-lighten-2;
    }
    HudWidget #hud-content {
        width: 1fr;
        height: 1fr;
        padding: 1 1 0 1;
    }
    """

    def __init__(
        self,
        *,
        store: TuiStore,
        worktrees_dir: Path | None,
        settings: HaivSettings,
        errors: deque[str],
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._store = store
        self._worktrees_dir = worktrees_dir
        self._settings = settings
        self._errors = errors
        self._active_mind: ActiveMindRaw | None = None
        self._sessions: SessionsRaw | None = None

    def compose(self) -> ComposeResult:
        yield SessionActionBar(
            settings=self._settings,
            errors=self._errors,
            id="hud-action-bar",
        )
        with Vertical(id="hud-content"):
            yield RecentFilesWidget(store=self._store, id="recent-files")

    def on_mount(self) -> None:
        self._store.active_mind_changed.connect(self._on_active_mind_changed)
        self._store.sessions_changed.connect(self._on_sessions_changed)
        if self._store.snapshot is not None:
            self._active_mind = self._store.snapshot.active_mind
            self._sessions = self._store.snapshot.sessions
            self._refresh()

    def _on_active_mind_changed(self, sender) -> None:
        self._active_mind = sender
        self._refresh()

    def _on_sessions_changed(self, sender) -> None:
        self._sessions = sender
        self._refresh()

    def _refresh(self) -> None:
        view = build_hud_view(self._active_mind, self._sessions, self._worktrees_dir)
        self.app.title = f"{view.session_display}  ·  {view.summary}"
        self.query_one(SessionActionBar).set_path(view.worktree_path)


# ---------------------------------------------------------------------------
# DTO
# ---------------------------------------------------------------------------


@dataclass
class HudView:
    """What the HUD widget needs to render."""

    worktree: str
    summary: str
    session_display: str
    worktree_path: Path | None = None


# ---------------------------------------------------------------------------
# Assembly
# ---------------------------------------------------------------------------


def build_hud_view(
    active_mind: ActiveMindRaw | None,
    sessions: SessionsRaw | None,
    worktrees_dir: Path | None = None,
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

    branch = session.branch if session else None
    wt_path = worktrees_dir / branch if worktrees_dir and branch else None

    return HudView(
        worktree=branch or "—",
        summary=session.task or "—" if session else "—",
        session_display=f"{mind_name} [{session.short_id}]" if session else mind_name,
        worktree_path=wt_path,
    )
