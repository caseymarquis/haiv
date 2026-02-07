"""Terminal management for mg windows."""

from __future__ import annotations

import os
import shlex
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from mg.errors import CommandError

if TYPE_CHECKING:
    from mg.wrappers.wezterm import Pane, WezTerm


class TerminalManager:
    """Manages WezTerm window and tab layout for an mg project.

    Identifies its window by tab titles: mg({project}) for the hud tab,
    mg({project}):buffer for the buffer tab. This works across multiple
    projects sharing a single WezTerm instance.
    """

    def __init__(self, wezterm: WezTerm, mg_root: Path, tui_command: list[str]) -> None:
        self.wezterm = wezterm
        self.mg_root = mg_root
        self.tui_command = tui_command
        self.project = mg_root.name
        self.hud_tab_title = f"mg({self.project})"
        self.buffer_tab_title = f"mg({self.project}):buffer"

    # -- Public API --

    def launch_in_mind_pane(
        self,
        env: dict[str, str],
        commands: list[str],
    ) -> None:
        """Spawn a new pane in buffer, swap it into the hud mind slot.

        1. Spawn a new pane in the buffer tab (with env vars)
        2. Move the current mind pane to the buffer tab
        3. Move the new pane into the hud's right side
        4. Send commands to the new pane

        The caller owns all domain logic (command construction,
        env var selection).

        Args:
            env: Environment variables to set in the spawned process.
            commands: Shell commands to send after the pane is in place.

        Raises:
            CommandError: If the workspace is not running.
        """
        hud_pane = self._find_hud_pane()
        if hud_pane is None:
            raise CommandError(
                "Workspace not running. Start it first with: mg start"
            )

        buffer_pane = self._find_buffer_pane()
        if buffer_pane is None:
            raise CommandError(
                "Buffer tab not found. Restart workspace with: mg start"
            )

        cwd = str(self.mg_root)

        # 1. Spawn new pane in buffer tab
        new_pane_id = self.wezterm.spawn(
            window_id=buffer_pane.window_id, cwd=cwd,
        )

        # 2. Move current mind pane to buffer (if one exists)
        mind_pane = self._find_mind_pane()
        if mind_pane is not None:
            self.wezterm.move_pane_to_new_tab(
                mind_pane.pane_id, window_id=buffer_pane.window_id,
            )

        # 3. Move new pane into hud as right split
        self.wezterm.split_pane(
            hud_pane.pane_id, direction="right", percent=50,
            move_pane_id=new_pane_id,
        )

        # 4. Send env vars and commands as a single &&-chained line
        parts: list[str] = []
        if sys.platform == "win32":
            for key, value in env.items():
                parts.append(f'set "{key}={value}"')
        else:
            for key, value in env.items():
                parts.append(f"export {key}={shlex.quote(value)}")
        parts.extend(commands)
        self.wezterm.send_text(new_pane_id, " && ".join(parts) + "\n")

    def ensure_workspace(self) -> None:
        """Ensure the mg window exists with the standard tab layout.

        | In WezTerm? | Window exists? | Action                                  |
        |-------------|----------------|-----------------------------------------|
        | No          | N/A            | Launch WezTerm with 'mg start'          |
        | Yes         | No             | Create new window, set up layout        |
        | Yes         | Yes            | Activate it, print message if needed    |
        """
        if not self._in_wezterm():
            self._launch_wezterm()
            return

        hud_pane = self._find_hud_pane()
        if hud_pane is None:
            self._create_window()
            return

        # Window exists — focus it
        self.wezterm.activate_pane(hud_pane.pane_id)
        print(f"mg window for '{self.project}' is ready.")

    # -- Queries --

    def _in_wezterm(self) -> bool:
        """Check if we're running inside a WezTerm session."""
        return os.environ.get("TERM_PROGRAM") == "WezTerm"

    def _find_hud_pane(self) -> Pane | None:
        """Find the hud pane (left pane in the hud tab)."""
        for pane in self.wezterm.list_panes():
            if pane.tab_title == self.hud_tab_title and pane.left_col == 0:
                return pane
        return None

    def _find_mind_pane(self) -> Pane | None:
        """Find the mind pane (right pane in the hud tab)."""
        for pane in self.wezterm.list_panes():
            if pane.tab_title == self.hud_tab_title and pane.left_col != 0:
                return pane
        return None

    def _find_buffer_pane(self) -> Pane | None:
        """Find any pane in the buffer tab."""
        for pane in self.wezterm.list_panes():
            if pane.tab_title == self.buffer_tab_title:
                return pane
        return None

    # -- Actions --

    def _launch_wezterm(self) -> None:
        """Launch a new WezTerm instance that runs 'mg start'."""
        self.wezterm.run_external(
            ["start", "--cwd", str(self.mg_root), "--", "mg", "start"],
            intent=f"launch WezTerm for '{self.project}'",
        )

    def _create_window(self) -> None:
        """Create a new window with hud and buffer tabs."""
        cwd = str(self.mg_root)

        # New window with TUI running in the hud pane
        hud_pane_id = self.wezterm.spawn(
            new_window=True, cwd=cwd, command=self.tui_command + [self.project],
        )
        self.wezterm.set_tab_title(self.hud_tab_title, pane_id=hud_pane_id)

        # Split right for mind pane
        self.wezterm.split_pane(hud_pane_id, direction="right", percent=50, cwd=cwd)

        # Find window_id so we can add the buffer tab to the same window
        panes = self.wezterm.list_panes()
        window_id = next(p.window_id for p in panes if p.pane_id == hud_pane_id)

        # Buffer tab
        buffer_pane_id = self.wezterm.spawn(window_id=window_id, cwd=cwd)
        self.wezterm.set_tab_title(self.buffer_tab_title, pane_id=buffer_pane_id)

        # Focus the hud pane
        self.wezterm.activate_pane(hud_pane_id)
