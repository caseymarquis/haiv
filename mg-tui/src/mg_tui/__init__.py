import importlib
import sys
from pathlib import Path

from mg._infrastructure.TuiServer import RESTART_EXIT_CODE


def _reload_packages():
    """Flush mg and mg_tui modules so the next import picks up code changes."""
    importlib.invalidate_caches()
    for key in [k for k in sys.modules if k.startswith(("mg.", "mg_tui."))]:
        del sys.modules[key]
    # Also remove the top-level package entries themselves
    sys.modules.pop("mg", None)
    sys.modules.pop("mg_tui", None)


def main():
    project = sys.argv[1] if len(sys.argv) > 1 else Path.cwd().name
    while True:
        from mg_tui.app import MindGamesApp

        app = MindGamesApp(project)
        app.run()
        app.shutdown()
        if (app.return_code or 0) != RESTART_EXIT_CODE:
            break
        _reload_packages()
