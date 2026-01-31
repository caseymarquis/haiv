"""mg-tui: Terminal UI for mind-games.

TODO: IPC and State Architecture
=================================

Layers:
  - mg defines TuiModel (dataclass, all fields SomeType | None except version).
  - mg-tui imports mg, instantiates TuiModel, owns the live state.
  - mg commands communicate with the running TUI via IPC.

State model (lives in mg):
  TuiModel is the shared state contract. Fields are typed as T | None.
  The version field is a random integer, managed solely by the TUI.

  Optimistic concurrency for writes:
    1. Caller reads full TuiModel (gets current version N).
    2. Caller modifies fields, leaves version unchanged.
    3. Caller sends updated model back.
    4. TUI checks version: if it matches, non-None fields are applied and
       version is set to a new random int. If it doesn't match, the write
       is rejected (stale state).

  Version is random (not incremented) so callers cannot predict or forge it.
  Later: segregate independent namespaces with their own version counters
  so unrelated updates don't conflict.

IPC (cross-platform):
  multiprocessing.connection (stdlib) — uses Unix domain sockets on Unix,
  Windows named pipes on Windows, same API.

  Pipe address derived from project name:
    Unix:    /tmp/mg-{project}.sock
    Windows: \\\\.\\pipe\\mg-{project}

  Single-instance enforcement: Listener bind fails if a TUI is already
  running for the same project.

  TUI runs a dedicated listener thread (blocking accept is fine — IPC and
  UI are fully separated). Messages placed on a thread-safe queue, UI
  thread consumes via call_from_thread() or polling.
"""

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Header, Footer, Static, Tree


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
    #hud {
        height: 5;
        border: solid yellow;
    }
    #terminal-area {
        height: 1fr;
        border: solid white;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("t", "toggle_sidebar", "Toggle Sidebar"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            with Vertical(id="sidebar"):
                tree = Tree("Minds", id="mind-tree")
                tree.root.expand()
                # Placeholder structure
                initiative = tree.root.add("mg improvements")
                initiative.add_leaf("wren (active)")
                initiative.add_leaf("sage (paused)")
                yield tree
            with Vertical(id="main"):
                yield Static(
                    "Role: COO\n"
                    "Worktree: (none - mg-state)\n"
                    "Summary: Exploring TUI\n"
                    "Session: ...",
                    id="hud",
                )
                yield Static("[Terminal area - to be implemented]", id="terminal-area")
        yield Footer()

    def action_toggle_sidebar(self) -> None:
        sidebar = self.query_one("#sidebar")
        sidebar.display = not sidebar.display
