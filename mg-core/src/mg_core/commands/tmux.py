"""Attach to the haiv tmux session.

Creates the session if it doesn't exist, then attaches to it.
This command is for humans running from a regular terminal - it will
error if called from within Claude Code or an existing tmux session.
"""

from haiv import cmd
from haiv.wrappers.tmux import Tmux


def define() -> cmd.Def:
    """Define the tmux command."""
    return cmd.Def(
        description="Attach to the haiv tmux session (creates if needed)",
    )


def execute(ctx: cmd.Ctx) -> None:
    """Execute the tmux command."""
    tmux = Tmux(hv_root=ctx.paths.root)
    tmux.attach()
