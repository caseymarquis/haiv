# haiv-tui

The terminal UI. A Textual app that runs in the left pane of the hud tab, providing a command center for managing sessions and minds. The TUI consumes raw data from `TuiModel` (defined in haiv-lib) and assembles display-specific DTOs within each widget.

**Location:** `worktrees/main/haiv-tui/src/haiv_tui/`

```
haiv_tui/
├── __init__.py          # Re-exports main from _runner
├── _runner.py           # Entry point: single run + os.execv restart
├── app.py               # HaivApp — takes deps/server/client via constructor
├── init.py              # HaivDeps dataclass + init() factory
├── recent_files_worker.py  # Background thread: file watcher + gatherer
├── store.py             # TuiStore — dirty-driven signal dispatch
└── widgets/
    ├── debounce_button.py   # Reusable button with cooldown after press
    ├── errors.py            # Error display (plain list[str], no assembly)
    ├── hud.py               # HUD: always-visible session panel + action bar
    ├── markdown_file.py     # File viewer with watchdog auto-refresh
    ├── recent_files.py      # Recent files list + age coloring + diff stats
    └── sessions.py          # Sessions tree + action bar + DTOs + assembly
```

---

## Data Flow

```
Raw data (haiv-lib) → TuiModel sections → TuiServer (dirty tracking)
    → poll loop drains dirty → TuiStore fires signals
    → widgets call assembly functions (raw → DTO) → render DTOs
```

**Key principle:** Raw data gathering (haiv-lib) is separate from display assembly (haiv-tui). The model holds only raw sections (`SessionsRaw`, `GitRaw`, `ActiveMindRaw`). Widgets own their own DTOs and assembly logic — co-located at the bottom of each widget file. Assembly functions are pure (raw in, DTO out) and testable without Textual.

## `_runner.py` — Entry point

Single-run entry point. Creates deps, server, client, runs the app. On `Ctrl+R`, the app exits with `RESTART_EXIT_CODE` and the runner calls `os.execv("hv-tui")` to replace the process entirely — no module flushing, no stale Textual class caches. Crash tracebacks go to `~/.cache/haiv/last-crash.log`. The runner checks the return code *before* calling `app.shutdown()` because shutdown can block on thread joins.

## `app.py` — HaivApp

Textual `App` subclass. Takes `HaivDeps`, `TuiServer`, and `TuiLocalClient` as keyword-only constructor params — no internal dependency resolution. Owns the server lifecycle. On mount:
- Sets the WezTerm pane title to `TUI_PANE_TITLE` via OSC 2 (used by `hv start` for crash detection)
- Starts the TUI server and a poll loop (0.1s interval)
- Watches the sessions file for external changes

The poll loop calls `server.drain_dirty()` to atomically get changed section names, reads a frozen snapshot, and passes both to `store.update()`. The store fires blinker signals only for dirty sections.

Layout: `Header`, session panel (65% — HUD with action bar + recent files), tabs panel (35% — Sessions, Plans), `ErrorsWidget`, `Footer`. `Screen { overflow: hidden }` prevents outer scroll. Tab/Shift+Tab cycles tabs. Active mind detected from WezTerm tab title on mount and displayed in the header.

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

## **CRITICAL: Do Not Override Textual Internal Methods**

**Never name a method `_render` on a Textual widget.** Textual's `Widget` base class uses `_render()` internally to produce visual output. Overriding it with a method that returns `None` causes `AttributeError: 'NoneType' object has no attribute 'render_strips'` — a crash that is extremely difficult to diagnose because:

- The error points to Textual internals, not your code
- The method is never explicitly called by you
- Tests of identical inline widget classes pass (because Textual resolves the MRO differently)
- The crash only manifests when the widget is imported from a separate module

**Safe alternatives:** `_refresh_content`, `_rebuild`, `_update_display` — anything that doesn't collide with Textual's private API. In general, avoid `_render`, `_compose`, `_layout`, and other `_`-prefixed names that Textual might use internally.

---

## Dependency Injection

All widgets declare dependencies as keyword-only constructor params. No widget reaches through `self.app` — deps come in via constructor, store subscriptions happen in `on_mount()`. This enables isolated widget testing: mount any widget in a bare `App` with mock deps, no `HaivApp` needed.

Test harness lives in `tests/harness.py`: `WidgetTestApp` (bare app mounting a single widget), `make_sessions_deps()`, `make_haiv_deps()`, `make_mock_server()`, `make_mock_client()`. Per-widget test files merge assembly + widget tests.
