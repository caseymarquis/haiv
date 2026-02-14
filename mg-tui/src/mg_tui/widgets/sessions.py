"""Sessions widget — displays active sessions in a tree with preview.

Full-screen tab content. The tree shows sessions nested by delegation
hierarchy. Highlighting a node updates the preview area below. The launch
action starts the highlighted mind.
"""

from __future__ import annotations

from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.events import Click
from textual.widgets import Static, Tree

from mg.helpers.tui import helpers
from mg.helpers.tui.TuiModel import SessionEntry
from mg.helpers.utils.trees import TreeNode, build_tree


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
        Binding("enter", "launch_session", "Launch", id="sessions.launch", priority=True),
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

    def _get_active_mind(self) -> str | None:
        """Get the active mind name from the terminal, or None."""
        terminal = self.app.terminal
        if terminal is not None:
            return terminal.get_active_mind_name()
        return None

    def _render_sessions(self, sessions) -> None:
        tree = self.query_one(Tree)
        tree.root.remove_children()
        entries = sessions.entries
        by_id = {e.id: e for e in entries}
        pairs = [(e, by_id.get(e.parent_id) if e.parent_id else None) for e in entries]
        roots = build_tree(pairs)
        active_mind = self._get_active_mind()

        def _build_label(entry: SessionEntry) -> Text:
            """Build a Rich Text label with git stats and active mind styling."""
            is_active = entry.mind == active_mind

            base = f"[{entry.short_id}] {entry.mind}: {entry.task}"

            # Git stats suffix (-1 means no data)
            has_stats = entry.changed_files >= 0
            if has_stats:
                parts = [f"↑{entry.ahead}", f"↓{entry.behind}"]
                if entry.changed_files > 0:
                    parts.append(f"~{entry.changed_files}")
                else:
                    parts.append("✓")
                suffix = f"  {' '.join(parts)}"
            else:
                suffix = "  --"

            style = "bold on dark_green" if is_active else ""
            return Text(f"{base}{suffix}", style=style)

        def _add_nodes(parent_tree_node, session_nodes: list[TreeNode[SessionEntry]]) -> None:
            for node in session_nodes:
                entry = node.item
                label = _build_label(entry)
                if node.child_nodes:
                    branch = parent_tree_node.add(label, data=entry)
                    branch.expand()
                    branch.allow_expand = False
                    _add_nodes(branch, node.child_nodes)
                else:
                    parent_tree_node.add_leaf(label, data=entry)

        _add_nodes(tree.root, roots)

    def on_click(self, event: Click) -> None:
        """Double-click launches the highlighted mind."""
        if event.chain >= 2:
            self.action_launch_session()

    def on_tree_node_highlighted(self, event: Tree.NodeHighlighted) -> None:
        """Update preview when cursor moves to a new node."""
        preview = self.query_one(SessionPreview)
        preview.render_preview(event.node.data)

    def action_launch_session(self) -> None:
        """Launch the highlighted mind."""
        tree = self.query_one(Tree)
        node = tree.cursor_node
        if node is None:
            return
        entry: SessionEntry | None = node.data
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
