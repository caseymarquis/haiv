"""TUI entry point — deliberately outside the reload blast radius.

_reload_packages() flushes all haiv.* and haiv_tui.* modules. This file
must NOT be flushed, so it is excluded from that sweep. It imports nothing
from haiv or haiv_tui at the top level — only stdlib.
"""

import importlib
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


def _reload_packages():
    """Flush haiv and haiv_tui modules so the next import picks up code changes."""
    importlib.invalidate_caches()
    for key in [k for k in sys.modules if k.startswith(("haiv.", "haiv_tui."))]:
        # Don't flush ourselves
        if key == "haiv_tui._runner":
            continue
        del sys.modules[key]
    sys.modules.pop("haiv", None)
    sys.modules.pop("haiv_tui", None)


def main():
    project = sys.argv[1] if len(sys.argv) > 1 else Path.cwd().name

    while True:
        try:
            from haiv._infrastructure.TuiServer import TuiLocalClient, TuiServer
            from haiv_tui.app import HaivApp
            from haiv_tui.init import init as init_haiv_deps

            deps = init_haiv_deps(on_error=lambda msg: sys.stderr.write(f"{msg}\n"))
            server = TuiServer(project)
            client = TuiLocalClient(server.submit)

            app = HaivApp(deps=deps, server=server, client=client)
            app.run()
            app.shutdown()
            rc = app.return_code
            if (rc or 0) != RESTART_EXIT_CODE:
                _write_log(EXIT_LOG, f"return_code={rc!r} (expected {RESTART_EXIT_CODE} for restart)\n")
                break
            _reload_packages()
        except Exception:
            _write_log(CRASH_LOG, traceback.format_exc())
            break
