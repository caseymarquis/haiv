"""Index command - directory default."""

from haiv import cmd


def define() -> cmd.Def:
    return cmd.Def(description="Tools index command")


def execute(ctx: cmd.Ctx) -> None:
    ctx.print("tools index executed")
