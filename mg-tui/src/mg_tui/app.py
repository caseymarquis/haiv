"""haiv-tui: Terminal UI for haiv.

Architecture
------------
The TUI and haiv commands share the same helper functions but access them
differently. haiv commands use the Tui class (tui.py) as a thin facade that
holds pre-loaded dependencies. This app does NOT use tui.py. Instead, it
calls helpers.py functions directly, passing only the dependencies each
function needs. This keeps the app decoupled from the command-side
dependency bag.

    haiv commands:  ctx.tui.mind_switch(mind)       # facade assembles deps
    TUI app:      helpers.mind_switch(term, mind)  # app passes deps directly

All domain logic for TUI operations lives in helpers.py as standalone
functions with explicit parameters. If you're adding a new capability,
put it in helpers.py first. The Tui class and this app are both callers.

terminal.py (TerminalManager) encapsulates WezTerm specifics — tab naming
conventions, pane splitting, parking. Helpers may take a TerminalManager as
a dependency but should not leak WezTerm details to their own callers.

Runtime
-------
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

from haiv._infrastructure.TuiServer import RESTART_EXIT_CODE, TuiLocalClient, TuiServer
from haiv.helpers.tui import helpers
from haiv.helpers.utils.file_watcher import FileWatcher
from haiv.wrappers.git import Git
from haiv_tui.init import init as init_hv_deps
from haiv_tui.store import TuiStore
from haiv_tui.widgets.errors import ErrorsWidget
from haiv_tui.widgets.hud import HudWidget
from haiv_tui.widgets.markdown_file import MarkdownFileWidget
from haiv_tui.widgets.sessions import SessionsWidget

MAX_INTERNAL_ERRORS = 5
POLL_INTERVAL = 0.1


class HaivApp(App):
    """haiv terminal UI."""

    CSS = """
    TabbedContent {
        height: 1fr;
    }
    TabbedContent Tabs {
        dock: bottom;
    }
    """

    # Keybinding IDs follow a dotted namespace convention:
    #   app.*        - application lifecycle (quit, restart)
    #   nav.*        - navigation between tabs/views
    #   sessions.*   - session tree actions
    #
    # Users can remap any binding via [keybindings] in haiv.toml:
    #   [keybindings]
    #   "nav.next_tab" = "l,tab"
    #
    # Textual's set_keymap() merges overrides — unlisted bindings keep defaults.
    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit", id="app.quit"),
        Binding("ctrl+r", "restart", "Restart", id="app.restart"),
        Binding("tab", "next_tab", "Next Tab", priority=True, id="nav.next_tab"),
        Binding("shift+tab", "previous_tab", "Previous Tab", priority=True, id="nav.previous_tab"),
    ]

    def __init__(self, project: str) -> None:
        super().__init__()
        self.project = project
        self.internal_errors: deque[str] = deque(maxlen=MAX_INTERNAL_ERRORS)
        deps = init_hv_deps(on_error=self.internal_errors.append)
        self.paths = deps.paths
        self.settings = deps.settings
        self.terminal = deps.terminal
        self.git = Git(deps.paths.root, quiet=True) if deps.paths else None
        self.store = TuiStore(error_sink=self.internal_errors.append)
        self._server = TuiServer(project)
        self.tui_client = TuiLocalClient(self._server.submit)
        self._last_write_counter = -1
        self._file_watcher: FileWatcher | None = None

    def on_mount(self) -> None:
        """Start the TUI server and load initial state."""
        self._server.start()
        if self.settings.keybindings:
            self.set_keymap(self.settings.keybindings)

        if self.paths is not None:
            helpers.sessions_refresh(self.tui_client, self.paths.user.sessions_file, git=self.git)
            self._start_file_watcher()

        # Immediate first read, then start polling
        self._poll_model()
        self.set_interval(POLL_INTERVAL, self._poll_model)

    def _poll_model(self) -> None:
        """Read model snapshot and push through store for dispatch."""
        current_counter = self._server.get_write_counter()
        if current_counter == self._last_write_counter:
            return
        self._last_write_counter = current_counter

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

    def on_tabbed_content_tab_activated(self, event: TabbedContent.TabActivated) -> None:
        """Focus the first focusable child in the newly activated tab."""
        for child in event.pane.query("*"):
            if child.can_focus:
                child.focus()
                return

    def action_restart(self) -> None:
        """Exit with restart code — main() handles cleanup and relaunch."""
        self.exit(return_code=RESTART_EXIT_CODE)

    def shutdown(self) -> None:
        """Stop the TUI server and file watcher. Called after app.run() returns."""
        self._server.stop()
        if self._file_watcher is not None:
            self._file_watcher.stop()

    def _start_file_watcher(self) -> None:
        """Watch sessions file for external changes and refresh the TUI."""
        sessions_file = self.paths.user.sessions_file
        sessions_file.parent.mkdir(parents=True, exist_ok=True)

        def _refresh_sessions_on_worker_thread(changed_paths: list[Path]) -> None:
            helpers.sessions_refresh(self.tui_client, sessions_file, git=self.git)

        self._file_watcher = (
            FileWatcher(_refresh_sessions_on_worker_thread)
            .watch_file(sessions_file)
            .start()
        )
