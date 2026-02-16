# Immediate Plan

**Updated:** 2026-02-14

---

## Current Focus: Role Evolution & Visibility

Delegation loop is mature. Now evolving the platform: role-appropriate launch experiences, live mind status, smarter TUI.

Run `mg sessions` to see current active work.

---

## Active Initiatives

- **Mind launch settings** — spark [4]: `settings.toml` per mind, starting with `launch.system_prompt` to give strategic minds a lighter Claude Code experience. Exploring with Casey.

---

## Next Up

- **Live mind status via Claude Code hooks** — spark's research (temp-aar/claude-hook-integration.md) mapped all lifecycle events. Plumbing → TUI status → leaf prioritization → idle automation.
- **TUI leaf sorting** — recently active leaves float to top (stacked trees → operate at leaves)
- **Idle timeout automation** — trigger summaries when a mind sits idle too long
- **Guided close-out prompting** — `mg pop` checklist creates TODOs, mind works through them

---

## Recently Completed

- Hook system (`mg_hooks`) — typed hook points, lazy discovery, fault-tolerant loading
- `uv sync` auto-runs on worktree creation (quiet mode)
- Active mind indicator in TUI (highlight background)
- Git branch stats in TUI sessions (ahead/behind, dirty/clean)
- `mg pop` command with merge, cleanup-only mode, session removal, work/ wipe
- Parent-child tree display in `mg sessions` CLI and TUI
- Non-destructive `scaffold_mind` with `skip_existing` for reused minds
- Welcome template now includes discussion-first guidance
- Staging: always worktree, auto-detect base branch, clean tree enforcement

---

## Lessons Learned

- Check live state via `mg sessions`, don't maintain worker tables in notes — they go stale between interactions
- Time is paused between interactions. Design for clear handoffs, not speed.
- Task descriptions: describe the landscape and destination, not the route
- Always worktree, always commit first — one path, clean branch points
- Push regularly — safety net for main
- Research deliverables should go in `temp-aar/`, not `work/` — `work/` gets wiped on pop

---

## Architecture

```
mg commands:  ctx.tui.mind_launch(mind)       # facade assembles deps
TUI app:      helpers.mind_launch(term, ...)   # app passes deps directly
```

- **helpers.py** — all domain logic as standalone functions, explicit deps
- **tui.py (Tui class)** — thin facade, one-line passthroughs to helpers
- **terminal.py (TerminalManager)** — WezTerm abstraction, nothing leaks
- **sessions.py** — `resolve_session()` always succeeds (crash recovery friendly)
- **hooks.py** — `HookPoint[TReq]`, `@mg_hook` decorator, lazy discovery via `configure()`

---

## Key Files

| File | Role |
|------|------|
| `mg/src/mg/mg_hooks.py` | Hook public API: HookPoint, @mg_hook, configure |
| `mg/src/mg/helpers/tui/helpers.py` | All TUI logic |
| `mg/src/mg/helpers/tui/terminal.py` | WezTerm abstraction |
| `mg/src/mg/helpers/sessions.py` | Session model, CRUD |
| `mg-core/src/mg_core/commands/pop.py` | Session close-out |
| `mg-core/src/mg_core/commands/minds/stage.py` | Staging |
| `mg-tui/src/mg_tui/widgets/sessions.py` | Sessions tree widget |

---

## Known Issues

- **Manual prompting for mg pop** — minds need to be told to run it
- **No push in close-out** — base branch not pushed after merge; acceptable for now
