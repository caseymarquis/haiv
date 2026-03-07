# Immediate Plan

**Updated:** 2026-03-07

---

## Current Focus: Cross-Project Support & Relay Infrastructure

The mg → haiv rename is complete (see AAR: `work/aars/build-relay-infrastructure-for-cross-venv-f695.md`). The git branch is now `haiv-hq`, CLI is `hv`, all packages renamed (haiv, haiv-core, haiv-cli, haiv-tui, haiv_project, haiv_user). Pixel did the rename; it's merged to main.

Next priority: **relay infrastructure** for running haiv across different project venvs. Core commands run in-process, project/user commands relaunch via `uv run` in the target project's venv. Design is settled (tempfile IPC, stdio passthrough, parent passes routed command file path to child). See the AAR and `work/docs/relay-task.md` for the full task spec and design decisions.

Run `hv sessions` to see current active work.

---

## Active Initiatives

- **Relay infrastructure** — unbuilt. Required for haiv to manage external projects (e.g., dnd at `/home/casey/code/dnd/`). The problem: `hv` always runs in haiv-cli's venv, but project/user commands need the project's own venv and dependencies.

---

## Next Up

- **Clean up stale sessions** — echo [7] and spark [4] are 23 commits behind main (pre-rename). Likely need to be closed out rather than merged.
- **dnd project rename** — still references mg_project/mg_user/mg-state. Low priority since it's just a test project with no real content.
- **Live mind status via Claude Code hooks** — spark's research (temp-aar/claude-hook-integration.md) mapped all lifecycle events.
- **TUI leaf sorting** — recently active leaves float to top
- **Mind launch settings** — `settings.toml` per mind, starting with `launch.system_prompt`

---

## Recently Completed

- **mg → haiv rename** — full rename across all packages, CLI, CLAUDE.md, mg-state content
- **Git branch rename** — mg-state → haiv-hq (local + remote)
- Hook system (`haiv_hooks`) — typed hook points, lazy discovery, fault-tolerant loading
- `uv sync` auto-runs on worktree creation (quiet mode)
- Active mind indicator in TUI (highlight background)
- Git branch stats in TUI sessions (ahead/behind, dirty/clean)
- `hv pop` command with merge, cleanup-only mode, session removal, work/ wipe
- Parent-child tree display in `hv sessions` CLI and TUI

---

## Lessons Learned

- Check live state via `hv sessions`, don't maintain worker tables in notes — they go stale between interactions
- Time is paused between interactions. Design for clear handoffs, not speed.
- Task descriptions: describe the landscape and destination, not the route
- Always worktree, always commit first — one path, clean branch points
- Push regularly — safety net for main
- Research deliverables should go in `temp-aar/`, not `work/` — `work/` gets wiped on pop

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
| `haiv/src/haiv/haiv_hooks.py` | Hook public API: HookPoint, @haiv_hook, configure |
| `haiv/src/haiv/helpers/tui/helpers.py` | All TUI logic |
| `haiv/src/haiv/helpers/tui/terminal.py` | WezTerm abstraction |
| `haiv/src/haiv/helpers/sessions.py` | Session model, CRUD |
| `haiv-core/src/haiv_core/commands/pop.py` | Session close-out |
| `haiv-core/src/haiv_core/commands/minds/stage.py` | Staging |
| `haiv-tui/src/haiv_tui/widgets/sessions.py` | Sessions tree widget |

---

## Known Issues

- **Manual prompting for hv pop** — minds need to be told to run it
- **No push in close-out** — base branch not pushed after merge; acceptable for now
