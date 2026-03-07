"""Thin WezTerm CLI subprocess wrapper with educational output.

By default, prints commands as they run. On failure, provides a prompt
that encourages Claude to analyze and help fix the error.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

from haiv.errors import CommandError


class WezTermError(CommandError):
    """Raised when a WezTerm CLI command fails.

    Attributes:
        stderr: The stderr output from the command.
    """

    def __init__(self, message: str, stderr: str = ""):
        super().__init__(message)
        self.stderr = stderr


@dataclass
class PaneSize:
    """Size information for a WezTerm pane."""

    rows: int
    cols: int
    pixel_width: int
    pixel_height: int
    dpi: int


@dataclass
class Pane:
    """A WezTerm pane as returned by 'wezterm cli list --format json'."""

    window_id: int
    tab_id: int
    pane_id: int
    workspace: str
    size: PaneSize
    title: str
    cwd: str
    cursor_x: int
    cursor_y: int
    cursor_shape: str
    cursor_visibility: str
    left_col: int
    top_row: int
    tab_title: str
    window_title: str
    is_active: bool
    is_zoomed: bool
    tty_name: str

    @classmethod
    def from_json(cls, data: dict) -> Pane:
        """Create a Pane from JSON data returned by wezterm cli list."""
        size_data = data["size"]
        size = PaneSize(
            rows=size_data["rows"],
            cols=size_data["cols"],
            pixel_width=size_data["pixel_width"],
            pixel_height=size_data["pixel_height"],
            dpi=size_data["dpi"],
        )
        return cls(
            window_id=data["window_id"],
            tab_id=data["tab_id"],
            pane_id=data["pane_id"],
            workspace=data["workspace"],
            size=size,
            title=data["title"],
            cwd=data["cwd"],
            cursor_x=data["cursor_x"],
            cursor_y=data["cursor_y"],
            cursor_shape=data["cursor_shape"],
            cursor_visibility=data["cursor_visibility"],
            left_col=data["left_col"],
            top_row=data["top_row"],
            tab_title=data["tab_title"],
            window_title=data["window_title"],
            is_active=data["is_active"],
            is_zoomed=data["is_zoomed"],
            tty_name=data["tty_name"],
        )


class WezTerm:
    """Thin wrapper around WezTerm CLI commands.

    Args:
        command: Base command to invoke WezTerm CLI (e.g., ["wezterm"] or
                 ["flatpak", "run", "org.wezfurlong.wezterm"]).
        quiet: If True, suppress output and Claude prompts.
    """

    def __init__(self, command: list[str], quiet: bool = False):
        self.command = list(command)
        self.quiet = quiet

    def run(self, args: list[str], *, intent: str | None = None) -> str:
        """Run a WezTerm CLI command.

        Args:
            args: Arguments after 'wezterm cli' (e.g., ["list", "--format", "json"]).
            intent: Optional description of what we're trying to accomplish.

        Returns:
            stdout from the command.

        Raises:
            WezTermError: If the command fails.
        """
        full_cmd = self.command + ["cli"] + args
        display_cmd = " ".join(full_cmd)

        if not self.quiet:
            print(f"→ {display_cmd}")

        result = subprocess.run(
            full_cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

        if result.returncode != 0:
            if not self.quiet:
                if result.stderr.strip():
                    print(result.stderr.rstrip())

                if intent:
                    print(f"\nWhile trying to: {intent}")

                print(
                    "\nAnalyze the above error, explain what happened, "
                    "and suggest a fix."
                )

            raise WezTermError(
                f"WezTerm command failed: {display_cmd}",
                stderr=result.stderr,
            )

        return result.stdout

    def run_external(self, args: list[str], *, intent: str | None = None) -> str:
        """Run a WezTerm command outside the CLI context.

        Unlike run(), this does NOT prepend 'cli'. Use this for commands
        like 'wezterm start' that launch a new instance rather than
        controlling an existing one. All other commands should use run(),
        which requires being inside a WezTerm session.

        Args:
            args: Arguments after the base command (e.g., ["start", "--workspace", "x"]).
            intent: Optional description of what we're trying to accomplish.

        Returns:
            stdout from the command.

        Raises:
            WezTermError: If the command fails.
        """
        full_cmd = self.command + args
        display_cmd = " ".join(full_cmd)

        if not self.quiet:
            print(f"→ {display_cmd}")

        result = subprocess.run(
            full_cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

        if result.returncode != 0:
            if not self.quiet:
                if result.stderr.strip():
                    print(result.stderr.rstrip())

                if intent:
                    print(f"\nWhile trying to: {intent}")

                print(
                    "\nAnalyze the above error, explain what happened, "
                    "and suggest a fix."
                )

            raise WezTermError(
                f"WezTerm command failed: {display_cmd}",
                stderr=result.stderr,
            )

        return result.stdout

    def list_panes(self) -> list[Pane]:
        """List all panes across all windows and tabs.

        Returns:
            List of Pane objects.
        """
        output = self.run(
            ["list", "--format", "json"],
            intent="list all panes",
        )
        data = json.loads(output)
        return [Pane.from_json(item) for item in data]

    def spawn(
        self,
        *,
        cwd: str | None = None,
        command: list[str] | None = None,
        window_id: int | None = None,
        new_window: bool = False,
        workspace: str | None = None,
    ) -> int:
        """Spawn a new pane in a window or tab.

        Args:
            cwd: Working directory for the spawned process.
            command: Command to run (default: shell).
            window_id: Target window (default: current window).
            new_window: If True, spawn in a new window.
            workspace: Workspace name for new window (requires new_window=True).

        Returns:
            The pane_id of the newly created pane.
        """
        args = ["spawn"]

        if cwd:
            args.extend(["--cwd", cwd])
        if window_id is not None:
            args.extend(["--window-id", str(window_id)])
        if new_window:
            args.append("--new-window")
        if workspace:
            args.extend(["--workspace", workspace])
        if command:
            args.append("--")
            args.extend(command)

        output = self.run(args, intent="spawn new pane")
        return int(output.strip())

    def split_pane(
        self,
        pane_id: int,
        *,
        direction: str = "right",
        percent: int | None = None,
        cwd: str | None = None,
        move_pane_id: int | None = None,
        command: list[str] | None = None,
    ) -> int:
        """Split a pane.

        Args:
            pane_id: The pane to split.
            direction: Split direction ("left", "right", "top", "bottom").
            percent: Percentage of space for new pane.
            cwd: Working directory for the spawned process.
            move_pane_id: Move existing pane instead of spawning new one.
            command: Command to run (default: shell).

        Returns:
            The pane_id of the newly created pane.
        """
        args = ["split-pane", "--pane-id", str(pane_id), f"--{direction}"]

        if percent is not None:
            args.extend(["--percent", str(percent)])
        if cwd:
            args.extend(["--cwd", cwd])
        if move_pane_id is not None:
            args.extend(["--move-pane-id", str(move_pane_id)])
        if command:
            args.append("--")
            args.extend(command)

        output = self.run(args, intent=f"split pane {pane_id} {direction}")
        return int(output.strip())

    def move_pane_to_new_tab(
        self,
        pane_id: int,
        *,
        window_id: int | None = None,
        new_window: bool = False,
    ) -> None:
        """Move a pane into a new tab.

        Args:
            pane_id: The pane to move.
            window_id: Target window for the new tab.
            new_window: If True, create tab in a new window.
        """
        args = ["move-pane-to-new-tab", "--pane-id", str(pane_id)]

        if window_id is not None:
            args.extend(["--window-id", str(window_id)])
        if new_window:
            args.append("--new-window")

        self.run(args, intent=f"move pane {pane_id} to new tab")

    def send_text(self, pane_id: int, text: str, *, no_paste: bool = False) -> None:
        """Send text to a pane as if pasted.

        Args:
            pane_id: Target pane.
            text: Text to send.
            no_paste: If True, send directly without bracketed paste.
        """
        args = ["send-text", "--pane-id", str(pane_id)]

        if no_paste:
            args.append("--no-paste")
        args.append(text)

        self.run(args, intent=f"send text to pane {pane_id}")

    def get_text(
        self,
        pane_id: int,
        *,
        start_line: int | None = None,
        end_line: int | None = None,
        escapes: bool = False,
    ) -> str:
        """Get text content from a pane.

        Args:
            pane_id: Target pane.
            start_line: Starting line (0 = first visible, negative = scrollback).
            end_line: Ending line.
            escapes: If True, include ANSI escape sequences.

        Returns:
            The pane's text content.
        """
        args = ["get-text", "--pane-id", str(pane_id)]

        if start_line is not None:
            args.extend(["--start-line", str(start_line)])
        if end_line is not None:
            args.extend(["--end-line", str(end_line)])
        if escapes:
            args.append("--escapes")

        return self.run(args, intent=f"get text from pane {pane_id}")

    def set_tab_title(self, title: str, *, pane_id: int | None = None) -> None:
        """Set the title of a tab.

        Args:
            title: New title for the tab.
            pane_id: Pane to identify the tab (default: current pane).
        """
        args = ["set-tab-title"]

        if pane_id is not None:
            args.extend(["--pane-id", str(pane_id)])
        args.append(title)

        self.run(args, intent=f"set tab title to '{title}'")

    def activate_pane(self, pane_id: int) -> None:
        """Activate (focus) a pane.

        Args:
            pane_id: The pane to activate.
        """
        self.run(
            ["activate-pane", "--pane-id", str(pane_id)],
            intent=f"activate pane {pane_id}",
        )

    def kill_pane(self, pane_id: int) -> None:
        """Kill a pane.

        Args:
            pane_id: The pane to kill.
        """
        self.run(
            ["kill-pane", "--pane-id", str(pane_id)],
            intent=f"kill pane {pane_id}",
        )

    def zoom_pane(
        self,
        pane_id: int,
        *,
        zoom: bool = False,
        unzoom: bool = False,
        toggle: bool = False,
    ) -> None:
        """Zoom, unzoom, or toggle zoom state of a pane.

        Args:
            pane_id: The pane to zoom.
            zoom: Zoom the pane.
            unzoom: Unzoom the pane.
            toggle: Toggle zoom state.

        If none of zoom/unzoom/toggle is specified, defaults to toggle.
        """
        args = ["zoom-pane", "--pane-id", str(pane_id)]

        if zoom:
            args.append("--zoom")
        elif unzoom:
            args.append("--unzoom")
        elif toggle:
            args.append("--toggle")
        else:
            args.append("--toggle")

        self.run(args, intent=f"zoom pane {pane_id}")
