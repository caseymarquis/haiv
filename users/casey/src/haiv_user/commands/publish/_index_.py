"""hv publish - List publishable packages."""

from haiv import cmd


def define() -> cmd.Def:
    return cmd.Def(description="List publishable packages")


def execute(ctx: cmd.Ctx) -> None:
    ctx.print("Publishable packages:\n")
    ctx.print("  hv publish haiv-lib")
    ctx.print("  hv publish haiv-core")
    ctx.print("  hv publish haiv-cli")
    ctx.print("  hv publish haiv-tui")
    ctx.print("  hv publish haiv")
    ctx.print()
    ctx.print("Use --dry-run to build without publishing.")
