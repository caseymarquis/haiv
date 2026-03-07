"""hv mine - Display information about the current mind.

Shows the mind name, location, work directory, and role (if configured).
Requires HV_MIND environment variable to be set.
"""

from __future__ import annotations

import os

from haiv import cmd
from haiv.errors import CommandError

from haiv.helpers.minds import resolve_mind


def define() -> cmd.Def:
    return cmd.Def(description="Display information about the current mind")


def execute(ctx: cmd.Ctx) -> None:
    mind_name = os.environ.get("HV_MIND")

    if not mind_name:
        raise CommandError(
            "HV_MIND environment variable not set. "
            "Run 'hv start {mind}' to launch a mind first."
        )

    # Resolve the mind
    mind = resolve_mind(mind_name, ctx.paths.user.minds_dir, ctx.paths.root)

    # Output mind info
    ctx.print(f"Mind: {mind.name}")
    ctx.print(f"Location: {mind.paths.root}")
    ctx.print(f"Work: {mind.paths.work.root}")

    # Check for role in references.toml
    if mind.paths.references_file.exists():
        try:
            import tomllib

            content = mind.paths.references_file.read_text()
            data = tomllib.loads(content)
            role = data.get("role")
            if role:
                ctx.print(f"Role: {role}")
        except Exception:
            pass  # Silently ignore parsing errors for role
