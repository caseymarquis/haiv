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

import sys
from collections import deque
from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.widgets import Header, Footer, TabbedContent, TabPane, Tabs

from haiv._infrastructure.TuiServer import RESTART_EXIT_CODE, TuiLocalClient, TuiServer
from haiv.helpers.tui import helpers
from haiv.helpers.tui.terminal import TUI_PANE_TITLE
from haiv.helpers.utils.file_watcher import FileWatcher
from haiv.wrappers.git import Git
from haiv_tui.command_dispatcher import CommandDispatcher
from haiv_tui.init import HaivDeps
from haiv_tui.store import TuiStore
from haiv_tui.bounce_worker import BounceWorker
from haiv_tui.claude_hooks_worker import ClaudeHooksWorker
from haiv_tui.widgets.claude_hooks import ClaudeHooksWidget
from haiv_tui.widgets.errors import ErrorsWidget
from haiv_tui.widgets.hud import HudWidget
from haiv_tui.widgets.markdown_file import MarkdownFileWidget
from haiv_tui.widgets.sessions import SessionsWidget

MAX_INTERNAL_ERRORS = 5
POLL_INTERVAL = 0.1


class HaivApp(App):
    """haiv terminal UI."""

    CSS = """
    Screen {
        overflow: hidden;
    }
    #session-panel {
        height: 13fr;
        border-bottom: solid $surface-lighten-2;
    }
    #tabs-panel {
        height: 7fr;
    }
    TabbedContent {
        height: 1fr;
    }
    TabbedContent Tabs {
        dock: bottom;
    }
    ErrorsWidget {
        height: auto;
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

    def __init__(
        self,
        *,
        deps: HaivDeps,
        server: TuiServer,
        client: TuiLocalClient,
    ) -> None:
        super().__init__()
        self.internal_errors: deque[str] = deque(maxlen=MAX_INTERNAL_ERRORS)
        self.paths = deps.paths
        self.settings = deps.settings
        self.terminal = deps.terminal
        self.git = Git(deps.paths.root, quiet=True) if deps.paths else None
        self.store = TuiStore(error_sink=self.internal_errors.append)
        self._server = server
        self.tui_client = client
        self._claude_hooks = ClaudeHooksWorker(client)
        self._bounce = BounceWorker(
            client=client,
            terminal=deps.terminal,
            sessions_file=deps.paths.user.sessions_file if deps.paths else Path("/dev/null"),
            haiv_root=deps.paths.root if deps.paths else Path("/dev/null"),
            git=self.git,
        )
        self._dispatcher = CommandDispatcher(
            on_restart=lambda _: self.action_restart(),
            on_bounce=lambda _: self._bounce.handle(),
            on_claude_hook_event=lambda req: self._claude_hooks.handle(req),
            error_sink=self.internal_errors.append,
        )
        self._bg_workers: _Workers | None = None

    def on_mount(self) -> None:
        """Start the TUI server and load initial state."""
        # Set the WezTerm pane title so `hv start` can detect whether the
        # TUI process is alive. See TUI_PANE_TITLE for the full story.
        sys.stdout.write(f"\033]2;{TUI_PANE_TITLE}\007")
        sys.stdout.flush()

        self._server.start()
        if self.settings.keybindings:
            self.set_keymap(self.settings.keybindings)

        if self.paths is not None:
            helpers.sessions_refresh(self.tui_client, self.paths.user.sessions_file, git=self.git)
            if self.terminal is not None:
                mind = self.terminal.get_active_mind_name()
                if mind:
                    helpers.active_mind_set(self.tui_client, mind)
            self._bg_workers = _Workers(self.paths, self.tui_client, self.git)
            self._bg_workers.start()
            self._bg_workers.register_with(self._dispatcher)

        # Immediate first read, then start polling
        self._poll_model()
        self.set_interval(POLL_INTERVAL, self._poll_model)

    def _poll_model(self) -> None:
        """Drain dirty sections and commands from the server."""
        # Commands — independent of model updates
        commands = self._server.drain_commands()
        if commands:
            try:
                self._dispatcher.dispatch(commands)
            except Exception as e:
                self.internal_errors.append(f"command: {e}")

        # Model updates — dirty tracking + store signals
        dirty = self._server.drain_dirty()
        if not dirty:
            if commands:
                self._update_errors()
            return

        try:
            snapshot = self.tui_client.read()
            self.store.update(snapshot, dirty)
        except Exception as e:
            self.internal_errors.append(f"poll: {e}")

        self._update_errors()

    def _update_errors(self) -> None:
        """Push internal errors to the errors widget."""
        try:
            self.query_one(ErrorsWidget).render_errors(list(self.internal_errors))
        except Exception:
            pass

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="session-panel"):
            yield HudWidget(
                store=self.store,
                worktrees_dir=self.paths.worktrees_dir if self.paths else None,
                settings=self.settings,
                errors=self.internal_errors,
                id="hud",
            )
        with Vertical(id="tabs-panel"):
            with TabbedContent(initial="sessions"):
                with TabPane("Sessions", id="sessions"):
                    yield SessionsWidget(
                        store=self.store,
                        terminal=self.terminal,
                        tui_client=self.tui_client,
                        sessions_file=self.paths.user.sessions_file if self.paths else Path("/dev/null"),
                        haiv_root=self.paths.root if self.paths else Path("/dev/null"),
                        settings=self.settings,
                        errors=self.internal_errors,
                        id="session-tree",
                    )
                with TabPane("Hooks", id="hooks"):
                    yield ClaudeHooksWidget(store=self.store, id="claude-hooks")
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
        """Stop the TUI server and workers. Called after app.run() returns."""
        self._server.stop()
        if self._bg_workers is not None:
            self._bg_workers.stop()


# ---------------------------------------------------------------------------
# Background workers
# ---------------------------------------------------------------------------


class _Workers:
    """Background threads that gather data and push it into the TUI model."""

    def __init__(self, paths, client: TuiLocalClient, git: Git | None) -> None:
        self._paths = paths
        self._client = client
        self._git = git
        self._file_watcher: FileWatcher | None = None
        self._recent_files: RecentFilesWorker | None = None
        self._recent_commits: RecentCommitsWorker | None = None

    def start(self) -> None:
        from haiv_tui.recent_commits_worker import RecentCommitsWorker
        from haiv_tui.recent_files_worker import RecentFilesWorker

        # Watch sessions file for external edits
        sessions_file = self._paths.user.sessions_file
        sessions_file.parent.mkdir(parents=True, exist_ok=True)

        def _refresh_sessions(changed_paths: list[Path]) -> None:
            helpers.sessions_refresh(self._client, sessions_file, git=self._git)

        self._file_watcher = (
            FileWatcher(_refresh_sessions)
            .watch_file(sessions_file)
            .start()
        )

        # Recent files gatherer
        self._recent_files = RecentFilesWorker(
            client=self._client,
            worktrees_dir=self._paths.worktrees_dir,
        ).start()

        # Recent commits gatherer
        self._recent_commits = RecentCommitsWorker(
            client=self._client,
            worktrees_dir=self._paths.worktrees_dir,
        ).start()

    def register_with(self, dispatcher: CommandDispatcher) -> None:
        """Let workers register themselves as command listeners."""
        if self._recent_files is not None:
            self._recent_files.register_with(dispatcher)
        if self._recent_commits is not None:
            self._recent_commits.register_with(dispatcher)

    def stop(self) -> None:
        if self._file_watcher is not None:
            self._file_watcher.stop()
        if self._recent_files is not None:
            self._recent_files.stop()
        if self._recent_commits is not None:
            self._recent_commits.stop()
