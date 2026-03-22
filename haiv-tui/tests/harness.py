"""Shared test harness for widget-level and app-level tests.

Provides a minimal Textual App that mounts a single widget with injected
dependencies, plus factories for mock deps used across test files.
"""

from __future__ import annotations

from collections import deque
from pathlib import Path
from unittest.mock import MagicMock

from textual.app import App, ComposeResult
from textual.widget import Widget

from haiv.helpers.tui.TuiModel import SessionEntry
from haiv.settings import HaivSettings
from haiv_tui.init import HaivDeps
from haiv_tui.store import TuiStore


class WidgetTestApp(App):
    """Bare app that mounts a single widget for testing."""

    def __init__(self, widget: Widget) -> None:
        super().__init__()
        self._widget = widget

    def compose(self) -> ComposeResult:
        yield self._widget


def make_store() -> TuiStore:
    return TuiStore()


def make_entry(
    mind: str,
    *,
    id: str = "1",
    task: str = "do stuff",
    branch: str = "main",
    short_id: int = 1,
    parent_id: str = "",
    status: str = "started",
    description: str = "",
) -> SessionEntry:
    return SessionEntry(
        id=id, mind=mind, task=task, branch=branch,
        short_id=short_id, parent_id=parent_id,
        status=status, description=description,
    )


def make_sessions_deps(store: TuiStore | None = None) -> dict:
    """Keyword args for SessionsWidget constructor."""
    return dict(
        store=store or make_store(),
        terminal=MagicMock(),
        tui_client=MagicMock(),
        sessions_file=Path("/tmp/fake-sessions.ig.toml"),
        haiv_root=Path("/tmp/fake-root"),
        settings=HaivSettings(),
        errors=deque(maxlen=5),
    )


def make_haiv_deps(tmp_path: Path | None = None) -> HaivDeps:
    """Mock HaivDeps — no filesystem or WezTerm access."""
    return HaivDeps(
        paths=None,
        settings=HaivSettings(),
        terminal=None,
    )


def make_mock_server() -> MagicMock:
    """Mock TuiServer — no threads, no sockets."""
    server = MagicMock()
    server.drain_dirty.return_value = frozenset()
    return server


def make_mock_client() -> MagicMock:
    """Mock TuiLocalClient."""
    return MagicMock()
