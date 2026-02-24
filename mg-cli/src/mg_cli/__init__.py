"""mg: Seamless management of a collaborative AI team."""

import os
import shlex
import sys
import traceback
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import cast

import mg_core
import mg_core.commands

from mg._infrastructure import env
from mg.paths import get_mg_root, Paths
from mg._infrastructure.routing import find_route, RouteMatch
from mg._infrastructure.loader import load_command, load_commands_module
from mg._infrastructure.args import build_ctx
from mg._infrastructure.runner import run_command
from mg._infrastructure.identity import detect_user, Identity
from mg._infrastructure.resolvers import make_resolver
from mg._infrastructure.mg_hooks import configure_mg_hooks
from mg.util import module_to_folder

__version__ = "0.1.0"

# Core package root (computed once at import)
_core_root = module_to_folder(mg_core)

# Cached mg_root lookup
_mg_root: Path | None = None
_mg_root_error: Exception | None = None

# Cached user detection
_user: Identity | None = None
_user_error: Exception | None = None


def _get_mg_root_cached() -> Path:
    """Get mg_root, caching the result (success or failure)."""
    global _mg_root, _mg_root_error

    if _mg_root is None and _mg_root_error is None:
        try:
            _mg_root = get_mg_root(cwd=Path.cwd())
        except Exception as e:
            _mg_root_error = e

    if _mg_root_error is not None:
        raise _mg_root_error

    return cast(Path, _mg_root)


def _detect_user_cached() -> Identity:
    """Detect user, caching the result (success or failure)."""
    global _user, _user_error

    if _user is None and _user_error is None:
        try:
            mg_root = _get_mg_root_cached()
            paths = Paths(_called_from=None, _pkg_root=None, _mg_root=mg_root, _core_root=_core_root)
            _user = detect_user(paths.users_dir)
            if _user is None:
                raise Exception(
                    "No user identity found.\n"
                    "Run 'mg users new --name <name>' to create one."
                )
        except Exception as e:
            _user_error = e

    if _user_error is not None:
        raise _user_error

    return cast(Identity, _user)


@dataclass
class CommandSource:
    """Tracks a command source and whether it was checked."""

    name: str
    path: str
    checked: bool
    error: str | None = None


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


def _try_source(
    command_string: str,
    name: str,
    path: str,
    get_commands: Callable[[], ModuleType],
) -> tuple[RouteMatch | None, CommandSource]:
    """Try to find a command in a single source.

    Args:
        command_string: The command to find
        name: Source name for error reporting
        path: Source path for error reporting
        get_commands: Callable that returns the commands module

    Returns:
        (route, source) - route is None if not found or source unavailable
    """
    try:
        commands = get_commands()
        route = find_route(command_string, commands)
        return route, CommandSource(name, path, checked=True)
    except Exception as e:
        return None, CommandSource(name, path, checked=False, error=str(e))


def _get_project_commands() -> ModuleType:
    """Load mg_project commands module."""
    mg_root = _get_mg_root_cached()
    os.environ[env.MG_ROOT] = str(mg_root)

    paths = Paths(_called_from=None, _pkg_root=None, _mg_root=mg_root, _core_root=_core_root)
    return load_commands_module(paths.pkgs.project.commands_dir / "__init__.py")


def _get_user_commands() -> ModuleType:
    """Load mg_user commands module."""
    mg_root = _get_mg_root_cached()
    user = _detect_user_cached()

    paths = Paths(_called_from=None, _pkg_root=None, _mg_root=mg_root, _user_name=user.name, _core_root=_core_root)
    return load_commands_module(paths.pkgs.user.commands_dir / "__init__.py")


def _find_command(
    command_string: str,
) -> tuple[RouteMatch | None, Path | None, list[CommandSource]]:
    """Try to find a command across all sources.

    Returns:
        (route, mg_root, sources) - route is None if not found
    """
    sources: list[CommandSource] = []

    # Try mg_user first (highest precedence)
    route, source = _try_source(
        command_string,
        "mg_user",
        "users/{user}/src/mg_user/commands/",
        _get_user_commands,
    )
    sources.append(source)
    if route is not None:
        return route, _mg_root, sources

    # Try mg_project next
    route, source = _try_source(
        command_string,
        "mg_project",
        "src/mg_project/commands/",
        _get_project_commands,
    )
    sources.append(source)
    if route is not None:
        return route, _mg_root, sources

    # Fall back to mg_core (always available)
    route, source = _try_source(
        command_string,
        "mg_core",
        "(installed)",
        lambda: mg_core.commands,
    )
    sources.append(source)

    return route, _mg_root, sources


def _print_not_found(command_string: str, sources: list[CommandSource]) -> None:
    """Print helpful error when command not found."""
    print(f"Unknown command: {command_string}", file=sys.stderr)

    checked = [s for s in sources if s.checked]
    not_checked = [s for s in sources if not s.checked]

    if checked:
        print("\nChecked:", file=sys.stderr)
        for s in checked:
            print(f"  ✓ {s.name} {s.path}", file=sys.stderr)

    if not_checked:
        print("\nCould not check:", file=sys.stderr)
        for s in not_checked:
            print(f"  ✗ {s.name} {s.path}", file=sys.stderr)
            if s.error:
                print(f"    {s.error}", file=sys.stderr)


def main():
    """Entry point for mg CLI.

    Load order (later takes precedence over earlier):
    1. Core package (mg_core) - always available
    2. Project package (mg_project) - if in mg-managed repo
    3. User package (mg_user) - deferred until user identity exists
    """
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

    # MG_PROG allows the wrapper script to pass its name (e.g., when using python -c)
    prog = os.environ.get(env.MG_PROG) or Path(sys.argv[0]).name
    args = sys.argv[1:]

    if not args:
        print(f"{prog} v{__version__}")
        print(f"Usage: {prog} <command> [args...]")
        print(f"Run '{prog} help' for available commands")
        return

    command_string = shlex.join(args)

    route, mg_root, sources = _find_command(command_string)

    if route is None:
        _print_not_found(command_string, sources)
        sys.exit(1)
        raise AssertionError("unreachable")

    if route.file is None:
        raise RuntimeError(
            f"RouteMatch.file is None for '{command_string}'. "
            "This indicates a bug in find_route() - it should return None "
            "instead of a RouteMatch with file=None."
        )

    try:
        command = load_command(route.file)
        mg_username = _user.name if _user else None

        # Build resolver callback from discovered resolvers
        # Order: mg_core, mg_project, mg_user (later overrides earlier)
        pkg_roots: list[Path] = []

        # mg_core
        pkg_roots.append(_core_root)

        # mg_project and mg_user via Paths
        paths = None
        if mg_root is not None:
            paths = Paths(
                _called_from=None,
                _pkg_root=None,
                _mg_root=mg_root,
                _user_name=mg_username,
                _core_root=_core_root,
            )
            if paths.pkgs.project.root.exists():
                pkg_roots.append(paths.pkgs.project.root)
            if mg_username is not None and paths.pkgs.user.root.exists():
                pkg_roots.append(paths.pkgs.user.root)

        resolve = make_resolver(pkg_roots, paths=paths, has_user=mg_username is not None)

        definition = command.define()
        mg_hook_registry = None
        if definition.enable_mg_hooks:
            mg_hook_registry = configure_mg_hooks(pkg_roots)

        ctx = build_ctx(
            route, command,
            mg_root=mg_root,
            mg_username=mg_username,
            resolve=resolve,
            mg_hook_registry=mg_hook_registry,
        )
        run_command(command, ctx)
    except Exception as exc:
        _handle_error(exc)


if __name__ == "__main__":
    main()
