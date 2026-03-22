"""Open directories in external applications (file explorer, editor)."""

from __future__ import annotations

import subprocess
from pathlib import Path


def open_in_explorer(path: Path, command: list[str]) -> None:
    """Open a directory in the system file explorer."""
    subprocess.Popen(
        [*command, str(path)],
        start_new_session=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def open_in_editor(path: Path, command: list[str]) -> None:
    """Open a directory in an editor."""
    subprocess.Popen(
        [*command, str(path)],
        start_new_session=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
