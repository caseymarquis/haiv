"""Simple command - no params, no flags."""

from haiv import cmd


def define() -> cmd.Def:
    return cmd.Def(description="A simple command")


def execute(ctx: cmd.Ctx) -> None:
    ctx.print("simple executed")
