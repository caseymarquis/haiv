"""mg become {mind} - Load a mind's context.

Outputs files for Claude to read. Requires MG_MIND to match or be unset.
If MG_MIND is unset, prints bootstrap instructions.
"""

import os

from mg import cmd, env
from mg.errors import CommandError

from mg_core.helpers.minds import Mind


def define() -> cmd.Def:
    return cmd.Def(
        description="Load a mind's context",
    )


def execute(ctx: cmd.Ctx) -> None:
    mind: Mind = ctx.args.get_one("mind")
    current_mind = os.environ.get(env.MG_MIND)

    # If already a different mind, error - can't switch identities
    if current_mind and current_mind != mind.name:
        raise CommandError(
            f"Already running as '{current_mind}'. "
            f"Cannot become '{mind.name}' - start a new session instead."
        )

    # If MG_MIND not set, print bootstrap instructions
    if not current_mind:
        ctx.print("MG_MIND is not set.")
        ctx.print("")
        ctx.print("To become this mind, set the environment variable and run again:")
        ctx.print(f"  export MG_MIND={mind.name}")
        ctx.print(f"  mg become {mind.name}")
        return

    # MG_MIND matches - output files to read (works for initial load or post-compaction)
    _output_startup_files(ctx, mind)


def _output_startup_files(ctx: cmd.Ctx, mind: Mind) -> None:
    """Output the list of files for the mind to read."""
    files_to_read: list[str] = []

    # Add paths from references.toml (relative to mg root)
    files_to_read.extend(mind.get_references())

    # Add startup files (convert to relative paths)
    for file in mind.get_startup_files():
        rel_path = file.relative_to(ctx.paths.root)
        files_to_read.append(str(rel_path))

    if not files_to_read:
        ctx.print(f"Mind '{mind.name}' has no startup files.")
        return

    ctx.print("Read the following files in their entirety:")
    for path in files_to_read:
        ctx.print(f"- {path}")
