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
