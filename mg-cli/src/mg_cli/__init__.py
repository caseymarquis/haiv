"""mg: Seamless management of a collaborative AI team."""

import sys
from pathlib import Path

__version__ = "0.1.0"


def main():
    """Entry point for mg CLI.

    TODO: This is a bootstrap implementation that only uses mg_core commands.
    The real implementation needs to discover and merge commands from multiple
    sources. Load order (later takes precedence over earlier):

    1. Core package (mg_core)
    2. Installed project packages (via entry points)
    3. Project package (mg-state/src/mg_project)
    4. Installed user packages (via entry points)
    5. User package (mg-state/users/{user}/src/mg_user)
    """
    from mg_core import commands
    from mg.routing import find_route
    from mg.loader import load_command
    from mg.args import build_ctx
    from mg.runner import run_command

    prog = Path(sys.argv[0]).name
    args = sys.argv[1:]

    if not args:
        print(f"{prog} v{__version__}")
        print(f"Usage: {prog} <command> [args...]")
        return

    command_string = " ".join(args)

    route = find_route(command_string, commands)
    if route is None:
        print(f"Unknown command: {command_string}")
        sys.exit(1)

    command = load_command(route.file)
    ctx = build_ctx(route, command)
    run_command(command, ctx)


if __name__ == "__main__":
    main()
