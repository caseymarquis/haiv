"""TUI state model.

TuiModel holds raw data gathered from external sources. Each section
represents one data source. The TUI reads frozen snapshots; gatherers
push updates via write_raw().

Sections are raw data — no display logic, no TUI-specific assembly.
The TUI assembles display concerns from raw sections at render time.

Publishing (future):
    The TUI will publish derived state (e.g. active mind) for consumption
    by hv commands. Remote clients push raw data in; the TUI decides what
    to publish out.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from haiv.wrappers.git import BranchStats


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


@dataclass
class SessionEntry:
    """A session as loaded from sessions.ig.toml."""

    id: str = ""
    mind: str = ""
    task: str = ""
    short_id: int = 0
    status: str = "started"  # staged / started
    description: str = ""
    parent_id: str = ""
    branch: str = ""
    base_branch: str = ""


# ---------------------------------------------------------------------------
# Raw sections — one per data source
# ---------------------------------------------------------------------------


@dataclass
class SessionsRaw:
    """Sessions loaded from sessions.ig.toml."""

    entries: list[SessionEntry] = field(default_factory=list)


@dataclass
class GitRaw:
    """Git branch stats, keyed by branch name."""

    branches: dict[str, BranchStats] = field(default_factory=dict)


@dataclass
class ActiveMindRaw:
    """Which mind is currently active in the HUD pane.

    Gathered from WezTerm terminal state.
    """

    mind: str = ""


@dataclass
class RecentFileEntry:
    """A recently modified file with optional diff stats."""

    path: str = ""  # relative to worktrees dir
    worktree: str = ""  # branch/worktree name
    mtime: float = 0.0
    additions: int = 0
    deletions: int = 0


@dataclass
class RecentFilesRaw:
    """Recently modified files across all worktrees."""

    files: list[RecentFileEntry] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Top-level model
# ---------------------------------------------------------------------------


@dataclass
class TuiModel:
    """Container of raw data sections.

    Every field is a raw section or None.
    None means "not provided" — the server skips that section on write.

    TuiModel() initializes the authoritative model (all sections present).
    """

    sessions: SessionsRaw | None = field(default_factory=SessionsRaw)
    git: GitRaw | None = field(default_factory=GitRaw)
    active_mind: ActiveMindRaw | None = field(default_factory=ActiveMindRaw)
    recent_files: RecentFilesRaw | None = field(default_factory=RecentFilesRaw)
