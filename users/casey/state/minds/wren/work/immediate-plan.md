# Immediate Plan

**Updated:** 2026-03-29

---

## Current Focus: Stabilize for Scale

haiv-mail is live — first external library integrated as a command source. All packages on PyPI at v0.2.2. The immediate work is getting the dependency story solid and battle-testing haiv-mail so we have a reliable foundation.

After that: the strategic pivot. The 1M context window changes everything about how we manage context. Instead of building elaborate context management infrastructure, we keep work units small enough that context isn't a problem. The interesting questions become architectural: decoupled architectures, context isolation, whether teams should share repos or maximize isolation with separate ones. haiv-mail (cross-colony communication) is the natural testbed for these ideas.

Run `hv sessions` to see current active work.

---

## Active Initiatives

- **haiv-mail integration** — first external library as command source. Commands discovered under `mail` prefix. Mailing lists, DMs, contacts. Needs real-world use to shake out issues.
- **PyPI publishing** — all packages at v0.2.2. `hv publish <package>` commands with tag check and keyring auth.
- **TUI** — activity tree, command queue, bounce/restart, claude hooks integration all live. Stable, not actively developing.

---

## Next Up

### Foundation (before the pivot)

- **[P1] Dependency audit** — dependency graph was built for git-clone + dev-install. Two venvs (project root vs worktrees/main), `uv.toml` sources overriding PyPI with local editables, lock files pinning stale versions. Goal: `uv sync --upgrade-package haiv-mail` just works.
- **[P2] Correct venv per command** — wire VenvResolver into the CLI so every command launches in the right venv automatically. Protocol and integration tests exist. Need the intercept in `_find_command` → `load_command` path.
- **[P3] `uv tool install` workflow** — evaluate whether end users can install haiv via `uv tool install haiv` for clean single-command setup.

### Strategic direction (after foundation)

- **Context isolation patterns** — how do separate teams work in the same repo? Can they? Should we use separate repos to maximize isolation? haiv-mail is the testbed.
- **Decoupled architecture** — push toward designs where components can be developed, tested, and deployed independently.

### Backlog

- **Bounce toggle** — half-implemented (Session.bounce field exists, `hv tui bounce` filters by it). Needs completion or cleanup.
- **Mail in TUI** — surface message state (unread counts, who's waiting).
- **Permission queue via hooks** — route approval decisions to TUI. Speculative.

---

## Recently Completed

- **Closed stale sessions** (2026-03-29) — Removed echo [6], spark [4], sage [3]. Echo's hook work was completed by wren. Spark's mind-launch settings weren't needed. Sage's suggestion system deprioritized.
- **Cross-colony infrastructure** (2026-03-27–29) — Founded haiv-mail colony with mind 仁. Published all haiv packages to PyPI (v0.2.2). Built `hv publish` commands. Integrated haiv-mail as command source in CLI. VenvResolver protocol. `try_with_client` on Tui facade. Init command auto-creates user and hooks config. Symlink support in command discovery.
- **Claude Code hooks integration** (2026-03-25) — End-to-end hook pipeline: CLI → IPC → TUI. ClaudeHooksWorker, Hooks tab, live session status.
- **TUI command queue** (2026-03-24) — Typed command channel, CommandDispatcher, bounce/restart wired end-to-end.
- **Activity tree redesign** (2026-03-24) — Categorized Tree widget, git status gatherer, age display, recent commits section.

---

## Lessons Learned

- Check live state via `hv sessions`, don't maintain worker tables in notes — they go stale between interactions
- Time is paused between interactions. Design for clear handoffs, not speed.
- Task descriptions: describe the landscape and destination, not the route
- Always worktree, always commit first — one path, clean branch points
- Push regularly — safety net for main
- Research deliverables should go in `temp-aar/`, not `work/` — `work/` gets wiped on pop
- After folder renames, nuke `.venv/` and `uv sync` fresh — hardlinked venvs point to old paths
- **Explicit writes, forgiving reads** — always write all fields when serializing. Tolerate missing on read with defaults.
- **Keep git's forward-slash paths untouched** — don't round-trip through `Path` on Windows.
- **Never override `_render` on Textual widgets** — it's an internal method.
- **Watchdog fires on open/close events** — filter to created/modified/moved/deleted.

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

---

## Key Files

| File | Role |
|------|------|
| `haiv-lib/src/haiv/helpers/tui/TuiModel.py` | Raw data sections, TuiModel container |
| `haiv-lib/src/haiv/helpers/tui/protocol.py` | ModelClient protocol |
| `haiv-lib/src/haiv/helpers/tui/helpers.py` | TUI logic: sessions_refresh, active_mind_set, mind_launch |
| `haiv-lib/src/haiv/helpers/tui/commands.py` | Typed command payloads + helper functions |
| `haiv-lib/src/haiv/_infrastructure/venv_resolver.py` | VenvResolver protocol |
| `haiv-lib/src/haiv/helpers/packages.py` | Package discovery — core, installed, project, user |
| `haiv-tui/src/haiv_tui/app.py` | HaivApp + workers + CommandDispatcher wiring |
| `haiv-tui/src/haiv_tui/_runner.py` | Entry point — os.execv restart, crash logging |

---

## Known Issues

- **Shutdown hang** — file watcher thread join blocks on quit. `os.execv` restart works. Quit needs Ctrl+C after.
- **Minds don't commit haiv-hq content** — pop handles worktree branch but state lives on haiv-hq.
- **Type checker noise** — dynamic `setattr` signals on TuiStore cause 16 `unresolved-attribute` diagnostics.
