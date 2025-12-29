"""Greet command - has a name param."""

from mg import cmd


def define() -> cmd.Def:
    return cmd.Def(description="Greet someone by name")


def execute(ctx: cmd.Ctx) -> None:
    name = ctx.args.get_one("name")
    ctx.print(f"hello {name}")
