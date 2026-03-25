"""hv tui restart - Restart the TUI process."""

from haiv import cmd


def define() -> cmd.Def:
    return cmd.Def(
        description="Restart the TUI process",
    )


def execute(ctx: cmd.Ctx) -> None:
    # TODO: ctx.tui.send_command(TuiCommand.RESTART) — waiting on command queue from Luna
    ctx.print("Not yet wired — waiting on TUI command queue.")
