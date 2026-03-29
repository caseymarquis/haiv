"""haiv error types and handling.

These are user-facing, expected failures - not internal bugs.
"""

import os
import sys
import traceback
from pathlib import Path


class CommandError(Exception):
    """Raised when a command fails in an expected way.

    Examples: missing required flag, invalid input, precondition not met.
    """

    pass


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


def handle_error(exc: Exception) -> None:
    """Handle an exception: print message, log traceback, exit."""
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
