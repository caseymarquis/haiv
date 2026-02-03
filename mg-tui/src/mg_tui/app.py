"""mg-tui: Terminal UI for mind-games.

Owns the TuiServer lifecycle. On mount, starts the server and a poll
loop that reads model snapshots and pushes them through the TuiStore
for per-section signal dispatch. The poll model avoids cross-thread
callbacks — the Textual thread pulls state, the model thread never
calls back into Textual.
"""

from __future__ import annotations

from collections import deque

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Header, Footer, Static

from mg._infrastructure.TuiServer import RESTART_EXIT_CODE, TuiLocalClient, TuiServer
from mg.helpers.tui import helpers
from mg.paths import Paths

from mg_tui.store import TuiStore
from mg_tui.widgets.hud import HudWidget
from mg_tui.widgets.sessions import SessionsWidget

MAX_INTERNAL_ERRORS = 5
POLL_INTERVAL = 0.1


class MindGamesApp(App):
    """Mind-games terminal UI."""

    CSS = """
    #sidebar {
        width: 30;
        border: solid green;
    }
    #main {
        border: solid blue;
    }
    #terminal-area {
        height: 1fr;
        border: solid white;
    }
    """

    BINDINGS = [
        ("ctrl+q", "quit", "Quit"),
        ("ctrl+r", "restart", "Restart"),
        ("t", "toggle_sidebar", "Toggle Sidebar"),
    ]

    def __init__(self, project: str, paths: Paths | None = None) -> None:
        super().__init__()
        self.project = project
        self.paths = paths
        self.internal_errors: deque[str] = deque(maxlen=MAX_INTERNAL_ERRORS)
        self.store = TuiStore(error_sink=self.internal_errors.append)
        self._server = TuiServer(project)
        self.tui_client = TuiLocalClient(self._server.submit)

    def on_mount(self) -> None:
        """Start the TUI server and load initial state."""
        self._server.start()

        if self.paths is None:
            helpers.errors_append(self.tui_client, "No user identity found. Run 'mg users new --name <name>'.")
        else:
            helpers.sessions_refresh(self.tui_client, self.paths.user.sessions_file)

        # Immediate first read, then start polling
        self._poll_model()
        self.set_interval(POLL_INTERVAL, self._poll_model)

    def _poll_model(self) -> None:
        """Read model snapshot and push through store for dispatch."""
        try:
            snapshot = self.tui_client.read()
            self.store.update(snapshot)
        except Exception as e:
            self.internal_errors.append(f"poll: {e}")

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            with Vertical(id="sidebar"):
                yield SessionsWidget(id="session-tree")
            with Vertical(id="main"):
                yield HudWidget(id="hud")
                yield Static("[Terminal area - to be implemented]", id="terminal-area")
        yield Footer()

    def action_toggle_sidebar(self) -> None:
        sidebar = self.query_one("#sidebar")
        sidebar.display = not sidebar.display

    def action_restart(self) -> None:
        """Exit with restart code — main() handles cleanup and relaunch."""
        self.exit(return_code=RESTART_EXIT_CODE)

    def shutdown(self) -> None:
        """Stop the TUI server. Called after app.run() returns."""
        self._server.stop()
