# Immediate Plan

**Updated:** 2026-03-24

---

## Current Focus: TUI Activity Tree + Command Queue

Major session. The HUD's file list became a categorized Tree widget showing pending changes and recent commits. Luna delivered a TUI command queue in parallel — `hv tui restart` and `hv tui bounce` are live. Session bounce eligibility is persisted.

Run `hv sessions` to see current active work.

---

## Active Initiatives

- **TUI feature buildout** — activity tree live (modified/deleted/conflicted/commits), command queue wired, bounce/restart commands working.
- **Relay infrastructure** — unbuilt. Required for haiv to manage external projects (e.g., dnd at `/home/casey/code/dnd/`). The problem: `hv` always runs in haiv-cli's venv, but project/user commands need the project's own venv and dependencies.

---

## Next Up

- **Bounce toggle command** — `hv tui bounce-toggle` or similar, to mark sessions as bounce-eligible/ineligible from the CLI
- **File openers per extension** — `[file_openers]` in `haiv.toml`, default to `code`, per-extension overrides (e.g., `".md" = "typora"`)
- **Type-safe signal subscriptions** — derive signal names from TuiModel fields via reflection, not raw strings
- **Live mind status via Claude Code hooks** — spark's research (temp-aar/claude-hook-integration.md) mapped all lifecycle events. Now that `ActiveMindRaw` exists, hook integration has a natural target.
- **CLAUDE.md clarification** — command search order is user → project → core (highest precedence first), but CLAUDE.md describes it as "haiv_core → haiv_project → haiv_user". Luna flagged this in her AAR. Should be clarified.
- **Clean up stale sessions** — echo [7] and spark [4] are 26+ commits behind main (pre-rename). Close out rather than merge.
- **mind_launch quiet mode** — Luna noted mind_launch prints user-facing messages that are noise for command-driven invocations. Add a `quiet` parameter.
- **Relay infrastructure** — design settled, unbuilt
- **`pip install haiv` user story** — meta-package exists, UX not worked out
- **Mind launch settings** — `settings.toml` per mind, starting with `launch.system_prompt`
- **Shutdown hang** — file watcher thread join blocks on quit. Restart works (os.execv before shutdown) but quit requires Ctrl+C. Need timeout or daemon thread fix.

---

## Recently Completed

- **TUI command queue** (2026-03-24) — Luna built typed command channel alongside write_raw data flow. `TuiCommand` envelope with `TuiCommandType` enum, `CommandDispatcher` with injected handlers, `send_command()` on both local and IPC clients. `hv tui restart` and `hv tui bounce` wired end-to-end.
- **Activity tree redesign** (2026-03-24) — Replaced flat OptionList with Tree widget. Three file categories (conflicted hidden when empty, recently modified, deleted) plus recent commits (collapsed by default, expand for files). Gatherer rewritten: `git status --porcelain` + `git diff HEAD --numstat` instead of scanning all files by mtime. `FileStatus` enum. Age display ("just now", "3m", "1h 2m"). Alphabetical sort, case-insensitive, underscore-ignored.
- **Recent commits section** (2026-03-24) — New `RecentCommitsRaw` model section with `CommitEntry` holding denormalized file lists. Single `git log --numstat` call with null-byte delimiter for reliable parsing. Separate `RecentCommitsWorker` (5s debounce).
- **Session bounce field** (2026-03-24) — `Session.bounce` (default `True`) marks sessions eligible for `hv tui bounce`. Cleaned up `_session_to_dict` to always write all fields — explicit writes, forgiving reads.
- **Windows path fix** (2026-03-24) — `shortest_unique_names` used `PurePosixPath` which can't split backslash paths. Fixed by keeping git's forward-slash strings untouched through the pipeline instead of round-tripping through `Path`.
- **Previous session work** (2026-03-23) — Recent files widget, TUI layout redesign, hot reload fix, action bar buttons, widget DI + test harness, TUI data model redesign.
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
- **Explicit writes, forgiving reads** — always write all fields when serializing. Tolerate missing fields on read with defaults. No conditional writes based on default values.
- **Keep git's forward-slash paths untouched** — `git ls-files` and `git diff` always output forward slashes. Don't round-trip through `Path` (which adds backslashes on Windows). Only convert to `Path` at the point of use.

---

## Architecture

### TUI Layout
```
Header (active mind + task)
├── session-panel (65%)
│   ├── HudWidget (Horizontal)
│   │   ├── SessionActionBar (vertical, left)
│   │   └── hud-content (Vertical, right)
│   │       ├── RecentFilesWidget (Tree)
│   │       │   ├── header Static
│   │       │   ├── Tree (categories → files)
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

Commands → TuiServer (command buffer) → poll loop drains commands → CommandDispatcher → handlers
```

- **TuiModel** — raw sections: `SessionsRaw`, `GitRaw`, `ActiveMindRaw`, `RecentFilesRaw`, `RecentCommitsRaw`. Plain dataclasses, no base class.
- **write_raw()** — callers pass section kwargs. Server replaces non-None sections, marks dirty.
- **send_command()** — typed `TuiCommand` envelope with `TuiCommandType` enum. Drains independently of model updates.
- **TuiStore** — fires blinker signals for dirty sections. Auto-discovered from TuiModel fields.
- **CommandDispatcher** — routes commands to handler callables injected via constructor.
- **Widgets** — receive deps via keyword-only constructor params. Subscribe in `on_mount()`. Assembly is pure functions (raw→DTO), testable without Textual.
- **HaivApp** — takes `HaivDeps`, `TuiServer`, `TuiLocalClient` via constructor.
- **_runner.py** — entry point, restart via `os.execv`, crash/exit logging.
- **_Workers** — background threads (file watcher for sessions, RecentFilesWorker, RecentCommitsWorker).

### Command Side
```
hv commands:  ctx.tui.bounce() / ctx.tui.restart()  # facade → send_command
TUI app:      helpers.mind_launch(term, ...)          # app passes deps directly
```

---

## Key Files

| File | Role |
|------|------|
| `haiv-lib/src/haiv/helpers/tui/TuiModel.py` | Raw data sections, TuiModel container |
| `haiv-lib/src/haiv/helpers/tui/protocol.py` | ModelClient protocol (unites remote + local) |
| `haiv-lib/src/haiv/helpers/tui/helpers.py` | TUI logic: sessions_refresh, active_mind_set, mind_launch |
| `haiv-lib/src/haiv/helpers/tui/commands.py` | Typed command payloads + helper functions |
| `haiv-lib/src/haiv/helpers/tui/recent_files.py` | Gather pending files: git status + git diff |
| `haiv-lib/src/haiv/helpers/tui/recent_commits.py` | Gather recent commits: git log --numstat |
| `haiv-lib/src/haiv/helpers/tui/terminal.py` | WezTerm abstraction |
| `haiv-lib/src/haiv/helpers/utils/file_watcher.py` | Debounced file watcher (write events only) |
| `haiv-lib/src/haiv/_infrastructure/TuiServer/` | Server, IPC, dirty tracking, command buffer, freeze |
| `haiv-core/src/haiv_core/commands/tui/bounce.py` | hv tui bounce — cycle sessions |
| `haiv-core/src/haiv_core/commands/tui/restart.py` | hv tui restart — restart TUI process |
| `haiv-tui/src/haiv_tui/_runner.py` | Entry point — os.execv restart, crash logging |
| `haiv-tui/src/haiv_tui/app.py` | HaivApp + _Workers + CommandDispatcher wiring |
| `haiv-tui/src/haiv_tui/command_dispatcher.py` | Route commands to typed handlers |
| `haiv-tui/src/haiv_tui/recent_files_worker.py` | Background: watches worktrees/, gathers on change |
| `haiv-tui/src/haiv_tui/recent_commits_worker.py` | Background: watches worktrees/, gathers commits |
| `haiv-tui/src/haiv_tui/store.py` | Signal dispatch from dirty set |
| `haiv-tui/src/haiv_tui/widgets/recent_files.py` | Activity tree + age coloring + commits + shortest unique names |
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
- **Type checker noise** — dynamic `setattr` signals on TuiStore cause 16 `unresolved-attribute` diagnostics. Pre-existing, not blocking.
- **mind_launch is chatty** — prints user-facing messages that are noise for command-driven invocations (bounce, etc.)
