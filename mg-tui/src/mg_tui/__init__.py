import importlib
import sys
from pathlib import Path

from haiv._infrastructure.TuiServer import RESTART_EXIT_CODE


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
    project = sys.argv[1] if len(sys.argv) > 1 else Path.cwd().name

    while True:
        from haiv_tui.app import HaivApp

        app = HaivApp(project)
        app.run()
        app.shutdown()
        if (app.return_code or 0) != RESTART_EXIT_CODE:
            break
        _reload_packages()
