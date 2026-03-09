# Immediate Plan

**Updated:** 2026-03-07

---

## Current Focus: PyPI Published, Atlas Built, Relay Still Pending

We claimed all five PyPI names: `haiv`, `haiv-lib`, `haiv-core`, `haiv-cli`, `haiv-tui` — all at v0.1.0, tagged. The old `haiv` package was renamed to `haiv-lib` (imports unchanged), and `haiv` is now the meta-package (depends on haiv-cli + haiv-tui). GitHub repo renamed from mind-games to haiv, remote URL updated.

Luna built an atlas system (`atlas/` on haiv-hq) — a mind-driven codebase exploration framework with journeys, maps, quests, and rewards. She also built `hv chart` to brief minds on how to explore. She completed The Routing Table quest and left three open quests plus one mystery.

Next priority: **relay infrastructure** for running haiv across different project venvs. Design is settled (tempfile IPC, stdio passthrough). See `work/docs/relay-task.md`.

Run `hv sessions` to see current active work.

---

## Active Initiatives

- **Relay infrastructure** — unbuilt. Required for haiv to manage external projects (e.g., dnd at `/home/casey/code/dnd/`). The problem: `hv` always runs in haiv-cli's venv, but project/user commands need the project's own venv and dependencies.

---

## Next Up

- **CLAUDE.md clarification** — command search order is user → project → core (highest precedence first), but CLAUDE.md describes it as "haiv_core → haiv_project → haiv_user". Luna flagged this in her AAR. Should be clarified.
- **`pip install haiv` user story** — the meta-package exists but we haven't worked out how a user goes from installing to having `hv` and `hv-tui` commands working.
- **Clean up stale sessions** — echo [7] and spark [4] are 26+ commits behind main (pre-rename). Close out rather than merge.
- **dnd project rename** — still references mg_project/mg_user/mg-state. Low priority.
- **Live mind status via Claude Code hooks** — spark's research (temp-aar/claude-hook-integration.md) mapped all lifecycle events.
- **TUI leaf sorting** — recently active leaves float to top
- **Mind launch settings** — `settings.toml` per mind, starting with `launch.system_prompt`

---

## Recently Completed

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
| `haiv-lib/src/haiv/haiv_hooks.py` | Hook public API: HookPoint, @haiv_hook, configure |
| `haiv-lib/src/haiv/helpers/tui/helpers.py` | All TUI logic |
| `haiv-lib/src/haiv/helpers/tui/terminal.py` | WezTerm abstraction |
| `haiv-lib/src/haiv/helpers/sessions.py` | Session model, CRUD |
| `haiv-core/src/haiv_core/commands/pop.py` | Session close-out |
| `haiv-core/src/haiv_core/commands/minds/stage.py` | Staging |
| `haiv-core/src/haiv_core/commands/chart.py` | Atlas exploration briefing |
| `haiv-tui/src/haiv_tui/widgets/sessions.py` | Sessions tree widget |

---

## Known Issues

- **Manual prompting for hv pop** — minds need to be told to run it
- **No push in close-out** — base branch not pushed after merge; acceptable for now
- **Minds don't commit haiv-hq content** — pop handles worktree branch but atlas/state lives on haiv-hq
