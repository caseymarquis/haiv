"""HUD widget — displays identity and session info.

Subscribes to the store's hud_changed signal and re-renders whenever
the HudSection changes.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.widgets import Static


class HudWidget(Static):
    """Head-up display showing role, worktree, summary, and session."""

    DEFAULT_CSS = """
    HudWidget {
        height: 5;
        border: solid yellow;
        padding: 0 1;
    }
    """

    def on_mount(self) -> None:
        store = self.app.store
        store.hud_changed.connect(self._on_hud_changed)
        # Render from current snapshot if available
        if store.snapshot is not None:
            self._render_hud(store.snapshot.hud)

    def _on_hud_changed(self, sender) -> None:
        """Called by blinker when the hud section changes."""
        self._render_hud(sender)

    def _render_hud(self, hud) -> None:
        self.update(
            f"Role: {hud.role or '—'}\n"
            f"Worktree: {hud.worktree or '—'}\n"
            f"Summary: {hud.summary or '—'}\n"
            f"Session: {hud.session or '—'}"
        )
