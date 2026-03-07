"""haiv: Seamless management of a collaborative AI team."""

import os
import shlex
import sys
import traceback
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import cast

import haiv_core
import haiv_core.commands

from haiv._infrastructure import env
from haiv.paths import get_hv_root, Paths
from haiv._infrastructure.routing import find_route, RouteMatch
from haiv._infrastructure.loader import load_command, load_commands_module
from haiv._infrastructure.args import build_ctx
from haiv._infrastructure.runner import run_command
from haiv._infrastructure.identity import detect_user, Identity
from haiv._infrastructure.resolvers import make_resolver
from haiv._infrastructure.hv_hooks import configure_hv_hooks
from haiv.util import module_to_folder

__version__ = "0.1.0"

# Core package root (computed once at import)
_core_root = module_to_folder(haiv_core)

# Cached hv_root lookup
_hv_root: Path | None = None
_hv_root_error: Exception | None = None

# Cached user detection
_user: Identity | None = None
_user_error: Exception | None = None


def _get_hv_root_cached() -> Path:
    """Get hv_root, caching the result (success or failure)."""
    global _hv_root, _hv_root_error

    if _hv_root is None and _hv_root_error is None:
        try:
            _hv_root = get_hv_root(cwd=Path.cwd())
        except Exception as e:
            _hv_root_error = e

    if _hv_root_error is not None:
        raise _hv_root_error

    return cast(Path, _hv_root)


def _detect_user_cached() -> Identity:
    """Detect user, caching the result (success or failure)."""
    global _user, _user_error

    if _user is None and _user_error is None:
        try:
            hv_root = _get_hv_root_cached()
            paths = Paths(_called_from=None, _pkg_root=None, _hv_root=hv_root, _core_root=_core_root)
            _user = detect_user(paths.users_dir)
            if _user is None:
                raise Exception(
                    "No user identity found.\n"
                    "Run 'hv users new --name <name>' to create one."
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
    """Log exception to XDG_STATE_HOME/haiv/logs/. Returns log path or None on failure."""
    from datetime import datetime

    try:
        state_home = os.environ.get("XDG_STATE_HOME", os.path.expanduser("~/.local/state"))
        log_dir = Path(state_home) / "haiv" / "logs"
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
    from haiv.errors import CommandError

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
    """Load hv_project commands module."""
    hv_root = _get_hv_root_cached()
    os.environ[env.HV_ROOT] = str(hv_root)

    paths = Paths(_called_from=None, _pkg_root=None, _hv_root=hv_root, _core_root=_core_root)
    return load_commands_module(paths.pkgs.project.commands_dir / "__init__.py")


def _get_user_commands() -> ModuleType:
    """Load hv_user commands module."""
    hv_root = _get_hv_root_cached()
    user = _detect_user_cached()

    paths = Paths(_called_from=None, _pkg_root=None, _hv_root=hv_root, _user_name=user.name, _core_root=_core_root)
    return load_commands_module(paths.pkgs.user.commands_dir / "__init__.py")


def _find_command(
    command_string: str,
) -> tuple[RouteMatch | None, Path | None, list[CommandSource]]:
    """Try to find a command across all sources.

    Returns:
        (route, hv_root, sources) - route is None if not found
    """
    sources: list[CommandSource] = []

    # Try hv_user first (highest precedence)
    route, source = _try_source(
        command_string,
        "hv_user",
        "users/{user}/src/hv_user/commands/",
        _get_user_commands,
    )
    sources.append(source)
    if route is not None:
        return route, _hv_root, sources

    # Try hv_project next
    route, source = _try_source(
        command_string,
        "hv_project",
        "src/hv_project/commands/",
        _get_project_commands,
    )
    sources.append(source)
    if route is not None:
        return route, _hv_root, sources

    # Fall back to haiv_core (always available)
    route, source = _try_source(
        command_string,
        "haiv_core",
        "(installed)",
        lambda: haiv_core.commands,
    )
    sources.append(source)

    return route, _hv_root, sources


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
    """Entry point for haiv CLI.

    Load order (later takes precedence over earlier):
    1. Core package (haiv_core) - always available
    2. Project package (hv_project) - if in haiv-managed repo
    3. User package (hv_user) - deferred until user identity exists
    """
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

    # HV_PROG allows the wrapper script to pass its name (e.g., when using python -c)
    prog = os.environ.get(env.HV_PROG) or Path(sys.argv[0]).name
    args = sys.argv[1:]

    if not args:
        print(f"{prog} v{__version__}")
        print(f"Usage: {prog} <command> [args...]")
        print(f"Run '{prog} help' for available commands")
        return

    command_string = shlex.join(args)

    route, hv_root, sources = _find_command(command_string)

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
        hv_username = _user.name if _user else None

        # Build resolver callback from discovered resolvers
        # Order: haiv_core, hv_project, hv_user (later overrides earlier)
        pkg_roots: list[Path] = []

        # haiv_core
        pkg_roots.append(_core_root)

        # hv_project and hv_user via Paths
        paths = None
        if hv_root is not None:
            paths = Paths(
                _called_from=None,
                _pkg_root=None,
                _hv_root=hv_root,
                _user_name=hv_username,
                _core_root=_core_root,
            )
            if paths.pkgs.project.root.exists():
                pkg_roots.append(paths.pkgs.project.root)
            if hv_username is not None and paths.pkgs.user.root.exists():
                pkg_roots.append(paths.pkgs.user.root)

        resolve = make_resolver(pkg_roots, paths=paths, has_user=hv_username is not None)

        definition = command.define()
        hv_hook_registry = None
        if definition.enable_hv_hooks:
            hv_hook_registry = configure_hv_hooks(pkg_roots)

        ctx = build_ctx(
            route, command,
            hv_root=hv_root,
            hv_username=hv_username,
            resolve=resolve,
            hv_hook_registry=hv_hook_registry,
        )
        run_command(command, ctx)
    except Exception as exc:
        _handle_error(exc)


if __name__ == "__main__":
    main()
