"""Simple test command for verifying CLI routing."""

from haiv import cmd


def define() -> cmd.Def:
    return cmd.Def(description="Test command that prints a greeting")


def execute(ctx: cmd.Ctx) -> None:
    print("Hello from haiv_core!")
