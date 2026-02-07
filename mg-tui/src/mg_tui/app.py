"""mg-tui: Terminal UI for mind-games.

Owns the TuiServer lifecycle. On mount, starts the server and a poll
loop that reads model snapshots and pushes them through the TuiStore
for per-section signal dispatch. The poll model avoids cross-thread
callbacks — the Textual thread pulls state, the model thread never
calls back into Textual.

Layout: full-screen tabbed views. Each tab owns the entire viewport.
Tab/Shift+Tab cycles tabs. The terminal lives in WezTerm — the TUI
is purely a command center.
"""

from __future__ import annotations

from collections import deque
from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Header, Footer, TabbedContent, TabPane, Tabs

from mg._infrastructure.TuiServer import RESTART_EXIT_CODE, TuiLocalClient, TuiServer
from mg.helpers.tui import helpers
from mg.paths import Paths

from mg_tui.store import TuiStore
from mg_tui.widgets.errors import ErrorsWidget
from mg_tui.widgets.hud import HudWidget
from mg_tui.widgets.markdown_file import MarkdownFileWidget
from mg_tui.widgets.sessions import SessionsWidget

MAX_INTERNAL_ERRORS = 5
POLL_INTERVAL = 0.5


class MindGamesApp(App):
    """Mind-games terminal UI."""

    CSS = """
    TabbedContent {
        height: 1fr;
    }
    TabbedContent Tabs {
        dock: bottom;
    }
    """

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit"),
        Binding("ctrl+r", "restart", "Restart"),
        Binding("tab", "next_tab", "Next Tab", priority=True),
        Binding("shift+tab", "previous_tab", "Previous Tab", priority=True),
    ]

    def __init__(self, project: str) -> None:
        super().__init__()
        self.project = project
        self.internal_errors: deque[str] = deque(maxlen=MAX_INTERNAL_ERRORS)
        self.paths = self._resolve_paths()
        self.store = TuiStore(error_sink=self.internal_errors.append)
        self._server = TuiServer(project)
        self.tui_client = TuiLocalClient(self._server.submit)

    def _resolve_paths(self) -> Paths | None:
        """Detect user identity and build Paths, or None with an error."""
        from mg._infrastructure.identity import detect_user
        from mg.paths import get_mg_root

        try:
            mg_root = get_mg_root(Path.cwd())
        except ValueError as e:
            self.internal_errors.append(f"paths: {e}")
            return None

        user = detect_user(mg_root / "users")
        if user is None:
            self.internal_errors.append(
                f"No user identity found (mg_root={mg_root}). "
                "Run 'mg users new --name <name>'."
            )
            return None

        return Paths(_called_from=None, _pkg_root=None, _mg_root=mg_root, _user_name=user.name)

    def on_mount(self) -> None:
        """Start the TUI server and load initial state."""
        self._server.start()

        if self.paths is not None:
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

        self._update_errors()

    def _update_errors(self) -> None:
        """Collect errors from all sources and push to the errors widget."""
        messages = []
        if self.store.snapshot is not None:
            messages.extend(self.store.snapshot.errors.messages)
        messages.extend(self.internal_errors)
        try:
            self.query_one(ErrorsWidget).render_errors(messages)
        except Exception:
            pass

    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent(initial="sessions"):
            with TabPane("Sessions", id="sessions"):
                yield SessionsWidget(id="session-tree")
            with TabPane("Session", id="session"):
                yield HudWidget(id="hud")
            with TabPane("Plans", id="plans"):
                yield self._plans_widget()
        yield ErrorsWidget(id="errors")
        yield Footer()

    def _plans_widget(self) -> MarkdownFileWidget:
        """Build the plans viewer, pointing at the active mind's immediate-plan.md."""
        if self.paths is not None:
            # TODO: resolve active mind dynamically instead of hardcoding
            plans_file = self.paths.user.state_dir / "minds" / "wren" / "work" / "immediate-plan.md"
        else:
            plans_file = Path("/dev/null")
        return MarkdownFileWidget(plans_file, id="plans-viewer")

    def action_next_tab(self) -> None:
        self.query_one(TabbedContent).query_one(Tabs).action_next_tab()

    def action_previous_tab(self) -> None:
        self.query_one(TabbedContent).query_one(Tabs).action_previous_tab()

    def action_restart(self) -> None:
        """Exit with restart code — main() handles cleanup and relaunch."""
        self.exit(return_code=RESTART_EXIT_CODE)

    def shutdown(self) -> None:
        """Stop the TUI server. Called after app.run() returns."""
        self._server.stop()
