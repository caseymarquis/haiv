"""Errors widget — displays internal and model errors.

Shows combined errors from the TUI model (external) and the app's
internal error deque (poll failures, subscriber exceptions). Updated
every poll cycle directly by the app — no signal wiring needed.
"""

from __future__ import annotations

from textual.widgets import Static


class ErrorsWidget(Static):
    """Displays error messages at the bottom of the main panel."""

    DEFAULT_CSS = """
    ErrorsWidget {
        color: $error;
        height: auto;
        max-height: 6;
        padding: 0 1;
    }
    """

    def render_errors(self, messages: list[str]) -> None:
        if not messages:
            self.update("")
            return
        self.update("\n".join(messages))
