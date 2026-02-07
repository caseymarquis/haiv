# Scratchpad

Rough thinking, debugging notes, half-formed ideas.

---

## Current Session Notes

### Session redesign thinking (2026-02-07)

Key insight from Casey: **derive, don't store.** Mind status is inferred from session state — no separate mind status field that can go stale. Commands naturally transition session states (stage creates, start activates), so the lifecycle is maintained by the tools themselves.

Session staleness is bounded: a staged session that never starts is visible in the TUI as something the human can investigate. Better than a hidden status buried in a file.

**One session per mind** simplifies everything. `mg start spark` just finds spark's session. No ambiguity. `mg minds stage` already only picks minds without active sessions, so the constraint is naturally respected.

**Why not auto-resume Claude sessions:** Casey has experienced corruption issues with native Claude session resume. When a session is corrupted, auto-resume creates nasty loops. Safer to always start fresh with `mg become` loading the mind's notes. Manual `/resume` available when the user knows the session is clean.

**TuiClient, not file watching for session updates:** Commands push changes directly via `ctx.tui.write()`. More consistent when we start working with data that doesn't live on disk. File watching (watchdog) still used for other things, but session state goes through the TuiClient.

### Open questions / things to figure out during implementation

- **Archive storage:** Separate file (`sessions-archive.ig.toml`)? Or same file with status=archived filtered out of active views? Separate file is cleaner for the one-session-per-mind constraint.
- **Session completion:** How does a session end normally? Mind marks itself done? Parent reviews AAR and archives? Need a `mg sessions complete` or similar. Not blocking for initial implementation — can add later.
- **WezTerm pane spawning from `mg start`:** Need to figure out the exact wezterm CLI calls. `ctx.wezterm` helper exists but need to check what it supports.
- **What happens if TUI isn't running when `mg start` is called?** The `ctx.tui.write()` will raise `ConnectionError`. Should we catch and warn, or require TUI? Casey said "we should always have a TUI up" — so probably error is fine.

## Architecture Decisions Made

- **helpers.py pattern**: Standalone functions with all deps as params. Tui class is thin wrapper only. Keeps TUI app decoupled from dependency bag.
- **Naming convention**: `noun_verb` in helpers (sessions_refresh, errors_append) for sorting
- **Poll model**: Textual polls model at 100ms via set_interval. No cross-thread callbacks. Avoids deadlock where model thread calls back into Textual.
- **Version-based diffing**: TuiStore compares `_version` ints per section. Cheaper than value equality, race-free.
- **Internal errors**: deque(maxlen=5) on app, separate from model errors. Store subscriber errors routed via error_sink callback. ErrorsWidget always visible, collapses when empty.
- **Session display**: Task-first ("task (mind)"), not mind-first. Humans remember what was happening, not who was doing it.
- **Session descriptions**: Commit convention — `task` is the short summary (title), `description` is the long-form body.
- **Tabbed layout**: No sidebar/main split. Full-screen tabs (Sessions, Session detail, Plans, future tabs). Tab/Shift+Tab to navigate. Terminal pane lives in WezTerm, not the TUI. Uses Textual's TabbedContent with tabs docked to bottom.
- **Focus-mode via tabs**: Each tab owns the full viewport. Switching tabs is the focus mode. No resizable split panes.
- **Thin main()**: `__init__.py:main()` is just the restart loop. All logic in MindGamesApp so Ctrl+R picks up changes.
- **File watching**: watchdog for event-driven filesystem monitoring. Watcher thread reads file, posts Textual message, widget updates on UI thread. No polling.

## Things to Remember

- Use `claude "prompt"` syntax, not separate Enter key
- AARs go in `temp-aar/`
- Can skip formal process for simple/urgent tasks, write welcome docs directly
- `flatpak run org.wezfurlong.wezterm` is the wezterm command on this system
