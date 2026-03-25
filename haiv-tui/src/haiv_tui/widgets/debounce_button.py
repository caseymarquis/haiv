"""A button that disables itself briefly after being pressed to prevent double-clicks."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Button


class DebounceButton(Widget):
    """Button with configurable debounce — disables briefly after press.

    Uses Textual's built-in ``disabled`` reactive. Setting
    ``widget.disabled = True`` disables the inner button; the debounce
    cooldown also disables it temporarily after a press.
    """

    class Pressed(Message):
        """Posted when the inner button is pressed (after debounce filtering)."""

        def __init__(self, button: DebounceButton) -> None:
            super().__init__()
            self.debounce_button = button

    DEFAULT_CSS = """
    DebounceButton {
        height: auto;
        width: auto;
        layout: vertical;
    }
    """

    def __init__(
        self,
        label: str,
        *,
        debounce_seconds: float = 0.5,
        disabled: bool = False,
        id: str | None = None,
    ) -> None:
        super().__init__(disabled=disabled, id=id)
        self._label = label
        self._debounce_seconds = debounce_seconds
        self._cooling_down = False

    def compose(self) -> ComposeResult:
        yield Button(self._label, id="inner", disabled=self.disabled)

    @property
    def button(self) -> Button:
        return self.query_one("#inner", Button)

    def watch_disabled(self, value: bool) -> None:
        try:
            self.button.disabled = value
        except Exception:
            pass  # compose hasn't run yet

    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        if self._cooling_down:
            return
        self._cooling_down = True
        self.button.disabled = True
        self.set_timer(self._debounce_seconds, self._end_cooldown)
        self.post_message(self.Pressed(self))

    def _end_cooldown(self) -> None:
        self._cooling_down = False
        if not self.disabled:
            self.button.disabled = False
