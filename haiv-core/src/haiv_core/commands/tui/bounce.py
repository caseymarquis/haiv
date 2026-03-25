"""hv tui bounce - Cycle to the next bounce-eligible session."""

from haiv import cmd


def define() -> cmd.Def:
    return cmd.Def(
        description="Cycle to the next bounce-eligible session",
    )


def execute(ctx: cmd.Ctx) -> None:
    ctx.tui.bounce()
