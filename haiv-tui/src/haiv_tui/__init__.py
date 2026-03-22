import importlib
import logging
import sys
import traceback
from pathlib import Path

from haiv._infrastructure.TuiServer import RESTART_EXIT_CODE

LOG_FILE = Path.home() / ".cache" / "haiv" / "tui.log"

logger = logging.getLogger("haiv_tui")


def _setup_logging() -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    handler = logging.FileHandler(LOG_FILE)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)


def _reload_packages():
    """Flush haiv and haiv_tui modules so the next import picks up code changes."""
    importlib.invalidate_caches()
    for key in [k for k in sys.modules if k.startswith(("haiv.", "haiv_tui."))]:
        del sys.modules[key]
    # Also remove the top-level package entries themselves
    sys.modules.pop("haiv", None)
    sys.modules.pop("haiv_tui", None)


def main():
    # Keep this function THIN. Ctrl+R reloads haiv and haiv_tui modules,
    # but main() itself is already executing and won't be reloaded.
    # All logic that should respond to code changes must live in
    # modules imported inside the loop (e.g. HaivApp, helpers).
    _setup_logging()
    log = logger  # local ref survives module reload
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
            if (app.return_code or 0) != RESTART_EXIT_CODE:
                break
            _reload_packages()
        except Exception:
            log.error("TUI crashed during reload:\n%s", traceback.format_exc())
            break
