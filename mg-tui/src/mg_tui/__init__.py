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
    from mg._infrastructure.identity import detect_user
    from mg.paths import Paths, get_mg_root

    mg_root = get_mg_root(Path.cwd())
    project = sys.argv[1] if len(sys.argv) > 1 else mg_root.name

    user = detect_user(mg_root / "users")
    paths = None
    if user is not None:
        paths = Paths(_called_from=None, _pkg_root=None, _mg_root=mg_root, _user_name=user.name)

    while True:
        from mg_tui.app import MindGamesApp

        app = MindGamesApp(project, paths=paths)
        app.run()
        app.shutdown()
        if (app.return_code or 0) != RESTART_EXIT_CODE:
            break
        _reload_packages()
