"""Command execution for mg.

Handles the command lifecycle: setup → execute → teardown.
"""

from mg import cmd
from mg.loader import Command


def run_command(command: Command, ctx: cmd.Ctx) -> None:
    """Execute a command through its full lifecycle.

    Args:
        command: The loaded command to execute
        ctx: Context with args and container
    """
    command.setup(ctx)
    try:
        command.execute(ctx)
    finally:
        command.teardown(ctx)
