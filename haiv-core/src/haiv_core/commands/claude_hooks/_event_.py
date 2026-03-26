"""hv claude_hooks <event> - Show full detail for a Claude Code hook event."""

import json
from datetime import datetime

from haiv import cmd


def define() -> cmd.Def:
    return cmd.Def(
        description="Show full detail for a Claude Code hook event",
    )


def execute(ctx: cmd.Ctx) -> None:
    from haiv.helpers.tui.TuiClient import TuiClient

    raw_id = ctx.args.get_one("event")
    try:
        event_id = int(raw_id)
    except ValueError:
        print(f"Invalid event ID: {raw_id}")
        return

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

    event = next((e for e in section.events if e.id == event_id), None)
    if event is None:
        print(f"No event with ID {event_id}.")
        return

    entry = {
        "id": event.id,
        "ts": datetime.fromtimestamp(event.ts).strftime("%H:%M:%S"),
        "hook": event.hook,
        "session_id": event.session_id,
        **event.payload,
    }
    print(json.dumps(entry, indent=2))
