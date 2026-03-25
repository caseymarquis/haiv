"""hv tui restart - Restart the TUI process."""

from haiv import cmd


def define() -> cmd.Def:
    return cmd.Def(
        description="Restart the TUI process",
    )


def execute(ctx: cmd.Ctx) -> None:
    ctx.tui.restart()
