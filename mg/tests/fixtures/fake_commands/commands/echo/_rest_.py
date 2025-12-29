"""Echo command - captures rest params."""

from mg import cmd


def define() -> cmd.Def:
    return cmd.Def(description="Echo all arguments")


def execute(ctx: cmd.Ctx) -> None:
    ctx.print(" ".join(ctx.args.rest))
