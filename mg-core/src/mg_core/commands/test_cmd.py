"""Simple test command for verifying CLI routing."""

from mg import cmd


def define() -> cmd.Def:
    return cmd.Def(description="Test command that prints a greeting")


def execute(ctx: cmd.Ctx) -> None:
    print("Hello from mg_core!")
