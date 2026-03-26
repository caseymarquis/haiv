"""hv claude_hooks setup - Guide setup of Claude Code hooks for haiv integration."""

import json
from pathlib import Path

from haiv import cmd


REQUIRED_HOOKS = {
    "Stop": "Detects when a mind finishes responding",
    "Notification": "Detects permission prompts and other blocked states",
    "SessionStart": "Detects when a session begins or resumes",
    "UserPromptSubmit": "Detects when the user sends a message",
    "SessionEnd": "Detects when a session terminates",
}


def _hook_entry(event: str) -> dict:
    return {"matcher": "", "hooks": [{"type": "command", "command": f"hv --claude-hook {event}"}]}


def define() -> cmd.Def:
    return cmd.Def(
        description="Guide setup of Claude Code hooks for haiv integration",
        flags=[
            cmd.Flag("json", type=bool, description="Output only the settings JSON"),
        ],
    )


def execute(ctx: cmd.Ctx) -> None:
    settings_file = ctx.paths.root / ".claude" / "settings.json"

    existing = {}
    if settings_file.exists():
        try:
            existing = json.loads(settings_file.read_text())
        except (json.JSONDecodeError, OSError):
            pass

    existing_hooks = existing.get("hooks", {})

    # Build the full config with all hooks
    hooks = dict(existing_hooks)
    missing = []
    present = []
    for event, description in REQUIRED_HOOKS.items():
        if event in existing_hooks:
            present.append((event, description))
        else:
            missing.append((event, description))
            hooks[event] = [_hook_entry(event)]

    updated = dict(existing)
    updated["hooks"] = hooks

    json_only = ctx.args.has("json")

    if json_only:
        print(json.dumps(updated, indent=2))
        return

    if not missing:
        ctx.print("All Claude Code hooks are configured.\n")
        ctx.print("Configured hooks:")
        for event, description in present:
            ctx.print(f"  {event:<20} {description}")
        return

    ctx.print("Claude Code hooks enable haiv to track mind activity —")
    ctx.print("detecting idle minds, permission prompts, and session lifecycle.\n")

    if present:
        ctx.print("Already configured:")
        for event, description in present:
            ctx.print(f"  {event:<20} {description}")
        ctx.print()

    ctx.print("Missing hooks:")
    for event, description in missing:
        ctx.print(f"  {event:<20} {description}")

    ctx.print(f"\nSettings file: {settings_file}")
    ctx.print()
    ctx.print("Add the following to .claude/settings.json:\n")
    ctx.print(json.dumps(updated, indent=2))
    ctx.print()
    ctx.print("Or run: hv claude_hooks setup --json > .claude/settings.json")
