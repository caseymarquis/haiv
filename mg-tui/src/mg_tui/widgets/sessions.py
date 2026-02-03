"""Sessions widget — displays active sessions in a tree.

Subscribes to the store's sessions_changed signal and rebuilds the
tree whenever the SessionsSection changes.
"""

from __future__ import annotations

from textual.widgets import Tree


class SessionsWidget(Tree):
    """Sidebar tree showing active sessions."""

    def __init__(self, **kwargs) -> None:
        super().__init__("Sessions", **kwargs)

    def on_mount(self) -> None:
        self.root.expand()
        store = self.app.store
        store.sessions_changed.connect(self._on_sessions_changed)
        # Render from current snapshot if available
        if store.snapshot is not None:
            self._render_sessions(store.snapshot.sessions)

    def _on_sessions_changed(self, sender) -> None:
        """Called by blinker when the sessions section changes."""
        self._render_sessions(sender)

    def _render_sessions(self, sessions) -> None:
        self.root.remove_children()
        for entry in sessions.entries:
            label = f"{entry.task} ({entry.mind})"
            self.root.add_leaf(label)
