# AAR: Research: notify running Claude instances of external events

## Summary

Researched how to notify a running Claude Code session when an external event occurs (e.g., a child mind finishing work). Investigated Claude Code hooks, terminal injection, and MCP. Arrived at a simple, elegant solution: `mg pop` scaffolds an AAR in the parent mind's directory, then injects a pre-filled prompt into the parent's terminal pane without submitting — the human reviews and sends when ready.

### Deliverables

- Research findings on all 14 Claude Code hook events and their content injection capabilities
- Implementation: `Session.as_filename()` for filesystem-safe AAR naming
- Implementation: `TerminalManager.send_text_to_mind()` / `try_send_text_to_mind()` for terminal text injection
- Implementation: `mg pop` AAR scaffolding (template creation) and parent notification on `--session`

## Key Decisions

- **Simple over clever** — rejected hook-based notification infrastructure (Stop hooks, PostToolUse injection, etc.) in favor of typing a prompt into the parent's terminal. No hooks, no signal files, no loop guards.
- **Human stays in control** — prompt is typed but not submitted. The human sees it, can edit it, and submits when ready. The "unhappy path" (human dismisses it) is still happy — they just ask about AARs later.
- **AAR lives in parent's directory** — `{parent_mind}/work/aars/{sanitized_task}.md`, not a shared `temp-aar/`. The report is directed at the parent.
- **Template scaffolded on `mg pop`** — created automatically with `skip_existing`, so re-running pop doesn't overwrite a partially filled AAR.
- **Two-function pattern for pane operations** — `try_send_text_to_mind` returns bool, `send_text_to_mind` raises. Pop uses `try_` since the parent pane may not exist.
- **Delegated implementation** — three isolated work packages run across two workers (nimbus, pulse) in parallel where possible.

## Open Items

- **First real-world test pending** — this pop session will be the first live trial of the notification injection
- **AAR reading process** — no formal process yet for how parents interpret and act on AARs. Running with it for now.
- **`temp-aar/` migration** — 17 existing AARs predate this system, could be migrated or archived
- **Process gap: testing mg commands from worktrees** — workers can't run modified `mg` commands during development, only the installed version
- **Mocks need `spec=` everywhere** — discovered that `MagicMock` silently allows calls to nonexistent methods, which hid a naming mismatch between `pop.py` and `Tui` (`try_send_text_to_mind` vs `mind_try_send_text`). Tests passed but the command crashed at runtime. All mocks across the test suite should use `spec=ClassName` (or `spec_set=`) to constrain them to real interfaces. This is a codebase-wide issue, not just pop.

### Side fix

Cleared `CLAUDECODE` env var in `generate_mind_name()` subprocess call so `mg minds stage` works from inside a Claude Code session. (`mg/src/mg/helpers/minds.py:386`)

## Commits and Files Changed

- d3b778b feat(mg): add Session.as_filename() for filesystem-safe task names
- 58c31b1 feat: add send_text_to_mind methods to TerminalManager and Tui
- 240efe2 feat(pop): scaffold AAR in parent mind and notify on wind-down
  Key files: pop.py, aar.md.j2, terminal.py, tui.py, helpers.py, sessions.py, paths.py
