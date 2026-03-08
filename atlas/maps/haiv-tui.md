# haiv-tui

The terminal UI. A Textual app that runs in the left pane of the hud tab, providing a command center for managing sessions and minds. The TUI is purely a display — all domain logic lives in `haiv-lib/helpers/tui/helpers.py`, which the app calls directly.

**Location:** `worktrees/main/haiv-tui/src/haiv_tui/`

```
haiv_tui/
├── __init__.py       # Entry point: main() loop with hot-reload
├── app.py            # HaivApp (Textual App subclass)
├── init.py           # Dependency initialization
├── store.py          # TuiStore — signal dispatch from model snapshots
└── widgets/
    ├── errors.py
    ├── hud.py
    ├── markdown_file.py
    └── sessions.py
```

---

## `__init__.py` — Entry point

A `while True` loop that creates and runs the app. On `Ctrl+R`, the app exits with `RESTART_EXIT_CODE`, the loop flushes all `haiv` and `haiv_tui` modules from `sys.modules`, and reimports everything — live code reload without restarting the process.

## `app.py` — HaivApp

Textual `App` subclass. Owns the `TuiServer` lifecycle. On mount:
- Sets the WezTerm pane title to `TUI_PANE_TITLE` via OSC 2 (used by `hv start` for crash detection)
- Starts the TUI server and a poll loop (0.1s interval)
- Watches the sessions file for external changes

Layout: `Header`, `TabbedContent` (Sessions, Session, Plans), `ErrorsWidget`, `Footer`. Tab/Shift+Tab cycles tabs.

The poll model avoids cross-thread callbacks — the Textual thread pulls state from the server, the model thread never calls back into Textual.

## Uncharted

- `init.py` — How dependencies (paths, settings, terminal manager) are assembled
- `store.py` — How model snapshots become per-section signals for widgets
- `widgets/` — Individual widget implementations
