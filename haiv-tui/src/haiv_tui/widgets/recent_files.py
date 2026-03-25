"""Pending changes widget — tree view of file changes and recent commits.

Subscribes to recent_files_changed and recent_commits_changed signals.
Files are colored on a gradient from bright green (just modified) to faded
gray (older edits). Double-click or Enter opens a file in the configured editor.

Tree categories:
  - Conflicted (hidden when empty)
  - Recently Modified
  - Deleted
  - Recent Commits (collapsed by default, expand to see files)
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.widgets import Static, Tree
from textual.widgets.tree import TreeNode

from haiv.helpers.open import open_in_editor
from haiv.helpers.tui.TuiModel import (
    ActiveMindRaw,
    CommitEntry,
    FileStatus,
    RecentCommitsRaw,
    RecentFileEntry,
    RecentFilesRaw,
    SessionsRaw,
)
from haiv.settings import HaivSettings

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections import deque

    from haiv_tui.store import TuiStore


# ---------------------------------------------------------------------------
# Widget
# ---------------------------------------------------------------------------


class RecentFilesWidget(Vertical):
    """Tree view of pending file changes across worktrees."""

    DEFAULT_CSS = """
    RecentFilesWidget {
        height: 1fr;
    }
    RecentFilesWidget #recent-files-header {
        height: auto;
        padding: 0 1;
    }
    RecentFilesWidget #recent-files-tree {
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
        self._recent_commits: RecentCommitsRaw | None = None
        self._active_mind: ActiveMindRaw | None = None
        self._sessions: SessionsRaw | None = None

    def compose(self) -> ComposeResult:
        yield Static("Pending Changes", id="recent-files-header")
        yield Tree("", id="recent-files-tree")
        yield Static("", id="recent-files-path")

    def on_mount(self) -> None:
        tree = self.query_one("#recent-files-tree", Tree)
        tree.show_root = False
        tree.guide_depth = 2

        self._store.recent_files_changed.connect(self._on_recent_files_changed)
        self._store.recent_commits_changed.connect(self._on_recent_commits_changed)
        self._store.active_mind_changed.connect(self._on_active_mind_changed)
        self._store.sessions_changed.connect(self._on_sessions_changed)
        if self._store.snapshot is not None:
            self._recent_files = self._store.snapshot.recent_files
            self._recent_commits = self._store.snapshot.recent_commits
            self._active_mind = self._store.snapshot.active_mind
            self._sessions = self._store.snapshot.sessions
            self._refresh_content()

    def _on_recent_files_changed(self, sender) -> None:
        self._recent_files = sender
        self._refresh_content()

    def _on_recent_commits_changed(self, sender) -> None:
        self._recent_commits = sender
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
        tree = self.query_one("#recent-files-tree", Tree)
        tree.clear()

        worktree = self._active_worktree()

        # File categories
        if self._recent_files:
            views = build_file_tree_views(self._recent_files, worktree=worktree)
            for category in views:
                if not category.entries:
                    continue
                cat_label = Text(f"{category.label} ({len(category.entries)})", style="bold")
                cat_node = tree.root.add(cat_label)

                for v in category.entries:
                    line = Text()
                    line.append(v.diff_display, style=v.diff_style)
                    line.append(" ")
                    line.append(v.display_path, style=v.age_style)
                    if not worktree:
                        line.append(f"  ({v.worktree})", style="dim")
                    if v.age_display:
                        line.append(f"  {v.age_display}", style="dim italic")
                    cat_node.add_leaf(
                        line,
                        data=FileNodeData(worktree=v.worktree, path=v.full_path),
                    )

                cat_node.expand()

        # Recent commits
        if self._recent_commits:
            commit_views = build_commit_views(self._recent_commits, worktree=worktree)
            if commit_views:
                cat_label = Text(f"Recent Commits ({len(commit_views)})", style="bold")
                cat_node = tree.root.add(cat_label)

                for cv in commit_views:
                    # Commit node: short hash + subject + age
                    commit_label = Text()
                    commit_label.append(cv.short_hash, style="cyan")
                    commit_label.append(" ")
                    commit_label.append(cv.subject, style=cv.age_style)
                    if not worktree:
                        commit_label.append(f"  ({cv.worktree})", style="dim")
                    if cv.age_display:
                        commit_label.append(f"  {cv.age_display}", style="dim italic")

                    commit_node = cat_node.add(commit_label)

                    # File children
                    for fv in cv.files:
                        file_label = Text()
                        file_label.append(fv.diff_display, style=fv.diff_style)
                        file_label.append(" ")
                        file_label.append(fv.display_path, style="dim")
                        commit_node.add_leaf(
                            file_label,
                            data=FileNodeData(worktree=cv.worktree, path=fv.full_path),
                        )

                # Collapsed by default — user expands to see commits
                cat_node.collapse()

    def on_tree_node_highlighted(self, event: Tree.NodeHighlighted) -> None:
        """Show full path at bottom when highlighted."""
        path_display = self.query_one("#recent-files-path", Static)
        if isinstance(event.node.data, FileNodeData) and self._worktrees_dir:
            full = self._worktrees_dir / event.node.data.worktree / event.node.data.path
            path_display.update(str(full))
        else:
            path_display.update("")

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        """Open the file on Enter/double-click."""
        if isinstance(event.node.data, FileNodeData):
            self._open_file(event.node.data)

    def _open_file(self, data: FileNodeData) -> None:
        if not self._worktrees_dir:
            return
        full_path = self._worktrees_dir / data.worktree / data.path
        if full_path.is_file():
            try:
                open_in_editor(full_path, self._settings.editor_command)
            except Exception as e:
                self._errors.append(f"open_file: {e}")

    def action_open_highlighted(self) -> None:
        tree = self.query_one("#recent-files-tree", Tree)
        node = tree.cursor_node
        if node is not None and isinstance(node.data, FileNodeData):
            self._open_file(node.data)

    def action_cursor_down(self) -> None:
        self.query_one(Tree).action_cursor_down()

    def action_cursor_up(self) -> None:
        self.query_one(Tree).action_cursor_up()


# ---------------------------------------------------------------------------
# Node data
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FileNodeData:
    """Attached to tree leaf nodes for file identification."""

    worktree: str
    path: str


# ---------------------------------------------------------------------------
# DTOs
# ---------------------------------------------------------------------------


@dataclass
class FileView:
    """What the widget needs to render one file entry."""

    display_path: str
    full_path: str
    worktree: str
    diff_display: str
    diff_style: str
    age_style: str
    age_display: str


@dataclass
class CategoryView:
    """A category (group) of file entries."""

    label: str
    entries: list[FileView]


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
    if mtime == 0.0:
        return _AGE_DEFAULT
    age = now - mtime
    for threshold, color in _AGE_STOPS:
        if age < threshold:
            return color
    return _AGE_DEFAULT


def format_age(seconds: float) -> str:
    """Format seconds into a human-readable relative time.

    Returns "just now", "3m", "1h 3m", "2d", etc.
    """
    if seconds < 60:
        return "just now"
    minutes = int(seconds / 60)
    if minutes < 60:
        return f"{minutes}m"
    hours = minutes // 60
    remaining_min = minutes % 60
    if hours < 24:
        if remaining_min:
            return f"{hours}h {remaining_min}m"
        return f"{hours}h"
    days = hours // 24
    return f"{days}d"


def shortest_unique_names(paths: list[str]) -> list[str]:
    """Compute the shortest unique suffix for each path.

    Given ["src/haiv/helpers/tui/helpers.py", "src/haiv/helpers/utils/helpers.py", "app.py"],
    returns ["tui/helpers.py", "utils/helpers.py", "app.py"].

    Expects forward-slash paths (as produced by git).
    """
    from pathlib import PurePosixPath

    parts_list = [PurePosixPath(p).parts for p in paths]
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


def _build_views(entries: list[RecentFileEntry], now: float, worktree_filter: str | None) -> list[FileView]:
    """Build FileViews from a list of entries. Alphabetical, with shortest unique names."""
    filtered = [e for e in entries if not worktree_filter or e.worktree == worktree_filter]
    if not filtered:
        return []

    short_names = shortest_unique_names([e.path for e in filtered])
    views = []
    for entry, short_name in zip(filtered, short_names):
        if entry.additions or entry.deletions:
            diff_display = f"+{entry.additions} -{entry.deletions}"
            diff_style = "green" if entry.additions >= entry.deletions else "red"
        else:
            diff_display = "     "
            diff_style = ""

        age_seconds = (now - entry.mtime) if entry.mtime > 0 else 0
        age_display = format_age(age_seconds) if entry.mtime > 0 else ""

        views.append(FileView(
            display_path=short_name,
            full_path=entry.path,
            worktree=entry.worktree,
            diff_display=f"{diff_display:>10}",
            diff_style=diff_style,
            age_style=_age_color(entry.mtime, now),
            age_display=age_display,
        ))
    return views


def build_file_tree_views(
    raw: RecentFilesRaw,
    *,
    worktree: str | None = None,
) -> list[CategoryView]:
    """Assemble category views from raw file data.

    Pure function — raw data in, DTOs out. Testable without Textual.
    Returns categories in display order. Empty categories are included
    so the widget can decide whether to hide them.
    """
    now = time.time()
    return [
        CategoryView(
            label="Conflicted",
            entries=_build_views(raw.conflicted, now, worktree),
        ),
        CategoryView(
            label="Recently Modified",
            entries=_build_views(raw.modified, now, worktree),
        ),
        CategoryView(
            label="Deleted",
            entries=_build_views(raw.deleted, now, worktree),
        ),
    ]


# ---------------------------------------------------------------------------
# Commit DTOs
# ---------------------------------------------------------------------------


@dataclass
class CommitFileView:
    """A file within a commit."""

    display_path: str
    full_path: str
    diff_display: str
    diff_style: str


@dataclass
class CommitView:
    """What the widget needs to render one commit."""

    short_hash: str
    subject: str
    worktree: str
    age_style: str
    age_display: str
    files: list[CommitFileView]


# ---------------------------------------------------------------------------
# Commit assembly
# ---------------------------------------------------------------------------


def build_commit_views(
    raw: RecentCommitsRaw,
    *,
    worktree: str | None = None,
) -> list[CommitView]:
    """Assemble commit views from raw data.

    Pure function — raw data in, DTOs out. Testable without Textual.
    """
    now = time.time()
    filtered = [c for c in raw.commits if not worktree or c.worktree == worktree]
    views = []
    for commit in filtered:
        age_seconds = (now - commit.timestamp) if commit.timestamp > 0 else 0
        age_display = format_age(age_seconds) if commit.timestamp > 0 else ""

        # Build file views with shortest unique names within this commit
        if commit.files:
            short_names = shortest_unique_names([f.path for f in commit.files])
        else:
            short_names = []

        file_views = []
        for f, short_name in zip(commit.files, short_names):
            if f.additions or f.deletions:
                diff_display = f"+{f.additions} -{f.deletions}"
                diff_style = "green" if f.additions >= f.deletions else "red"
            else:
                diff_display = "     "
                diff_style = ""
            file_views.append(CommitFileView(
                display_path=short_name,
                full_path=f.path,
                diff_display=f"{diff_display:>10}",
                diff_style=diff_style,
            ))

        views.append(CommitView(
            short_hash=commit.short_hash,
            subject=commit.subject,
            worktree=commit.worktree,
            age_style=_age_color(commit.timestamp, now),
            age_display=age_display,
            files=file_views,
        ))
    return views
