"""mg: Seamless management of a collaborative AI team."""

import os
import sys
import traceback
from pathlib import Path

from mg import env
from mg.paths import get_mg_root

__version__ = "0.1.0"


def _log_exception(exc: Exception) -> Path | None:
    """Log exception to XDG_STATE_HOME/mg/logs/. Returns log path or None on failure."""
    from datetime import datetime

    try:
        state_home = os.environ.get("XDG_STATE_HOME", os.path.expanduser("~/.local/state"))
        log_dir = Path(state_home) / "mg" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        log_file = log_dir / f"error-{timestamp}.log"
        with open(log_file, "w") as f:
            f.write(traceback.format_exc())
        return log_file
    except Exception:
        return None


def _handle_error(exc: Exception) -> None:
    """Handle an exception: print message, log traceback, exit."""
    from mg.errors import CommandError

    log_path = _log_exception(exc)

    if isinstance(exc, CommandError):
        print(f"---\n{exc}", file=sys.stderr)
    else:
        print(f"---\nAn unexpected error occurred: {exc}", file=sys.stderr)

    if log_path:
        print(f"\n---\nDetails: {log_path}", file=sys.stderr)
    else:
        traceback.print_exc()

    sys.exit(1)


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

    try:
        mg_root = get_mg_root(cwd=Path.cwd())
        os.environ[env.MG_ROOT] = str(mg_root)

        command = load_command(route.file)
        ctx = build_ctx(route, command, mg_root=mg_root)
        run_command(command, ctx)
    except Exception as exc:
        _handle_error(exc)


if __name__ == "__main__":
    main()
