"""hv start - Start the haiv TUI for this project."""

from haiv import cmd


def define() -> cmd.Def:
    return cmd.Def(
        description="Start the haiv TUI for this project",
    )


def execute(ctx: cmd.Ctx) -> None:
    ctx.tui.start()
