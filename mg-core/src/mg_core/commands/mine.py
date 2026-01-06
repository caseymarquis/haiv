"""mg mine - Display information about the current mind.

Shows the mind name, location, startup context path, and role (if configured).
Requires MG_MIND environment variable to be set.
"""

from __future__ import annotations

import os

from mg import cmd
from mg.errors import CommandError

from mg_core.helpers.minds import resolve_mind


def define() -> cmd.Def:
    return cmd.Def(description="Display information about the current mind")


def execute(ctx: cmd.Ctx) -> None:
    mind_name = os.environ.get("MG_MIND")

    if not mind_name:
        raise CommandError(
            "MG_MIND environment variable not set. "
            "Run 'mg start {mind}' to launch a mind first."
        )

    # Resolve the mind
    mind = resolve_mind(mind_name, ctx.paths.minds)

    # Output mind info
    ctx.print(f"Mind: {mind.name}")
    ctx.print(f"Location: {mind.paths.root}")
    ctx.print(f"Startup: {mind.paths.startup}")

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
