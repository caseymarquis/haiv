"""Claude hooks widget — displays recent Claude Code hook events.

Shows a scrolling log of hook events received from Claude Code
sessions. Subscribes to claude_hook_events and sessions signals
to resolve session IDs to mind names.

Architecture:
    DTO + assembly below widget. Assembly is testable without Textual.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Static

from haiv.helpers.tui.TuiModel import ClaudeHookEntry, ClaudeHookEventsRaw, SessionEntry, SessionsRaw

if TYPE_CHECKING:
    from haiv_tui.store import TuiStore


# ---------------------------------------------------------------------------
# Widget
# ---------------------------------------------------------------------------


class ClaudeHooksWidget(VerticalScroll):
    """Scrolling log of Claude Code hook events."""

    DEFAULT_CSS = """
    ClaudeHooksWidget {
        height: 1fr;
    }
    ClaudeHooksWidget .hook-line {
        height: 1;
    }
    """

    def __init__(self, *, store: TuiStore, **kwargs) -> None:
        super().__init__(**kwargs)
        self._store = store
        self._hooks: ClaudeHookEventsRaw | None = None
        self._sessions: SessionsRaw | None = None

    def on_mount(self) -> None:
        self._store.claude_hook_events_changed.connect(self._on_hooks_update)
        self._store.sessions_changed.connect(self._on_sessions_update)

    def compose(self) -> ComposeResult:
        yield Static("No hook events yet.", id="hook-empty")

    def _on_hooks_update(self, section: ClaudeHookEventsRaw) -> None:
        self._hooks = section
        self._rebuild()

    def _on_sessions_update(self, section: SessionsRaw) -> None:
        self._sessions = section
        self._rebuild()

    def _rebuild(self) -> None:
        if self._hooks is None:
            return

        try:
            empty = self.query_one("#hook-empty", Static)
            empty.remove()
        except Exception:
            pass

        self.query(".hook-line").remove()

        entries = self._sessions.entries if self._sessions else []
        rows = build_hook_rows(self._hooks.events, entries)

        for row in rows:
            line = Text.assemble(
                (f"{row.id:>3} ", "dim"),
                (f"{row.ts} ", "dim"),
                (f"{row.mind:<10} ", "bold"),
                (f"{row.label:<10} ", row.style),
                (row.summary, "dim italic" if row.summary else ""),
            )
            self.mount(Static(line, classes="hook-line"))

        self.scroll_end(animate=False)


# ---------------------------------------------------------------------------
# DTO + assembly
# ---------------------------------------------------------------------------


@dataclass
class HookRow:
    """Display-ready hook event."""

    id: int
    ts: str
    mind: str
    label: str
    summary: str
    style: str


def build_hook_rows(
    events: list[ClaudeHookEntry],
    sessions: list[SessionEntry],
) -> list[HookRow]:
    """Assemble hook events into display rows, resolving mind names."""
    session_map = {s.id: s.mind for s in sessions}

    rows = []
    for event in events:
        mind = session_map.get(event.session_id, event.session_id[:8] if event.session_id else "?")
        label, summary, style = _classify(event)
        rows.append(HookRow(
            id=event.id,
            ts=datetime.fromtimestamp(event.ts).strftime("%H:%M:%S"),
            mind=mind,
            label=label,
            summary=summary,
            style=style,
        ))
    return rows


def _classify(event: ClaudeHookEntry) -> tuple[str, str, str]:
    """Classify an event into a display label, summary, and style.

    Returns (label, summary, style).
    """
    p = event.payload

    if event.hook == "UserPromptSubmit":
        prompt = p.get("prompt", "")
        if len(prompt) > 40:
            prompt = prompt[:37] + "..."
        return "prompt", prompt, ""

    if event.hook == "Notification":
        ntype = p.get("notification_type", "")
        msg = p.get("message", "")
        if ntype == "permission_prompt":
            # extract tool name from "Claude needs your permission to use X"
            tool = msg.rsplit("use ", 1)[-1] if "use " in msg else msg
            return "BLOCKED", f"permission: {tool}", "bold red"
        return ntype or "notify", msg, "yellow"

    if event.hook == "Stop":
        msg = p.get("last_assistant_message", "")
        if len(msg) > 40:
            msg = msg[:37] + "..."
        return "done", msg, "green"

    if event.hook == "SessionStart":
        return "start", "", "blue"

    if event.hook == "SessionEnd":
        return "end", "", "dim"

    return event.hook, "", ""
