"""Recent files widget — shows recently modified files with diff stats.

Subscribes to recent_files_changed signal. Files are colored on a gradient
from bright green (just modified) to faded gray (older edits).
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Static

from haiv.helpers.tui.TuiModel import ActiveMindRaw, RecentFilesRaw, SessionsRaw

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from haiv_tui.store import TuiStore


# ---------------------------------------------------------------------------
# Widget
# ---------------------------------------------------------------------------


class RecentFilesWidget(Vertical):
    """Displays recently modified files with age-based coloring and diff stats."""

    DEFAULT_CSS = """
    RecentFilesWidget {
        height: 1fr;
        padding: 0 1;
    }
    RecentFilesWidget #recent-files-content {
        height: auto;
    }
    """

    def __init__(self, *, store: TuiStore, **kwargs) -> None:
        super().__init__(**kwargs)
        self._store = store
        self._recent_files: RecentFilesRaw | None = None
        self._active_mind: ActiveMindRaw | None = None
        self._sessions: SessionsRaw | None = None

    def compose(self) -> ComposeResult:
        yield Static("", id="recent-files-content")

    def on_mount(self) -> None:
        self._store.recent_files_changed.connect(self._on_recent_files_changed)
        self._store.active_mind_changed.connect(self._on_active_mind_changed)
        self._store.sessions_changed.connect(self._on_sessions_changed)
        if self._store.snapshot is not None:
            self._recent_files = self._store.snapshot.recent_files
            self._active_mind = self._store.snapshot.active_mind
            self._sessions = self._store.snapshot.sessions
            self._refresh_content()

    def _on_recent_files_changed(self, sender) -> None:
        self._recent_files = sender
        self._refresh_content()

    def _on_active_mind_changed(self, sender) -> None:
        self._active_mind = sender
        self._refresh_content()

    def _on_sessions_changed(self, sender) -> None:
        self._sessions = sender
        self._refresh_content()

    def _active_worktree(self) -> str | None:
        """Resolve the active mind's worktree (branch) name."""
        mind = self._active_mind.mind if self._active_mind else None
        if not mind or not self._sessions:
            return None
        for entry in self._sessions.entries:
            if entry.mind == mind:
                return entry.branch or None
        return None

    def _refresh_content(self) -> None:
        content = self.query_one("#recent-files-content", Static)
        if not self._recent_files or not self._recent_files.files:
            content.update("No recent files")
            return

        worktree = self._active_worktree()
        views = build_recent_files_view(self._recent_files, worktree=worktree)
        if not views:
            content.update("No recent files")
            return

        text = Text()
        text.append("Recently Edited Files\n", style="bold")
        for i, v in enumerate(views):
            if i > 0:
                text.append("\n")
            text.append(v.diff_display, style=v.diff_style)
            text.append(" ")
            text.append(v.display_path, style=v.age_style)
            if not worktree:
                text.append(f"  ({v.worktree})", style="dim")
        content.update(text)


# ---------------------------------------------------------------------------
# DTO
# ---------------------------------------------------------------------------


@dataclass
class RecentFileView:
    """What the widget needs to render one file entry."""

    display_path: str
    worktree: str
    diff_display: str
    diff_style: str
    age_style: str


# ---------------------------------------------------------------------------
# Assembly
# ---------------------------------------------------------------------------


# Age gradient: bright green → dim green → gray → dim gray
_AGE_STOPS = [
    (60,      "#00ff00"),  # < 1 min: bright green
    (300,     "#00cc00"),  # < 5 min: green
    (1800,    "#00aa00"),  # < 30 min: muted green
    (3600,    "#888888"),  # < 1 hour: gray
]
_AGE_DEFAULT = "#555555"   # older: dim gray


def _age_color(mtime: float, now: float) -> str:
    age = now - mtime
    for threshold, color in _AGE_STOPS:
        if age < threshold:
            return color
    return _AGE_DEFAULT


def build_recent_files_view(raw: RecentFilesRaw, *, worktree: str | None = None) -> list[RecentFileView]:
    """Assemble display views from raw recent files data.

    Args:
        raw: The raw file data.
        worktree: If set, only show files from this worktree.

    Pure function — raw data in, DTOs out. Testable without Textual.
    """
    now = time.time()
    views = []
    for entry in raw.files:
        if worktree and entry.worktree != worktree:
            continue
        if entry.additions or entry.deletions:
            diff_display = f"+{entry.additions} -{entry.deletions}"
            diff_style = "green" if entry.additions >= entry.deletions else "red"
        else:
            diff_display = "     "
            diff_style = ""

        views.append(RecentFileView(
            display_path=entry.path,
            worktree=entry.worktree,
            diff_display=f"{diff_display:>10}",
            diff_style=diff_style,
            age_style=_age_color(entry.mtime, now),
        ))
    return views
