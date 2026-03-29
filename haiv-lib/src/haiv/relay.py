"""Command relay for cross-venv execution.

When a command lives in a package with its own venv (e.g., haiv_project
or haiv_user), the CLI can't load it in-process — the command's dependencies
aren't available. The relay solves this: the CLI serializes the route data
and subprocesses into the target venv, where this module loads and runs
the command.

The relay function works both as a direct call (same venv) and as a
subprocess entry point (different venv via `uv run --project`).

Entry point: python -m haiv.relay '<json>'
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from haiv._infrastructure.routing import RouteMatch, ParamCapture


def _run(route: RouteMatch, *, haiv_root: Path | None, haiv_username: str | None) -> None:
    """Load and execute a command from a resolved route.

    The command gets whatever resolvers and dependencies are available
    in the current venv.
    """
    from haiv._infrastructure.loader import load_command
    from haiv._infrastructure.args import build_ctx
    from haiv._infrastructure.runner import run_command
    from haiv._infrastructure.resolvers import make_resolver
    from haiv._infrastructure.haiv_hooks import configure_haiv_hooks

    from haiv.paths import Paths

    paths = Paths(
        _called_from=None,
        _pkg_root=route.pkg_root,
        _haiv_root=haiv_root,
        _user_name=haiv_username,
    )

    command = load_command(route.file)
    resolve = make_resolver([route.pkg_root], paths=paths, has_user=haiv_username is not None)

    definition = command.define()
    haiv_hook_registry = None
    if definition.enable_haiv_hooks:
        haiv_hook_registry = configure_haiv_hooks([route.pkg_root])

    ctx = build_ctx(
        route,
        command,
        haiv_root=haiv_root,
        haiv_username=haiv_username,
        resolve=resolve,
        haiv_hook_registry=haiv_hook_registry,
    )
    run_command(command, ctx)


def run_route(
    route: RouteMatch,
    *,
    haiv_root: Path | None = None,
    haiv_username: str | None = None,
) -> None:
    """Execute a command from a route object (in-process)."""
    _run(route, haiv_root=haiv_root, haiv_username=haiv_username)


def subprocess_relay(
    project_root: Path,
    route: RouteMatch,
    *,
    haiv_root: Path | None = None,
    haiv_username: str | None = None,
) -> int:
    """Run a command in another venv via subprocess.

    Returns the subprocess exit code.
    """
    import subprocess

    data = json.dumps(_route_to_dict(route, haiv_root=haiv_root, haiv_username=haiv_username))

    result = subprocess.run(
        ["uv", "run", "--project", str(project_root), "python", "-m", "haiv.relay", data],
    )
    return result.returncode


def _route_to_dict(
    route: RouteMatch,
    *,
    haiv_root: Path | None = None,
    haiv_username: str | None = None,
) -> dict[str, Any]:
    """Serialize route data to a dict for JSON transport."""
    return {
        "file": str(route.file),
        "pkg_root": str(route.pkg_root),
        "params": {
            name: {
                "value": cap.value,
                "resolver": cap.resolver,
                "explicit_resolver": cap.explicit_resolver,
            }
            for name, cap in route.params.items()
        },
        "rest": route.rest,
        "raw_flags": route.raw_flags,
        "haiv_root": str(haiv_root) if haiv_root else None,
        "haiv_username": haiv_username,
    }


def _route_from_dict(data: dict[str, Any]) -> tuple[RouteMatch, Path | None, str | None]:
    """Deserialize route data from a dict."""
    route = RouteMatch(
        file=Path(data["file"]),
        pkg_root=Path(data["pkg_root"]),
        params={
            name: ParamCapture(
                value=cap["value"],
                resolver=cap["resolver"],
                explicit_resolver=cap["explicit_resolver"],
            )
            for name, cap in data["params"].items()
        },
        rest=data["rest"],
        raw_flags=data["raw_flags"],
    )
    haiv_root = Path(data["haiv_root"]) if data.get("haiv_root") else None
    haiv_username = data.get("haiv_username")
    return route, haiv_root, haiv_username


def _define_all(files: list[str]) -> dict[str, Any]:
    """Load definitions for a batch of command files.

    Returns a dict mapping file path to cmd.Def or to an error string.
    """
    from haiv._infrastructure.loader import load_command

    results: dict[str, Any] = {}
    for file_path in files:
        try:
            command = load_command(Path(file_path))
            results[file_path] = command.define()
        except Exception as e:
            results[file_path] = str(e)
    return results


def subprocess_define_all(project_root: Path, files: list[str]) -> dict[str, Any]:
    """Get definitions for commands in another venv via subprocess.

    Returns dict mapping file path to cmd.Def or error string.
    """
    import pickle
    import subprocess

    data = json.dumps({"mode": "define_all", "files": files})

    result = subprocess.run(
        ["uv", "run", "--project", str(project_root), "python", "-m", "haiv.relay", data],
        capture_output=True,
    )
    if result.returncode != 0:
        error = result.stderr.decode().strip() or "subprocess failed"
        return {f: error for f in files}

    return pickle.loads(result.stdout)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m haiv.relay '<json>'", file=sys.stderr)
        sys.exit(1)

    data = json.loads(sys.argv[1])

    if data.get("mode") == "define_all":
        import pickle
        results = _define_all(data["files"])
        sys.stdout.buffer.write(pickle.dumps(results))
    else:
        route, haiv_root, haiv_username = _route_from_dict(data)
        _run(route, haiv_root=haiv_root, haiv_username=haiv_username)
