"""Open directories in external applications (file explorer, editor)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_WINDOWS = sys.platform == "win32"


def _open(command: list[str], path: Path) -> None:
    if _WINDOWS:
        subprocess.Popen(
            [*command, str(path)],
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    else:
        subprocess.Popen(
            [*command, str(path)],
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


def open_in_explorer(path: Path, command: list[str]) -> None:
    """Open a directory in the system file explorer."""
    _open(command, path)


def open_in_editor(path: Path, command: list[str]) -> None:
    """Open a file or directory in an editor."""
    _open(command, path)
