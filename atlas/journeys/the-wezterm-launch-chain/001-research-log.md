# 001 — Research Log

**Explorer:** wren
**Date:** 2026-03-30
**Goal:** Trace the full execution path from `hv start` to running Claude Code sessions inside WezTerm. Understand who spawns what, which processes stay alive, and where a Windows job object could intercept the tree to ensure clean shutdown.

---

## What pulled me here

On Windows, closing WezTerm doesn't kill child processes. Claude Code sessions, the TUI — they all become orphans. The fix should be a job object with `KILL_ON_JOB_CLOSE`, but we need to understand the process tree first. Who is the parent of what? Does `wezterm cli split-pane` create children of the calling process, or does the WezTerm server spawn them? The answer determines where the job object goes.

## What I searched in the atlas

**Maps:** `haiv-lib/infrastructure/venv-relay.md` covers the new relay architecture but nothing about process lifecycle. No map exists for the TUI launch sequence or WezTerm integration.

**Quest board:** No quests related to process management or WezTerm lifecycle.

**Journeys:** No prior journey through this territory. The TUI data model and hook system have been explored, but not the launch chain.

## What's missing

- The full process tree: launcher → `hv start` → WezTerm → TUI → mind sessions
- Which process spawns which — especially on Windows
- Whether `wezterm cli split-pane` creates children of the caller or the WezTerm server
- Where the TUI process lives in the tree and how long it survives
- The right place to attach a job object (if it's even possible given the tree shape)

## Where I plan to go

1. `src/haiv_project/commands/dev/install.py` — the launcher scripts (bash + .cmd), both used on Windows
2. `haiv-cli/src/haiv_cli/__init__.py` — `main()`, now a pure router that delegates to relay
3. `haiv-core/commands/start/_index_.py` → `ctx.tui.start()` — entry point for the TUI
4. `haiv-lib/helpers/tui/terminal.py` — TerminalManager, WezTerm launch and pane management
5. `haiv-lib/wrappers/wezterm.py` — raw WezTerm CLI wrapper, `run()` vs `run_external()`
6. `haiv-tui/_runner.py` — TUI entry point, the long-lived process
7. `haiv-lib/helpers/tui/helpers.py` — `mind_launch()`, how Claude Code sessions get spawned

Following the full chain from launcher script to running processes. At each step, noting: does this process exit, stay alive, or get replaced? On Windows specifically, which processes survive if WezTerm is closed? That's where the orphans come from.
