"""Venv resolution for cross-package command execution.

When a command file lives in an external package with its own venv,
the CLI needs to detect this and re-launch with the correct venv.

The VenvResolver protocol abstracts the detection. Given a command
file path, it determines which project (and therefore which venv)
should execute that command.

The re-launch uses `uv run --project <path>` to enter the correct
venv. The re-launched process re-routes from scratch — no state
crosses the boundary.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class VenvMatch:
    """Result of venv resolution.

    project_root: Path to the project directory containing pyproject.toml
    """

    project_root: Path


@runtime_checkable
class VenvResolver(Protocol):
    """Determines which venv a command file should run in."""

    def resolve(self, command_file: Path) -> VenvMatch | None:
        """Given a command file, return the project it belongs to.

        Returns None if the command should run in the current venv.
        Returns VenvMatch if a different venv is needed.
        """
        ...


class PyprojectVenvResolver:
    """Default resolver: walks up from command file looking for pyproject.toml.

    Compares the found project's venv against the currently active venv.
    If they differ, returns a VenvMatch pointing to the project.
    """

    def resolve(self, command_file: Path) -> VenvMatch | None:
        project_root = _find_project_root(command_file)
        if project_root is None:
            return None

        project_venv = project_root / ".venv"
        if not project_venv.is_dir():
            return None

        if _is_current_venv(project_venv):
            return None

        return VenvMatch(project_root=project_root)


def _find_project_root(path: Path) -> Path | None:
    """Walk up from path looking for a pyproject.toml with a .venv sibling."""
    current = path.parent if path.is_file() else path
    while current != current.parent:
        if (current / "pyproject.toml").is_file() and (current / ".venv").is_dir():
            return current
        current = current.parent
    return None


def _is_current_venv(venv_path: Path) -> bool:
    """Check if the given venv is the one we're currently running in."""
    try:
        current_prefix = Path(sys.prefix).resolve()
        target = venv_path.resolve()
        return current_prefix == target
    except (OSError, ValueError):
        return False
