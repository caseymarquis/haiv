# Immediate Plan

**Updated:** 2026-03-23

---

## Current Focus: TUI Feature-Rich, Recent Files Live

Major TUI session today. The TUI now has a split layout (65/35) with the active session panel always visible at top and tabs below. Recent files widget shows files sorted by mtime with age-gradient coloring and git diff stats. Files open in editor on Enter/double-click. Shortest unique suffix algorithm for display names. 67 TUI tests, all green.

Run `hv sessions` to see current active work.

---

## Active Initiatives

- **TUI feature buildout** — layout redesigned, recent files live, file openers per extension next.
- **Relay infrastructure** — unbuilt. Required for haiv to manage external projects (e.g., dnd at `/home/casey/code/dnd/`). The problem: `hv` always runs in haiv-cli's venv, but project/user commands need the project's own venv and dependencies.

---

## Next Up

- **File openers per extension** — `[file_openers]` in `haiv.toml`, default to `code`, per-extension overrides (e.g., `".md" = "typora"`)
- **Type-safe signal subscriptions** — derive signal names from TuiModel fields via reflection, not raw strings
- **TUI publish mechanism** — publish derived state (active mind, etc.) for consumption by `hv` commands. The RecentFilesWorker currently polls — should subscribe instead.
- **Live mind status via Claude Code hooks** — spark's research (temp-aar/claude-hook-integration.md) mapped all lifecycle events. Now that `ActiveMindRaw` exists, hook integration has a natural target.
- **CLAUDE.md clarification** — command search order is user → project → core (highest precedence first), but CLAUDE.md describes it as "haiv_core → haiv_project → haiv_user". Luna flagged this in her AAR. Should be clarified.
- **Clean up stale sessions** — echo [7] and spark [4] are 26+ commits behind main (pre-rename). Close out rather than merge.
- **TUI leaf sorting** — recently active leaves float to top
- **Relay infrastructure** — design settled, unbuilt
- **`pip install haiv` user story** — meta-package exists, UX not worked out
- **Mind launch settings** — `settings.toml` per mind, starting with `launch.system_prompt`
- **Shutdown hang** — file watcher thread join blocks on quit. Restart works (os.execv before shutdown) but quit requires Ctrl+C. Need timeout or daemon thread fix.

---

## Recently Completed

- **Recent files widget** (2026-03-23) — `RecentFilesRaw` section in TuiModel (auto-discovered signal). Background `RecentFilesWorker` watches `worktrees/` via `FileWatcher`, gathers tracked+untracked files via `git ls-files`, diff stats via `git diff --numstat`. Widget shows files with age gradient (green→gray), diff stats, shortest unique suffix display names. Enter/double-click opens in editor. Full path shown at bottom on highlight. Fixed watcher feedback loop (watchdog was firing on open/close read events from VS Code git polling).
- **TUI layout redesign** (2026-03-23) — HUD always visible at top (65%) with vertical action bar + recent files. Sessions and Plans in tabbed area below (35%). `Screen { overflow: hidden }` prevents outer scroll. Active mind detected from WezTerm tab title on mount, displayed in app header. Action bar decoupled from session tree — sources from active mind's worktree path.
- **Hot reload fixed** (2026-03-23) — replaced in-process module flush with `os.execv("hv-tui")`. Textual's LRU caches and `__init_subclass__` registries don't survive module reload — process replacement is the only clean path. `_runner.py` also logs crashes/exits to `~/.cache/haiv/`.
- **Action bar → clickable buttons** (2026-03-23) — replaced static text with `DebounceButton` widgets. New reusable `DebounceButton` widget (configurable cooldown). Removed `e`/`v` keybindings.
- **Widget DI + test harness + action bar** — widgets take deps as keyword-only constructor params. 67 TUI tests total.
- **TUI data model redesign** — separated raw data from display assembly. `write_raw()` API, dirty-set change tracking, DTOs co-located with widgets.
- Older: PyPI name claim, haiv-lib rename, meta-package, atlas system, mg-* cleanup, hook system, TUI, `hv pop`, session tree display

---

## Lessons Learned

- Check live state via `hv sessions`, don't maintain worker tables in notes — they go stale between interactions
- Time is paused between interactions. Design for clear handoffs, not speed.
- Task descriptions: describe the landscape and destination, not the route
- Always worktree, always commit first — one path, clean branch points
- Push regularly — safety net for main
- Research deliverables should go in `temp-aar/`, not `work/` — `work/` gets wiped on pop
- After folder renames, nuke `.venv/` and `uv sync` fresh — hardlinked venvs point to old paths
- Minds working on haiv-hq content need reminding to commit there — pop only handles the worktree branch
- **Never override `_render` on Textual widgets** — it's an internal method. Use `_refresh_content` or similar. See atlas for details.
- **Watchdog fires on open/close events**, not just writes. Filter to `created/modified/moved/deleted` in the bridge handler.
- **Use isolated test copies** when debugging widget issues — don't modify production files during bisection.

---

## Architecture

### TUI Layout
```
Header (active mind + task)
├── session-panel (65%)
│   ├── HudWidget (Horizontal)
│   │   ├── SessionActionBar (vertical, left)
│   │   └── hud-content (Vertical, right)
│   │       ├── RecentFilesWidget
│   │       │   ├── header Static
│   │       │   ├── OptionList (files)
│   │       │   └── path Static
│   │       └── (future: more session tools)
├── tabs-panel (35%)
│   └── TabbedContent
│       ├── Sessions tab → SessionsWidget
│       └── Plans tab → MarkdownFileWidget
├── ErrorsWidget
└── Footer
```

### TUI Data Flow
```
Raw data sources → TuiModel (per-source sections) → TuiServer (dirty tracking)
    → poll loop drains dirty → TuiStore fires signals → widgets rebuild from DTOs
```

- **TuiModel** — raw sections: `SessionsRaw`, `GitRaw`, `ActiveMindRaw`, `RecentFilesRaw`. Plain dataclasses, no base class.
- **write_raw()** — callers pass section kwargs. Server replaces non-None sections, marks dirty.
- **TuiStore** — fires blinker signals for dirty sections. Auto-discovered from TuiModel fields.
- **Widgets** — receive deps via keyword-only constructor params. Subscribe in `on_mount()`. Assembly is pure functions (raw→DTO), testable without Textual.
- **HaivApp** — takes `HaivDeps`, `TuiServer`, `TuiLocalClient` via constructor.
- **_runner.py** — entry point, restart via `os.execv`, crash/exit logging.
- **_Workers** — background threads (file watcher for sessions, RecentFilesWorker for worktree changes).

### Command Side
```
hv commands:  ctx.tui.mind_launch(mind)       # facade assembles deps
TUI app:      helpers.mind_launch(term, ...)   # app passes deps directly
```

---

## Key Files

| File | Role |
|------|------|
| `haiv-lib/src/haiv/helpers/tui/TuiModel.py` | Raw data sections, TuiModel container |
| `haiv-lib/src/haiv/helpers/tui/protocol.py` | ModelClient protocol (unites remote + local) |
| `haiv-lib/src/haiv/helpers/tui/helpers.py` | TUI logic: sessions_refresh, active_mind_set, mind_launch |
| `haiv-lib/src/haiv/helpers/tui/recent_files.py` | Gather recent files: git ls-files + git diff --numstat |
| `haiv-lib/src/haiv/helpers/tui/terminal.py` | WezTerm abstraction |
| `haiv-lib/src/haiv/helpers/utils/file_watcher.py` | Debounced file watcher (write events only) |
| `haiv-lib/src/haiv/_infrastructure/TuiServer/` | Server, IPC, dirty tracking, freeze |
| `haiv-tui/src/haiv_tui/_runner.py` | Entry point — os.execv restart, crash logging |
| `haiv-tui/src/haiv_tui/app.py` | HaivApp + _Workers (background threads) |
| `haiv-tui/src/haiv_tui/recent_files_worker.py` | Background: watches worktrees/, gathers on change |
| `haiv-tui/src/haiv_tui/store.py` | Signal dispatch from dirty set |
| `haiv-tui/src/haiv_tui/widgets/recent_files.py` | Recent files list + age coloring + shortest unique names |
| `haiv-tui/src/haiv_tui/widgets/sessions.py` | Sessions tree + action bar + DTOs + assembly |
| `haiv-tui/src/haiv_tui/widgets/hud.py` | HUD: always-visible session panel |
| `haiv-tui/src/haiv_tui/widgets/debounce_button.py` | Reusable button with configurable debounce cooldown |
| `haiv-tui/tests/harness.py` | Shared test harness: WidgetTestApp, mock factories |

---

## Known Issues

- **Shutdown hang** — file watcher thread join blocks on quit. `os.execv` restart works. Quit needs Ctrl+C after.
- **Manual prompting for hv pop** — minds need to be told to run it
- **No push in close-out** — base branch not pushed after merge; acceptable for now
- **Minds don't commit haiv-hq content** — pop handles worktree branch but atlas/state lives on haiv-hq
- **Textual `disabled` reactive shadows** — custom widgets cannot define a `disabled` property; must use `watch_disabled()`.
- **Textual `_render` override** — never name a method `_render` on a widget. See atlas.
