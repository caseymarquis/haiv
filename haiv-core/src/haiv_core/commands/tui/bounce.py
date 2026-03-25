"""hv tui bounce - Cycle to the next bounce-eligible session."""

from haiv import cmd


def define() -> cmd.Def:
    return cmd.Def(
        description="Cycle to the next bounce-eligible session",
    )


def execute(ctx: cmd.Ctx) -> None:
    # TODO: ctx.tui.send_command(TuiCommand.BOUNCE) — waiting on command queue from Luna
    ctx.print("Not yet wired — waiting on TUI command queue.")
