"""TUI entry point — restarts via os.execv for clean process reload.

Ctrl+R in the TUI exits with RESTART_EXIT_CODE. This loop detects that
and re-execs the process, giving Textual a completely fresh start with
no stale class caches or module state.
"""

import os
import shutil
import sys
import traceback
from pathlib import Path

LOG_DIR = Path.home() / ".cache" / "haiv"
CRASH_LOG = LOG_DIR / "last-crash.log"
EXIT_LOG = LOG_DIR / "last-exit.log"
RESTART_EXIT_CODE = 75  # duplicated from haiv._infrastructure.TuiServer to avoid importing haiv


def _write_log(path: Path, text: str) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    except Exception:
        pass


def main():
    # --- Capture all inputs upfront ---
    project = sys.argv[1] if len(sys.argv) > 1 else Path.cwd().name

    try:
        from haiv._infrastructure.TuiServer import TuiLocalClient, TuiServer
        from haiv_tui.app import HaivApp
        from haiv_tui.init import init as init_haiv_deps

        deps = init_haiv_deps(on_error=lambda msg: sys.stderr.write(f"{msg}\n"))
        server = TuiServer(project)
        client = TuiLocalClient(server.submit)

        app = HaivApp(deps=deps, server=server, client=client)
        app.run()

        # Check return code BEFORE shutdown — shutdown blocks on thread join.
        # os.execv replaces the process so cleanup is unnecessary on restart.
        rc = app.return_code
        if (rc or 0) == RESTART_EXIT_CODE:
            if sys.platform == "win32":
                # os.execv on Windows spawns a detached process instead of
                # replacing the current one, breaking the terminal context.
                # Exit cleanly and let the user restart manually for now.
                return
            hv_tui = shutil.which("hv-tui")
            if hv_tui is None:
                _write_log(EXIT_LOG, "hv-tui not found on PATH, cannot restart\n")
                return
            os.execv(hv_tui, [hv_tui, project])

        app.shutdown()
        if rc:
            _write_log(EXIT_LOG, f"return_code={rc!r}\n")
    except Exception:
        _write_log(CRASH_LOG, traceback.format_exc())
        raise
