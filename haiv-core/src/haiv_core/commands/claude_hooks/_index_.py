"""hv claude_hooks - List recent Claude Code hook events."""

from __future__ import annotations

from datetime import datetime

from haiv import cmd
from haiv.helpers.tui.TuiModel import ClaudeHookEntry, SessionEntry


def define() -> cmd.Def:
    return cmd.Def(
        description="Show recent Claude Code hook events",
    )


def execute(ctx: cmd.Ctx) -> None:
    from haiv.helpers.tui.TuiClient import TuiClient

    client = TuiClient(ctx.paths.root.name)

    try:
        model = client.read()
    except ConnectionError:
        print("TUI is not running.")
        return

    section = model.claude_hook_events
    if not section or not section.events:
        print("No hook events yet.")
        return

    sessions = model.sessions.entries if model.sessions else []
    session_map = _build_session_map(sessions)

    for event in section.events:
        mind = session_map.get(event.session_id, event.session_id[:8] if event.session_id else "?")
        ts = datetime.fromtimestamp(event.ts).strftime("%H:%M:%S")
        summary = _summarize(event)
        print(f"  {event.id:>3}  {ts}  {mind:<12}  {event.hook:<20}  {summary}")


def _build_session_map(sessions: list[SessionEntry]) -> dict[str, str]:
    """Map session IDs to mind names."""
    return {s.id: s.mind for s in sessions}


def _summarize(event: ClaudeHookEntry) -> str:
    """Extract a short summary from the event payload."""
    p = event.payload

    if event.hook == "UserPromptSubmit":
        prompt = p.get("prompt", "")
        if len(prompt) > 50:
            return prompt[:47] + "..."
        return prompt

    if event.hook == "Notification":
        msg = p.get("message", "")
        ntype = p.get("notification_type", "")
        return f"[{ntype}] {msg}" if ntype else msg

    if event.hook == "Stop":
        msg = p.get("last_assistant_message", "")
        if len(msg) > 50:
            return msg[:47] + "..."
        return msg

    return ""
