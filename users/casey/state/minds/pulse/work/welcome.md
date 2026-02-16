# Task Assignment

**Fix: TUI not updating when new mind launches**

When `mg start` launches a new mind, the TUI sessions tree doesn't refresh to show the new active session. The session is written to `sessions.ig.toml` but the TUI doesn't reflect it until manually refreshed.

**Location:** `worktrees/pulse/`

---

## Context

The TUI displays sessions via a `SessionsSection` in the `TuiModel`, updated through IPC (`TuiClient.write()`). When `mg minds stage` creates a session, it likely updates the TUI model. When `mg start` transitions a session from "staged" to "started", something similar should happen — but it seems like the TUI update is missing.

## Key files

- `mg-core/src/mg_core/commands/start.py` (or similar) — the start command
- `mg-core/src/mg_core/commands/minds/stage.py` — compare how stage updates the TUI
- `mg/src/mg/helpers/tui/helpers.py` — TUI domain logic
- `mg/src/mg/helpers/tui/TuiClient.py` — IPC client for writing model updates
- `mg/src/mg/helpers/tui/TuiModel.py` — `SessionEntry` and `SessionsSection`

---

## Success Criteria

- After `mg start {mind}`, the TUI sessions tree updates to show the new/updated session
- No regression to existing TUI update behavior

---

## Before You Begin

Read the full assignment, then discuss your understanding and approach with your human collaborator before writing code. The task description is a starting point — not a spec. Do not use planning tools unless your human explicitly requests it. You work best together.
