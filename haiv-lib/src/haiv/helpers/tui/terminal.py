"""Terminal management for haiv windows."""

from __future__ import annotations

import os
import shlex
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from haiv.errors import CommandError

if TYPE_CHECKING:
    from haiv.wrappers.wezterm import Pane, WezTerm


class TerminalManager:
    """Manages WezTerm window and tab layout for a haiv project.

    Tab naming convention:
        hv({project})        — hud tab, no active mind (TUI only)
        hv({project}):mind   — hud tab with active mind
        ~mind                — parked mind tab

    Parked tabs don't need the project prefix because they're found
    by window_id from the hud tab. No ambiguity across projects.
    """

    def __init__(self, wezterm: WezTerm, haiv_root: Path, tui_command: list[str]) -> None:
        self.wezterm = wezterm
        self.haiv_root = haiv_root
        self.tui_command = tui_command
        self.project = haiv_root.name

    # -- Tab title helpers --

    @property
    def hud_tab_prefix(self) -> str:
        return f"hv({self.project})"

    def _hud_tab_title(self, mind: str | None = None) -> str:
        if mind:
            return f"hv({self.project}):{mind}"
        return f"hv({self.project})"

    @staticmethod
    def _parked_tab_title(mind: str) -> str:
        return f"~{mind}"

    # -- Public API --

    def launch_in_mind_pane(
        self,
        mind: str,
        env: dict[str, str],
        commands: list[str],
    ) -> None:
        """Swap a new pane into the hud mind slot.

        If a mind pane exists: split it to create the new pane (no tab
        switch), then park the old pane in its own tab.

        If no mind pane: split the TUI pane directly.

        Args:
            mind: Name of the mind being launched.
            env: Environment variables to set in the spawned process.
            commands: Shell commands to send after the pane is in place.

        Raises:
            CommandError: If the workspace is not running.
        """
        hud_pane = self._find_hud_pane()
        if hud_pane is None:
            raise CommandError(
                "Workspace not running. Start it first with: hv start"
            )

        cwd = str(self.haiv_root)
        old_mind_pane = self._find_mind_pane()

        if old_mind_pane is not None:
            # Split the current mind pane — new pane stays in hud
            new_pane_id = self.wezterm.split_pane(
                old_mind_pane.pane_id, direction="right", cwd=cwd,
            )

            # Park old mind pane to its own tab
            old_mind = self.get_active_mind_name()
            self.wezterm.move_pane_to_new_tab(
                old_mind_pane.pane_id, window_id=hud_pane.window_id,
            )
            if old_mind:
                self.wezterm.set_tab_title(
                    self._parked_tab_title(old_mind), pane_id=old_mind_pane.pane_id,
                )
        else:
            # No mind pane — split TUI directly
            new_pane_id = self.wezterm.split_pane(
                hud_pane.pane_id, direction="right", percent=50, cwd=cwd,
            )

        # 4. Send env vars and commands
        parts: list[str] = []
        if sys.platform == "win32":
            for key, value in env.items():
                parts.append(f'set "{key}={value}"')
        else:
            for key, value in env.items():
                parts.append(f"export {key}={shlex.quote(value)}")
        parts.extend(commands)
        self.wezterm.send_text(new_pane_id, " && ".join(parts) + "\n", no_paste=True)

        # 5. Focus new pane, update hud tab title
        self.wezterm.activate_pane(new_pane_id)
        self.wezterm.set_tab_title(
            self._hud_tab_title(mind), pane_id=new_pane_id,
        )

    def switch_to_mind(self, mind: str) -> None:
        """Switch the hud to a parked mind.

        Finds the parked mind's tab, parks the current mind,
        and pulls the target mind into the hud.

        Args:
            mind: Name of the mind to switch to.

        Raises:
            CommandError: If workspace not running or mind not found.
        """
        hud_pane = self._find_hud_pane()
        if hud_pane is None:
            raise CommandError(
                "Workspace not running. Start it first with: hv start"
            )

        target_pane = self._find_parked_mind(mind)
        if target_pane is None:
            raise CommandError(f"No parked pane found for mind: {mind}")

        # Park current mind (if one exists)
        old_mind_pane = self._find_mind_pane()
        if old_mind_pane is not None:
            old_mind = self.get_active_mind_name()
            self.wezterm.move_pane_to_new_tab(
                old_mind_pane.pane_id, window_id=hud_pane.window_id,
            )
            if old_mind:
                self.wezterm.set_tab_title(
                    self._parked_tab_title(old_mind), pane_id=old_mind_pane.pane_id,
                )

        # Pull target into hud
        self.wezterm.split_pane(
            hud_pane.pane_id, direction="right", percent=50,
            move_pane_id=target_pane.pane_id,
        )

        # Focus and update title
        self.wezterm.activate_pane(target_pane.pane_id)
        self.wezterm.set_tab_title(
            self._hud_tab_title(mind), pane_id=target_pane.pane_id,
        )

    def ensure_workspace(self) -> None:
        """Ensure the haiv window exists with the standard tab layout.

        | In WezTerm? | Window exists? | Action                                  |
        |-------------|----------------|-----------------------------------------|
        | No          | N/A            | Launch WezTerm with 'hv start'          |
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
        print(f"haiv window for '{self.project}' is ready.")

    def try_send_text_to_mind(self, mind: str, text: str, *, submit: bool = False) -> bool:
        """Send text to a mind's pane, whether active or parked.

        Args:
            mind: Name of the mind to send text to.
            text: Text to send.
            submit: If False (default), text appears in input without submitting.
                If True, text is submitted as if the user pressed Enter.

        Returns:
            True if the mind's pane was found and text was sent, False otherwise.
        """
        pane = self._find_pane_for_mind(mind)
        if pane is None:
            return False

        self.wezterm.send_text(pane.pane_id, text)
        if submit:
            self.wezterm.send_text(pane.pane_id, "\n", no_paste=True)

        return True

    def send_text_to_mind(self, mind: str, text: str, *, submit: bool = False) -> None:
        """Send text to a mind's pane, raising if not found.

        Args:
            mind: Name of the mind to send text to.
            text: Text to send.
            submit: If False (default), text appears in input without submitting.
                If True, text is submitted as if the user pressed Enter.

        Raises:
            CommandError: If no pane found for the mind.
        """
        if not self.try_send_text_to_mind(mind, text, submit=submit):
            raise CommandError(f"No pane found for mind: {mind}")

    # -- Queries (public) --

    def close_parked_mind(self, mind: str) -> None:
        """Kill a parked mind's pane.

        Args:
            mind: Name of the mind whose parked pane to close.

        Raises:
            CommandError: If no parked pane found for the mind.
        """
        pane = self._find_parked_mind(mind)
        if pane is None:
            raise CommandError(f"No parked pane found for mind: {mind}")
        self.wezterm.kill_pane(pane.pane_id)

    def get_active_mind_name(self) -> str | None:
        """Get the name of the mind currently showing in the hud.

        Queries terminal panes — this does real work each call.
        """
        for pane in self.wezterm.list_panes():
            if pane.tab_title.startswith(self.hud_tab_prefix):
                if ":" in pane.tab_title:
                    return pane.tab_title.split(":", 1)[1]
                return None
        return None

    def is_mind_active(self, mind: str) -> bool:
        """True if mind is currently showing in the hud."""
        return self.get_active_mind_name() == mind

    def is_mind_parked(self, mind: str) -> bool:
        """True if mind has a parked pane."""
        return self._find_parked_mind(mind) is not None

    # -- Queries (private) --

    def _in_wezterm(self) -> bool:
        """Check if we're running inside a WezTerm session."""
        return os.environ.get("TERM_PROGRAM") == "WezTerm"

    def _find_hud_pane(self) -> Pane | None:
        """Find the TUI pane (left pane in the hud tab)."""
        for pane in self.wezterm.list_panes():
            if pane.tab_title.startswith(self.hud_tab_prefix) and pane.left_col == 0:
                return pane
        return None

    def _find_mind_pane(self) -> Pane | None:
        """Find the active mind pane (right pane in the hud tab)."""
        for pane in self.wezterm.list_panes():
            if pane.tab_title.startswith(self.hud_tab_prefix) and pane.left_col != 0:
                return pane
        return None

    def _find_pane_for_mind(self, mind: str) -> Pane | None:
        """Find a mind's pane — active (hud right pane) or parked (~mind tab)."""
        if self.get_active_mind_name() == mind:
            return self._find_mind_pane()
        return self._find_parked_mind(mind)

    def _find_parked_mind(self, mind: str) -> Pane | None:
        """Find a parked mind's pane by tab title."""
        title = self._parked_tab_title(mind)
        for pane in self.wezterm.list_panes():
            if pane.tab_title == title:
                return pane
        return None

    # -- Actions --

    def _launch_wezterm(self) -> None:
        """Launch a new WezTerm instance that runs 'hv start'."""
        self.wezterm.run_external(
            ["start", "--cwd", str(self.haiv_root), "--", "hv", "start"],
            intent=f"launch WezTerm for '{self.project}'",
        )

    def _create_window(self) -> None:
        """Create a new window with hud tab."""
        cwd = str(self.haiv_root)

        # New window with TUI running in the hud pane
        hud_pane_id = self.wezterm.spawn(
            new_window=True, cwd=cwd, command=self.tui_command + [self.project],
        )
        self.wezterm.set_tab_title(self._hud_tab_title(), pane_id=hud_pane_id)

        # Split right for mind pane (empty shell, ready for hv start <mind>)
        self.wezterm.split_pane(hud_pane_id, direction="right", percent=50, cwd=cwd)

        # Focus the hud pane
        self.wezterm.activate_pane(hud_pane_id)
