"""hv become {mind} - Load a mind's context.

Outputs files for Claude to read. Requires HV_MIND to match or be unset.
If HV_MIND is unset, prints bootstrap instructions.
"""

import os

from haiv import cmd
from haiv._infrastructure import env
from haiv.errors import CommandError

from haiv.helpers.minds import Mind


def define() -> cmd.Def:
    return cmd.Def(
        description="Load a mind's context",
    )


def execute(ctx: cmd.Ctx) -> None:
    mind = ctx.args.get_one("mind", type=Mind)
    current_mind = os.environ.get(env.HV_MIND)

    # If already a different mind, error - can't switch identities
    if current_mind and current_mind != mind.name:
        raise CommandError(
            f"Already running as '{current_mind}'. "
            f"Cannot become '{mind.name}' - start a new session instead."
        )

    # If HV_MIND not set, print bootstrap instructions
    if not current_mind:
        ctx.print("HV_MIND is not set.")
        ctx.print("")
        ctx.print("To become this mind, set the environment variable and run again:")
        ctx.print(f"  export HV_MIND={mind.name}")
        ctx.print(f"  hv become {mind.name}")
        return

    # HV_MIND matches - output files to read (works for initial load or post-compaction)
    _output_startup_files(ctx, mind)


def _output_startup_files(ctx: cmd.Ctx, mind: Mind) -> None:
    """Output the list of files for the mind to read."""
    # get_startup_files() returns all files: references + work/ + home/
    startup_files = mind.get_startup_files()

    # Welcome message
    ctx.print(f"Welcome back, {mind.name}!")
    ctx.print("")

    if not startup_files:
        ctx.print("You have no startup documents yet. Ask what you should work on.")
        return

    ctx.print("Here are the documents you left for yourself.")
    ctx.print("Please read them in their entirety before continuing your work:")
    ctx.print("")
    for file in startup_files:
        rel_path = file.relative_to(ctx.paths.root)
        ctx.print(f"- {rel_path}")
