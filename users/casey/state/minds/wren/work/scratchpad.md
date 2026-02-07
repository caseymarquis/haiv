# Scratchpad

Rough thinking, debugging notes, half-formed ideas.

---

## Current Session Notes

### WezTerm pane management findings (2026-02-07)

Live-tested the full launch flow with Casey. Bugs found and fixed:

1. **`spawn(window_id=...)` creates a new tab**, not a pane in an existing tab. Use `split_pane` to create within a tab.
2. **`send_text` uses bracketed paste** by default — newline doesn't trigger Enter. Use `no_paste=True`.
3. **No `activate_pane` call** — focus stayed on whichever tab was last touched. Must explicitly activate.
4. **`move_pane_to_new_tab` always creates a new tab** — can't move into an existing tab. Drove the switch from buffer-tab to per-mind-tab design.
5. **Focus flash on spawn** — `spawn` auto-focuses the new tab. Fixed by splitting the existing mind pane instead of spawning a staging tab. No tab creation = no focus jump.

**Final working flow (no-flash):**
- If mind pane exists: split it → new pane appears in hud, move old pane out to `~mind` tab
- If no mind pane: split TUI pane directly
- `send_text --no-paste` for commands, `activate_pane` to ensure focus, `set_tab_title` for naming

**User vars don't work** for pane identity on this WezTerm version — `wezterm cli list --format json` doesn't include them. Per-mind tab titles solve the same problem.

### Open questions

- **Session completion:** How does a session end normally? Mind marks itself done? Parent reviews AAR and archives? Need a `mg sessions complete` or similar. Second priority after TUI actions.
- **TUI action model:** Should the TUI shell out to `mg start` or call TerminalManager directly? Shelling out keeps domain logic in commands. Calling directly avoids subprocess overhead.
- **Archiving:** Deferred. Currently `create_session` just removes old session for the mind. If we need history, design archiving later.

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
- **Tab naming convention**: `mg({project}):mind` for hud with active mind, `~mind` for parked. Project prefix only needed on hud (parked tabs found by window_id). `:` = active, `~` = parked.
- **No buffer tab**: Each parked mind gets its own tab. Simpler than a shared buffer, and tab titles give identity for free.
- **Split-in-place for no-flash swap**: Split the current mind pane to create the new one (stays in hud), then move old pane out. Avoids spawning a staging tab which auto-focuses.

## Things to Remember

- Use `claude "prompt"` syntax, not separate Enter key
- AARs go in `temp-aar/`
- Can skip formal process for simple/urgent tasks, write welcome docs directly
- `flatpak run org.wezfurlong.wezterm` is the wezterm command on this system
- `mg tui debug` shows WezTerm pane layout — useful during pane management work
- WezTerm `send_text` needs `--no-paste` for commands to execute
- WezTerm user vars not in `list --format json` output (at least on flatpak version)
