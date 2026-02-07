"""TUI state model.

TuiModel is the shared state contract between mg commands (clients) and the
running TUI (server). It is a frozen container of section instances, each
representing a distinct area of TUI state.

Callers never manipulate versions directly — the TuiClient.write() mutator
pattern handles that. read() returns a deep-frozen snapshot.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from mg.helpers.tui._base import TuiModelSection


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


@dataclass
class SessionEntry:
    """A session displayed in the TUI."""

    mind: str = ""
    task: str = ""
    short_id: int = 0
    status: str = "started"  # staged / started


# ---------------------------------------------------------------------------
# Concrete sections
# ---------------------------------------------------------------------------


@dataclass
class HudSection(TuiModelSection):
    """Head-up display: identity and session info."""

    role: str | None = None
    worktree: str | None = None
    summary: str | None = None
    session: str | None = None


@dataclass
class SessionsSection(TuiModelSection):
    """Active sessions for the sidebar tree."""

    entries: list[SessionEntry] = field(default_factory=list)


@dataclass
class ErrorsSection(TuiModelSection):
    """Errors to display in the TUI."""

    messages: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Top-level model
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TuiModel:
    """Container of TUI state sections.

    Frozen at the top level — sections are stable slots. Mutators modify
    section fields, not the section references themselves.

    Every field on TuiModel must be a TuiModelSection subclass.
    """

    hud: HudSection = field(default_factory=HudSection)
    sessions: SessionsSection = field(default_factory=SessionsSection)
    errors: ErrorsSection = field(default_factory=ErrorsSection)
