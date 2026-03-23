# Immediate Plan

**Updated:** 2026-03-23

---

## Current Focus: Action Bar Clickable, Hot Reload Broken

Action bar converted from static text to clickable `DebounceButton` widgets. Buttons work, debounce prevents double-clicks. Moved bar between tree and preview. 53 TUI tests.

Hot reload (Ctrl+R) is broken. Isolated the reload loop into `_runner.py` (outside module flush blast radius), added crash/exit logging to `~/.cache/haiv/last-{crash,exit}.log`. Neither log fires — suggesting the entry point isn't reaching `_runner.py` (likely needs `uv sync` in the right venv). **Next step:** run `uv sync` in haiv-tui's venv, restart TUI, reproduce, check logs.

Run `hv sessions` to see current active work.

---

## Active Initiatives

- **TUI feature buildout** — action bar done, hot reload fix in progress. More session actions to come.
- **Relay infrastructure** — unbuilt. Required for haiv to manage external projects (e.g., dnd at `/home/casey/code/dnd/`). The problem: `hv` always runs in haiv-cli's venv, but project/user commands need the project's own venv and dependencies.

---

## Next Up

- **Fix hot reload** — entry point now `haiv_tui._runner:main`, needs `uv sync`. If logs still empty, investigate whether Textual's internal state survives module flush.
- **Type-safe signal subscriptions** — derive signal names from TuiModel fields via reflection, not raw strings
- **TUI publish mechanism** — publish derived state (active mind, etc.) for consumption by `hv` commands
- **Live mind status via Claude Code hooks** — spark's research (temp-aar/claude-hook-integration.md) mapped all lifecycle events. Now that `ActiveMindRaw` exists, hook integration has a natural target.
- **CLAUDE.md clarification** — command search order is user → project → core (highest precedence first), but CLAUDE.md describes it as "haiv_core → haiv_project → haiv_user". Luna flagged this in her AAR. Should be clarified.
- **Clean up stale sessions** — echo [7] and spark [4] are 26+ commits behind main (pre-rename). Close out rather than merge.
- **TUI leaf sorting** — recently active leaves float to top
- **Relay infrastructure** — design settled, unbuilt
- **`pip install haiv` user story** — meta-package exists, UX not worked out
- **Mind launch settings** — `settings.toml` per mind, starting with `launch.system_prompt`

---

## Recently Completed

- **Action bar → clickable buttons** (2026-03-23) — replaced static `[e] Explorer [v] Editor` text with `DebounceButton` widgets. New reusable `DebounceButton` widget (configurable cooldown, composes a `Button`, disables briefly after press). Removed `e`/`v` keybindings. Moved bar between tree and preview. 8 new debounce tests, 53 TUI tests total.
- **TUI crash/exit logging** (2026-03-23) — `_runner.py` isolated from reload. Writes `~/.cache/haiv/last-crash.log` (traceback) and `last-exit.log` (return code) with no dependencies.
- **Widget DI + test harness + action bar** — widgets take deps as keyword-only constructor params (no more `self.app`). HaivApp takes deps/server/client via constructor; main() factory for hot-reload. Shared test harness (`WidgetTestApp`), per-widget test files merging assembly + widget tests. 44 TUI tests, 1021 total.
- **TUI data model redesign** — separated raw data (sessions, git, active mind) from display assembly. New `write_raw()` API, dirty-set change tracking, DTOs co-located with widgets, 17 new TUI assembly tests. Git branch flakiness structurally fixed. haiv-tui added to test-all.sh and type-all.sh. (994 tests total, all green)
- **PyPI name claim** — haiv, haiv-lib, haiv-core, haiv-cli, haiv-tui all published at 0.1.0, tagged v0.1.0
- **haiv → haiv-lib rename** — package renamed, folder renamed, imports unchanged
- **haiv meta-package** — depends on haiv-cli + haiv-tui
- **Atlas system** — Luna built exploration framework, `hv chart` command, maps, quests, rewards
- **mg-* cleanup** — removed dead mg/, mg-cli/, mg-core/, mg-tui/ from main worktree
- **type-all.sh / test-all.sh fixes** — updated for haiv-lib rename
- **Remote URL update** — mind-games.git → haiv.git
- **Pop notification fix** — now tells parent mind work is already reviewed and merged
- **mg → haiv rename** — full rename across all packages, CLI, CLAUDE.md
- Hook system, TUI, `hv pop`, session tree display (older)

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

---

## Architecture

### TUI Data Flow
```
Raw data sources → TuiModel (per-source sections) → TuiServer (dirty tracking)
    → poll loop drains dirty → TuiStore fires signals → widgets rebuild from DTOs
```

- **TuiModel** — raw sections only: `SessionsRaw`, `GitRaw`, `ActiveMindRaw`. Plain dataclasses, no base class.
- **write_raw()** — callers pass section kwargs. Server replaces non-None sections, marks dirty. No concurrency errors.
- **TuiServer** — `Atom<set[str>>` dirty tracking. `drain_dirty()` for atomic poll-loop consumption.
- **TuiStore** — fires blinker signals for dirty sections. Widgets subscribe.
- **Widgets** — receive deps via keyword-only constructor params. Hold latest raw sections, call pure assembly functions (raw→DTO), render DTOs. Subscribe to store signals in `on_mount()`.
- **DTOs + assembly** — co-located at bottom of each widget file. Testable without Textual. Assembly computes full paths (e.g. `worktree_path`) so widgets stay UI-only.
- **HaivApp** — takes `HaivDeps`, `TuiServer`, `TuiLocalClient` via constructor. `main()` holds the factory, re-creates on restart for hot-reload.

### Command Side
```
hv commands:  ctx.tui.mind_launch(mind)       # facade assembles deps
TUI app:      helpers.mind_launch(term, ...)   # app passes deps directly
```

- **helpers.py** — all domain logic as standalone functions, explicit deps
- **tui.py (Tui class)** — thin facade, one-line passthroughs to helpers
- **terminal.py (TerminalManager)** — WezTerm abstraction, nothing leaks
- **sessions.py** — `resolve_session()` always succeeds (crash recovery friendly)
- **hooks.py** — `HookPoint[TReq]`, `@haiv_hook` decorator, lazy discovery via `configure()`

---

## Key Files

| File | Role |
|------|------|
| `haiv-lib/src/haiv/helpers/tui/TuiModel.py` | Raw data sections, TuiModel container |
| `haiv-lib/src/haiv/helpers/tui/protocol.py` | ModelClient protocol (unites remote + local) |
| `haiv-lib/src/haiv/helpers/tui/helpers.py` | TUI logic: sessions_refresh, active_mind_set, mind_launch |
| `haiv-lib/src/haiv/helpers/tui/terminal.py` | WezTerm abstraction |
| `haiv-lib/src/haiv/_infrastructure/TuiServer/` | Server, IPC, dirty tracking, freeze |
| `haiv-tui/src/haiv_tui/store.py` | Signal dispatch from dirty set |
| `haiv-tui/src/haiv_tui/widgets/sessions.py` | Sessions tree + DTOs + assembly |
| `haiv-tui/src/haiv_tui/widgets/hud.py` | HUD widget + DTOs + assembly |
| `haiv-lib/src/haiv/helpers/sessions.py` | Session model, CRUD |
| `haiv-lib/src/haiv/helpers/open.py` | Open dirs in explorer/editor (cross-platform) |
| `haiv-lib/src/haiv/haiv_hooks.py` | Hook public API |
| `haiv-tui/src/haiv_tui/_runner.py` | Entry point — reload loop, crash logging (outside blast radius) |
| `haiv-tui/src/haiv_tui/widgets/debounce_button.py` | Reusable button with configurable debounce cooldown |
| `haiv-tui/tests/harness.py` | Shared test harness: WidgetTestApp, mock factories |

---

## Known Issues

- **Hot reload broken** — Ctrl+R crashes TUI silently. `_runner.py` isolates the loop but logs aren't firing yet. Likely needs `uv sync` so entry point resolves to `_runner.py`. May also be Textual internal state not surviving module flush.
- **Manual prompting for hv pop** — minds need to be told to run it
- **No push in close-out** — base branch not pushed after merge; acceptable for now
- **Minds don't commit haiv-hq content** — pop handles worktree branch but atlas/state lives on haiv-hq
- **Textual `disabled` reactive shadows** — custom widgets cannot define a `disabled` property; must use Textual's built-in reactive + `watch_disabled()`. Learned building DebounceButton.
