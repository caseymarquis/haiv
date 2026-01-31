"""mg start - Start the mg TUI for this project."""

from mg import cmd


def define() -> cmd.Def:
    return cmd.Def(
        description="Start the mg TUI for this project",
    )


def execute(ctx: cmd.Ctx) -> None:
    ctx.tui.start()
