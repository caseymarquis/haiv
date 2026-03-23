# haiv-tui

The terminal UI. A Textual app that runs in the left pane of the hud tab, providing a command center for managing sessions and minds. The TUI consumes raw data from `TuiModel` (defined in haiv-lib) and assembles display-specific DTOs within each widget.

**Location:** `worktrees/main/haiv-tui/src/haiv_tui/`

```
haiv_tui/
├── __init__.py       # Entry point: main() loop with hot-reload + dep factory
├── app.py            # HaivApp — takes deps/server/client via constructor
├── init.py           # HaivDeps dataclass + init() factory
├── store.py          # TuiStore — dirty-driven signal dispatch
└── widgets/
    ├── errors.py     # Error display (plain list[str], no assembly)
    ├── hud.py        # HUD: widget + HudView DTO + assembly
    ├── markdown_file.py  # File viewer with watchdog auto-refresh
    └── sessions.py   # Sessions tree + action bar + DTOs + assembly
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

A `while True` loop that creates and runs the app. On `Ctrl+R`, the app exits with `RESTART_EXIT_CODE`, the loop flushes all `haiv` and `haiv_tui` modules from `sys.modules`, and reimports everything — live code reload without restarting the process. The loop holds the dependency factory: each iteration calls `init()` to get fresh `HaivDeps`, creates a `TuiServer` and `TuiLocalClient`, and passes all three to `HaivApp`.

## `app.py` — HaivApp

Textual `App` subclass. Takes `HaivDeps`, `TuiServer`, and `TuiLocalClient` as keyword-only constructor params — no internal dependency resolution. Owns the server lifecycle. On mount:
- Sets the WezTerm pane title to `TUI_PANE_TITLE` via OSC 2 (used by `hv start` for crash detection)
- Starts the TUI server and a poll loop (0.1s interval)
- Watches the sessions file for external changes

The poll loop calls `server.drain_dirty()` to atomically get changed section names, reads a frozen snapshot, and passes both to `store.update()`. The store fires blinker signals only for dirty sections.

Layout: `Header`, `TabbedContent` (Sessions, Session, Plans), `ErrorsWidget`, `Footer`. Tab/Shift+Tab cycles tabs.

## `init.py` — Dependency Factory

`HaivDeps` dataclass holds resolved dependencies: `paths` (Paths | None), `settings` (HaivSettings), `terminal` (TerminalManager | None). The `init()` function detects the haiv root, user identity, loads settings, and creates the terminal manager. Called by `main()` on each restart cycle.

## `store.py` — TuiStore

Dirty-driven signal dispatcher. Holds the last frozen `TuiModel` snapshot. On `update(model, dirty)`, fires `{name}_changed` blinker signals for each dirty section name. Signals are auto-discovered from `dataclasses.fields(TuiModel)` — adding a new section to the model creates a signal automatically.

## `widgets/sessions.py` — Sessions Tree + Action Bar

The most complex widget. Takes `store`, `terminal`, `tui_client`, `sessions_file`, `haiv_root`, `settings`, `errors` as keyword-only constructor deps. Subscribes to `sessions_changed`, `git_changed`, and `active_mind_changed` in `on_mount()`. Calls `build_session_tree()` to assemble `SessionNodeView` DTOs — label formatting, active mind highlighting, git stats, and full worktree paths are all pre-computed in the DTO.

Contains three child widgets:
- **`SessionActionBar`** — action bar for the highlighted session. `[e]` opens worktree in file explorer, `[v]` opens in editor. Uses `helpers/open.py` from haiv-lib. Commands configurable via `file_explorer_command` and `editor_command` settings.
- **`SessionPreview`** — shows details of the highlighted node.
- **Tree** — the session tree itself. `action_launch_session` calls `helpers.mind_launch`.

## `widgets/hud.py` — HUD

Takes `store` as keyword-only constructor dep. Subscribes to `active_mind_changed` and `sessions_changed`. Calls `build_hud_view()` to assemble a `HudView` DTO showing the active mind's worktree, task summary, and session identifier.

## Dependency Injection

All widgets declare dependencies as keyword-only constructor params. No widget reaches through `self.app` — deps come in via constructor, store subscriptions happen in `on_mount()`. This enables isolated widget testing: mount any widget in a bare `App` with mock deps, no `HaivApp` needed.

Test harness lives in `tests/harness.py`: `WidgetTestApp` (bare app mounting a single widget), `make_sessions_deps()`, `make_haiv_deps()`, `make_mock_server()`, `make_mock_client()`. Per-widget test files merge assembly + widget tests.
