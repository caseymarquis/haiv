"""Recent files widget — shows recently modified files with diff stats.

Subscribes to recent_files_changed signal. Files are colored on a gradient
from bright green (just modified) to faded gray (older edits). Double-click
or Enter opens the file in the configured editor.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.events import Click
from textual.widgets import OptionList, Static
from textual.widgets.option_list import Option

from haiv.helpers.open import open_in_editor
from haiv.helpers.tui.TuiModel import ActiveMindRaw, RecentFilesRaw, SessionsRaw
from haiv.settings import HaivSettings

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections import deque

    from haiv_tui.store import TuiStore


# ---------------------------------------------------------------------------
# Widget
# ---------------------------------------------------------------------------


class RecentFilesWidget(Vertical):
    """Displays recently modified files with age-based coloring and diff stats."""

    DEFAULT_CSS = """
    RecentFilesWidget {
        height: 1fr;
    }
    RecentFilesWidget #recent-files-header {
        height: auto;
        padding: 0 1;
    }
    RecentFilesWidget #recent-files-list {
        height: 1fr;
        padding: 0 1;
    }
    RecentFilesWidget #recent-files-path {
        height: auto;
        padding: 0 1;
        color: $text-muted;
    }
    """

    BINDINGS = [
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
        Binding("enter", "open_highlighted", "Open", show=False),
    ]

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
        self._recent_files: RecentFilesRaw | None = None
        self._active_mind: ActiveMindRaw | None = None
        self._sessions: SessionsRaw | None = None

    def compose(self) -> ComposeResult:
        yield Static("Recently Edited Files", id="recent-files-header")
        yield OptionList(id="recent-files-list")
        yield Static("", id="recent-files-path")

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
        option_list = self.query_one("#recent-files-list", OptionList)
        prev_highlighted = option_list.highlighted
        option_list.clear_options()

        if not self._recent_files or not self._recent_files.files:
            return

        worktree = self._active_worktree()
        views = build_recent_files_view(self._recent_files, worktree=worktree)

        for v in views:
            line = Text()
            line.append(v.diff_display, style=v.diff_style)
            line.append(" ")
            line.append(v.display_path, style=v.age_style)
            if not worktree:
                line.append(f"  ({v.worktree})", style="dim")
            # id encodes worktree:path for resolution on selection
            option_list.add_option(Option(line, id=f"{v.worktree}\t{v.full_path}"))

        if prev_highlighted is not None and option_list.option_count > 0:
            option_list.highlighted = min(prev_highlighted, option_list.option_count - 1)

    def on_option_list_option_highlighted(self, event: OptionList.OptionHighlighted) -> None:
        """Show full path at bottom when highlighted."""
        path_display = self.query_one("#recent-files-path", Static)
        if event.option.id:
            parts = event.option.id.split("\t", 1)
            if len(parts) == 2 and self._worktrees_dir:
                full = self._worktrees_dir / parts[0] / parts[1]
                path_display.update(str(full))
                return
        path_display.update("")

    def on_click(self, event: Click) -> None:
        """Double-click opens the highlighted file."""
        if event.chain >= 2:
            self.action_open_highlighted()

    def action_open_highlighted(self) -> None:
        """Open the currently highlighted file in the editor."""
        option_list = self.query_one("#recent-files-list", OptionList)
        highlighted = option_list.highlighted
        if highlighted is not None:
            option = option_list.get_option_at_index(highlighted)
            self._open_file(option.id)

    def _open_file(self, option_id: str | None) -> None:
        if not option_id or not self._worktrees_dir:
            return
        parts = option_id.split("\t", 1)
        if len(parts) != 2:
            return
        wt, rel_path = parts
        full_path = self._worktrees_dir / wt / rel_path
        if full_path.is_file():
            try:
                open_in_editor(full_path, self._settings.editor_command)
            except Exception as e:
                self._errors.append(f"open_file: {e}")

    def action_cursor_down(self) -> None:
        self.query_one(OptionList).action_cursor_down()

    def action_cursor_up(self) -> None:
        self.query_one(OptionList).action_cursor_up()


# ---------------------------------------------------------------------------
# DTO
# ---------------------------------------------------------------------------


@dataclass
class RecentFileView:
    """What the widget needs to render one file entry."""

    display_path: str
    full_path: str
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


def shortest_unique_names(paths: list[str]) -> list[str]:
    """Compute the shortest unique suffix for each path.

    Given ["src/haiv/helpers/tui/helpers.py", "src/haiv/helpers/utils/helpers.py", "app.py"],
    returns ["tui/helpers.py", "utils/helpers.py", "app.py"].
    """
    from pathlib import PurePath

    parts_list = [PurePath(p).parts for p in paths]
    result = []
    for i, parts in enumerate(parts_list):
        # Start with just the filename, extend until unique
        for depth in range(1, len(parts) + 1):
            suffix = parts[-depth:]
            suffix_str = "/".join(suffix)
            # Check if any other path ends with the same suffix
            unique = True
            for j, other_parts in enumerate(parts_list):
                if i == j:
                    continue
                if len(other_parts) >= depth and other_parts[-depth:] == suffix:
                    unique = False
                    break
            if unique:
                result.append(suffix_str)
                break
        else:
            result.append(paths[i])
    return result


def build_recent_files_view(raw: RecentFilesRaw, *, worktree: str | None = None) -> list[RecentFileView]:
    """Assemble display views from raw recent files data.

    Args:
        raw: The raw file data.
        worktree: If set, only show files from this worktree.

    Pure function — raw data in, DTOs out. Testable without Textual.
    """
    filtered = [e for e in raw.files if not worktree or e.worktree == worktree]
    short_names = shortest_unique_names([e.path for e in filtered])
    now = time.time()
    views = []
    for entry, short_name in zip(filtered, short_names):
        if entry.additions or entry.deletions:
            diff_display = f"+{entry.additions} -{entry.deletions}"
            diff_style = "green" if entry.additions >= entry.deletions else "red"
        else:
            diff_display = "     "
            diff_style = ""

        views.append(RecentFileView(
            display_path=short_name,
            full_path=entry.path,
            worktree=entry.worktree,
            diff_display=f"{diff_display:>10}",
            diff_style=diff_style,
            age_style=_age_color(entry.mtime, now),
        ))
    return views
