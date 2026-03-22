# haiv-tui

The terminal UI. A Textual app that runs in the left pane of the hud tab, providing a command center for managing sessions and minds. The TUI consumes raw data from `TuiModel` (defined in haiv-lib) and assembles display-specific DTOs within each widget.

**Location:** `worktrees/main/haiv-tui/src/haiv_tui/`

```
haiv_tui/
├── __init__.py       # Entry point: main() loop with hot-reload
├── app.py            # HaivApp (Textual App subclass)
├── init.py           # Dependency initialization
├── store.py          # TuiStore — dirty-driven signal dispatch
└── widgets/
    ├── errors.py     # Error display (plain list[str], no assembly)
    ├── hud.py        # HUD: widget + HudView DTO + assembly
    ├── markdown_file.py  # File viewer with watchdog auto-refresh
    └── sessions.py   # Sessions tree: widget + SessionNodeView DTO + assembly
```

---

## Data Flow

```
Raw data (haiv-lib) → TuiModel sections → TuiServer (dirty tracking)
    → poll loop drains dirty → TuiStore fires signals
    → widgets call assembly functions (raw → DTO) → render DTOs
```

**Key principle:** Raw data gathering (haiv-lib) is separate from display assembly (haiv-tui). The model holds only raw sections (`SessionsRaw`, `GitRaw`, `ActiveMindRaw`). Widgets own their own DTOs and assembly logic — co-located at the bottom of each widget file. Assembly functions are pure (raw in, DTO out) and testable without Textual.

## `__init__.py` — Entry point

A `while True` loop that creates and runs the app. On `Ctrl+R`, the app exits with `RESTART_EXIT_CODE`, the loop flushes all `haiv` and `haiv_tui` modules from `sys.modules`, and reimports everything — live code reload without restarting the process.

## `app.py` — HaivApp

Textual `App` subclass. Owns the `TuiServer` lifecycle. On mount:
- Sets the WezTerm pane title to `TUI_PANE_TITLE` via OSC 2 (used by `hv start` for crash detection)
- Starts the TUI server and a poll loop (0.1s interval)
- Watches the sessions file for external changes

The poll loop calls `server.drain_dirty()` to atomically get changed section names, reads a frozen snapshot, and passes both to `store.update()`. The store fires blinker signals only for dirty sections.

Layout: `Header`, `TabbedContent` (Sessions, Session, Plans), `ErrorsWidget`, `Footer`. Tab/Shift+Tab cycles tabs.

## `store.py` — TuiStore

Dirty-driven signal dispatcher. Holds the last frozen `TuiModel` snapshot. On `update(model, dirty)`, fires `{name}_changed` blinker signals for each dirty section name. Signals are auto-discovered from `dataclasses.fields(TuiModel)` — adding a new section to the model creates a signal automatically.

## `widgets/sessions.py` — Sessions Tree

The most complex widget. Subscribes to `sessions_changed`, `git_changed`, and `active_mind_changed`. Holds the latest of each raw section and calls `build_session_tree()` to assemble `SessionNodeView` DTOs on any change. The tree renders DTOs — label formatting, active mind highlighting, and git stats are all pre-computed in the DTO.

`SessionPreview` shows details of the highlighted node. `action_launch_session` calls `helpers.mind_launch` to start/switch minds.

## `widgets/hud.py` — HUD

Subscribes to `active_mind_changed` and `sessions_changed`. Calls `build_hud_view()` to assemble a `HudView` DTO showing the active mind's worktree, task summary, and session identifier.

## Uncharted

- `init.py` — How dependencies (paths, settings, terminal manager) are assembled
- Widget dependency injection — widgets currently reach through `self.app` for store/terminal/paths; should declare dependencies explicitly
