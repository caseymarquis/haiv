"""Thin tmux subprocess wrapper with educational output.

By default, prints commands as they run. On failure, provides a prompt
that encourages Claude to analyze and help fix the error.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from haiv.errors import CommandError


class TmuxError(CommandError):
    """Raised when a tmux command fails.

    Attributes:
        stderr: The stderr output from the tmux command.
    """

    def __init__(self, message: str, stderr: str = ""):
        super().__init__(message)
        self.stderr = stderr


class TmuxWindow:
    """A window within a tmux session.

    Created via Tmux.get_window(), not directly instantiated.

    Attributes:
        tmux: The parent Tmux instance.
        name: The window name.
        created: True if the window was just created, False if it already existed.
    """

    def __init__(self, tmux: "Tmux", name: str, created: bool):
        self.tmux = tmux
        self.name = name
        self.created = created

    def send_keys(self, keys: str, enter: bool = True) -> None:
        """Send keys to this window.

        Args:
            keys: The keys/text to send.
            enter: If True, append Enter key after the keys.
        """
        self.tmux.send_keys(keys, target=self.name, enter=enter)

    def capture_pane(
        self,
        start: int | None = None,
        end: int | None = None,
    ) -> str:
        """Capture the contents of this window's pane.

        Args:
            start: Start line (negative = from scrollback). Default: visible start.
            end: End line. Default: visible end.

        Returns:
            The captured pane content.
        """
        return self.tmux.capture_pane(target=self.name, start=start, end=end)

    def kill(self) -> None:
        """Kill this window."""
        self.tmux.kill_window(self.name)


class Tmux:
    """Thin wrapper around tmux commands for a single session.

    The session name is derived from the hv_root directory name.

    Args:
        hv_root: Path to the haiv repository root. Session name = directory name.
        quiet: If True, suppress output and Claude prompts.
    """

    def __init__(self, hv_root: Path, quiet: bool = False):
        self.hv_root = Path(hv_root)
        self.quiet = quiet

    @property
    def session(self) -> str:
        """The tmux session name, derived from the hv_root directory name."""
        return self.hv_root.name

    def _run(
        self,
        cmd: str,
        *,
        intent: str | None = None,
        check: bool = True,
        quiet: bool | None = None,
    ) -> str:
        """Run a tmux command (internal, does NOT auto-create session).

        IMPORTANT: Only use _run() for session management methods (has_session,
        create_session_if_needed). All other methods should use run() to ensure
        the session exists before operating on it.

        Args:
            cmd: Tmux command without 'tmux' prefix (e.g., "list-windows -t session").
            intent: Optional description of what we're trying to accomplish.
            check: If True (default), raise TmuxError on non-zero exit.
                   If False, return stdout regardless of exit code.
            quiet: Override instance quiet setting for this call.

        Returns:
            stdout from the command.

        Raises:
            TmuxError: If the command fails and check=True.
        """
        full_cmd = f"tmux {cmd}"
        be_quiet = quiet if quiet is not None else self.quiet

        if not be_quiet:
            print(f"→ {full_cmd}")

        result = subprocess.run(
            full_cmd,
            shell=True,
            capture_output=True,
            text=True,
        )

        if check and result.returncode != 0:
            if not be_quiet:
                if result.stderr.strip():
                    print(result.stderr.rstrip())

                if intent:
                    print(f"\nWhile trying to: {intent}")

                print(
                    "\nAnalyze the above error, explain what happened, "
                    "and suggest a fix."
                )

            raise TmuxError(
                f"tmux command failed: {full_cmd}",
                stderr=result.stderr,
            )

        return result.stdout

    def run(self, cmd: str, *, intent: str | None = None) -> str:
        """Run a tmux command, creating the session if needed.

        IMPORTANT: Use this method (not _run) for all operations that expect
        the session to exist. This ensures the session is created automatically
        on first use.

        Args:
            cmd: Tmux command without 'tmux' prefix (e.g., "list-windows").
            intent: Optional description of what we're trying to accomplish.

        Returns:
            stdout from the command.

        Raises:
            TmuxError: If the command fails.
        """
        self.create_session_if_needed()
        return self._run(cmd, intent=intent)

    def has_session(self) -> bool:
        """Check if the session exists."""
        try:
            # Quiet because a missing session is expected, not an error
            self._run(f"has-session -t {self.session}", quiet=True)
            return True
        except TmuxError:
            return False

    def create_session_if_needed(self) -> bool:
        """Create the session if it doesn't already exist.

        Returns:
            True if a new session was created, False if it already existed.
        """
        if self.has_session():
            return False
        self._run(
            f"new-session -d -s {self.session}",
            intent=f"create session '{self.session}'",
        )
        return True

    def list_windows(self, format: str = "#{window_index}:#{window_name}") -> list[str]:
        """List windows in the session.

        Args:
            format: tmux format string for output.

        Returns:
            List of formatted window strings.
        """
        output = self.run(
            f"list-windows -t {self.session} -F '{format}'",
            intent=f"list windows in session '{self.session}'",
        )
        return [line for line in output.strip().split("\n") if line]

    def capture_pane(
        self,
        target: str | None = None,
        start: int | None = None,
        end: int | None = None,
    ) -> str:
        """Capture the contents of a pane.

        Args:
            target: Pane target (e.g., "0" for window 0, "0.1" for window 0 pane 1).
                    If None, captures the current/first pane.
            start: Start line (negative = from scrollback). Default: visible start.
            end: End line. Default: visible end.

        Returns:
            The captured pane content.
        """
        full_target = f"{self.session}:{target}" if target else self.session

        cmd_parts = ["capture-pane", "-p", f"-t {full_target}"]
        if start is not None:
            cmd_parts.append(f"-S {start}")
        if end is not None:
            cmd_parts.append(f"-E {end}")

        return self.run(
            " ".join(cmd_parts),
            intent=f"capture content from pane '{full_target}'",
        )

    def send_keys(self, keys: str, target: str | None = None, enter: bool = True) -> None:
        """Send keys to a pane.

        Args:
            keys: The keys/text to send.
            target: Pane target (e.g., "0" for window 0). If None, sends to first pane.
            enter: If True, append Enter key after the keys.
        """
        full_target = f"{self.session}:{target}" if target else self.session

        # Escape single quotes in keys
        escaped_keys = keys.replace("'", "'\\''")
        cmd = f"send-keys -t {full_target} '{escaped_keys}'"
        if enter:
            cmd += " Enter"

        self.run(cmd, intent=f"send keys to pane '{full_target}'")

    def get_window(self, name: str, *, must_create: bool = False) -> TmuxWindow:
        """Get or create a window by name.

        Args:
            name: The window name.
            must_create: If True, raise TmuxError if the window already exists.

        Returns:
            TmuxWindow instance with `created` attribute indicating if it was new.

        Raises:
            TmuxError: If must_create=True and window already exists.
        """
        # Check if window exists
        windows = self.list_windows(format="#{window_name}")
        exists = name in windows

        if exists:
            if must_create:
                raise TmuxError(
                    f"Window '{name}' already exists in session '{self.session}'",
                    stderr="",
                )
            return TmuxWindow(self, name, created=False)

        # Create the window
        self.run(f"new-window -t {self.session} -n {name}", intent=f"create window '{name}'")
        return TmuxWindow(self, name, created=True)

    def setenv(self, var: str, value: str, *, global_: bool = False) -> None:
        """Set an environment variable in the session.

        Args:
            var: The environment variable name.
            value: The value to set.
            global_: If True, set globally (-g flag). Otherwise, set for the session.
        """
        flag = "-g " if global_ else ""
        # Escape single quotes in value
        escaped_value = value.replace("'", "'\\''")
        self.run(
            f"setenv {flag}-t {self.session} {var} '{escaped_value}'",
            intent=f"set {var} in session",
        )

    def kill_window(self, name: str) -> None:
        """Kill a window by name.

        Args:
            name: The window name to kill.
        """
        self.run(
            f"kill-window -t {self.session}:{name}",
            intent=f"kill window '{name}'",
        )

    def has_window(self, name: str) -> bool:
        """Check if a window exists.

        Args:
            name: The window name to check.

        Returns:
            True if the window exists, False otherwise.
        """
        windows = self.list_windows(format="#{window_name}")
        return name in windows

    def attach(self) -> None:
        """Attach to the session, replacing the current process.

        This uses os.execvp() to replace the Python process with tmux.
        The session is created first if it doesn't exist.

        Raises:
            CommandError: If called from within Claude Code or tmux.
        """
        if os.environ.get("CLAUDECODE"):
            raise CommandError(
                "Cannot attach to tmux from within Claude Code. "
                "Run 'hv tmux' from a regular terminal instead."
            )
        if os.environ.get("TMUX"):
            raise CommandError(
                "Already inside tmux. Use 'tmux switch-client -t "
                f"{self.session}' to switch sessions."
            )

        self.create_session_if_needed()
        os.execvp("tmux", ["tmux", "attach-session", "-t", self.session])
