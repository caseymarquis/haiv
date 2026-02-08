"""Sessions widget — displays active sessions in a tree with preview.

Full-screen tab content. The tree shows all sessions (eventually nested
for delegation hierarchy). Highlighting a node updates the preview area
below. Pressing Enter switches to the Session tab for that session.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.widgets import Static, TabbedContent, Tree

from mg.helpers.tui import helpers
from mg.helpers.tui.TuiModel import SessionEntry


class SessionPreview(Static):
    """Preview area showing details of the highlighted session."""

    DEFAULT_CSS = """
    SessionPreview {
        height: auto;
        max-height: 8;
        padding: 0 1;
        border-top: solid $surface-lighten-2;
    }
    """

    def render_preview(self, entry: SessionEntry | None) -> None:
        if entry is None:
            self.update("")
            return
        self.update(
            f"Task: {entry.task}\n"
            f"Mind: {entry.mind}\n"
            f"Status: {entry.status or 'none'}\n"
            f"Session: {entry.short_id}"
        )


class SessionsWidget(Vertical):
    """Sessions tab — tree with inline preview."""

    BINDINGS = [
        Binding("j", "cursor_down", "Cursor Down", show=False, id="sessions.cursor_down"),
        Binding("k", "cursor_up", "Cursor Up", show=False, id="sessions.cursor_up"),
    ]

    def action_cursor_down(self) -> None:
        self.query_one(Tree).action_cursor_down()

    def action_cursor_up(self) -> None:
        self.query_one(Tree).action_cursor_up()

    def compose(self) -> ComposeResult:
        yield Tree[SessionEntry]("Sessions", id="sessions-tree")
        yield SessionPreview(id="session-preview")

    def on_mount(self) -> None:
        tree = self.query_one(Tree)
        tree.root.expand()
        store = self.app.store
        store.sessions_changed.connect(self._on_sessions_changed)
        if store.snapshot is not None:
            self._render_sessions(store.snapshot.sessions)

    def _on_sessions_changed(self, sender) -> None:
        """Called by blinker when the sessions section changes."""
        self._render_sessions(sender)

    def _render_sessions(self, sessions) -> None:
        tree = self.query_one(Tree)
        tree.root.remove_children()
        for entry in sessions.entries:
            status = entry.status or "none"
            label = f"[{status}] {entry.task} ({entry.mind})"
            tree.root.add_leaf(label, data=entry)

    def on_tree_node_highlighted(self, event: Tree.NodeHighlighted) -> None:
        """Update preview when cursor moves to a new node."""
        preview = self.query_one(SessionPreview)
        preview.render_preview(event.node.data)

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        """Launch the selected mind and switch to Session tab."""
        entry: SessionEntry | None = event.node.data
        if entry is None:
            return

        app = self.app
        if app.terminal is not None and app.paths is not None:
            try:
                helpers.mind_launch(
                    app.terminal,
                    app.tui_client,
                    app.paths.user.sessions_file,
                    entry.mind,
                    app.paths.root,
                )
            except Exception as e:
                app.internal_errors.append(f"mind_launch: {e}")

        tabbed = app.query_one(TabbedContent)
        tabbed.active = "session"
