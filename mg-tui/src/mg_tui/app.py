"""mg-tui: Terminal UI for mind-games.

Owns the TuiServer lifecycle. On mount, starts the server with an
on_change callback that reads a fresh snapshot via TuiLocalClient and
pushes it through the TuiStore for per-section signal dispatch.
"""

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Header, Footer, Static, Tree

from mg._infrastructure.TuiServer import RESTART_EXIT_CODE, TuiLocalClient, TuiServer

from mg_tui.store import TuiStore
from mg_tui.widgets.hud import HudWidget


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

    def __init__(self, project: str) -> None:
        super().__init__()
        self.project = project
        self.store = TuiStore()
        self._server = TuiServer(project, on_change=self._on_server_change)
        self.tui_client = TuiLocalClient(self._server.submit)

    def _on_server_change(self) -> None:
        """Called from the model thread after a successful write.

        Reads a frozen snapshot via the local client and schedules
        a store update on Textual's main thread.
        """
        snapshot = self.tui_client.read()
        self.call_from_thread(self.store.update, snapshot)

    def on_mount(self) -> None:
        """Start the TUI server when the app mounts."""
        self._server.start()
        # Push initial state through the store
        snapshot = self.tui_client.read()
        self.store.update(snapshot)

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            with Vertical(id="sidebar"):
                tree = Tree("Sessions", id="session-tree")
                tree.root.expand()
                yield tree
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
