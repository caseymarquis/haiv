# Immediate Plan

**Updated:** 2026-02-03

---

## Current Focus: Get Delegation Working via TUI

We're bootstrapping the TUI until we can delegate again. Working collaboratively with Casey — extending the HUD to fill gaps as we encounter them.

---

## What's Done (This Session)

1. **Session index** - `sessions.ig.toml` has wren's session entry
2. **`mg start <mind> --tui`** - Creates session if none exists, starts claude with session tracking
3. **TUI architecture rework:**
   - `helpers.py` — standalone functions, all real logic, no implicit state
   - `tui.py` — thin wrapper for command author ergonomics (no logic)
   - `_base.py` — `TuiModelSection` (fixed circular import) + `ModelClient` protocol
4. **TuiModel sections** - `SessionsSection`, `ErrorsSection` added
5. **Poll-based threading** - Replaced deadlocking `on_change` callback with `set_interval` poll loop (100ms). Textual thread pulls state, model thread never calls back.
6. **Version-based diffing** in TuiStore — compares `_version` ints, not values. Race-free.
7. **Error handling** - `internal_errors` deque on app (max 5), store subscriber errors caught via `error_sink` callback
8. **SessionsWidget** - Subscribes to `sessions_changed`, renders `task (mind)` tree entries

## What's Done (Previous Sessions)

1. **WezTerm wrapper** - `mg.wrappers.wezterm` wraps the CLI, accessible via `ctx.wezterm`
2. **mg-tui package** - `worktrees/main/mg-tui/` with Textual app
3. **WezTerm workspace** - TerminalManager creates hud tab + buffer tab
4. **TuiServer** - IPC server with optimistic concurrency, local + remote clients

---

## In Progress

### Finish session display in sidebar
- Wire entry point: `get_mg_root` + `detect_user` → `Paths` → pass to app
- Test live with reload hotkey
- Should see "Figure out how to start delegating again (wren)" in sidebar

---

## What's Next

### 1. Select session → populate HUD
- Click/keyboard select in sidebar shows session details in HUD panel
- Mind name, task, session start time

### 2. Start minds from TUI
- `mg minds stage` creates a session entry
- `mg start <mind> --tui` spawns in a WezTerm pane
- New session appears in sidebar

### 3. Mind switching
- Select session in sidebar → swap panes between hud and buffer tabs
- Active mind's pane visible, others parked in buffer

### 4. Session data integration
- Read `~/.claude/projects/.../sessions-index.json`
- Auto-populate summaries for human context recovery

---

## Active Minds

| Mind | Task | Status |
|------|------|--------|
| wren | Figure out how to start delegating again | Active (this session) |
| spark | WezTerm wrapper | Staged in `_new/`, ready to start |
| sage | `mg minds suggest_role` | Paused, WIP committed |

---

## Previous Work (Still Valid)

- Folder structure: `work/` + `home/` (implemented)
- Terminology: "assign" not "spawn" (implemented)
- `mg become` loads from `work/` + `home/` (implemented)
