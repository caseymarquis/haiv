# AAR: fix: hv start should recover crashed TUI layout

## Summary

`hv start` now detects and recovers from TUI crashes. The TUI app marks itself alive via a WezTerm pane title, and `ensure_workspace()` checks for that marker. If the hud tab exists but the TUI pane is gone, it splits left with the TUI command to restore the layout.

Beyond the fix, charted the TUI system and hook system for the atlas — two journeys, three new maps, one completed quest.

## Key Decisions

- **Two binary signals for detection** — "hud tab exists?" and "TUI pane alive?" are all we check. We don't try to detect finer-grained state (split intact, which pane crashed, etc.) because we can't know those things with certainty.
- **OSC 2 for pane title** — the TUI app writes `\033]2;haiv-tui\007` on mount. Confirmed via live test that WezTerm picks this up and that the shell resets it after a crash.
- **Split left for recovery** — `_recover_tui()` splits the surviving pane to the left with the TUI command. This guarantees the TUI is leftmost regardless of what else survived.
- **TUI_PANE_TITLE constant shared** — lives in `terminal.py`, imported by both the TUI app and the terminal manager.

## Open Items

### Verification needed

The fix needs manual end-to-end testing: kill the TUI process, run `hv start`, check that the layout is restored. Unit tests cover the logic but not the real WezTerm interaction.

### Atlas work completed alongside

- Journey: `atlas/journeys/hv-start-crash-recovery/` (4 entries)
- Journey: `atlas/journeys/the-hook-system/` (7 entries, completed The Hook System quest)
- New maps: haiv-cli, haiv-core, haiv-tui
- Updated map: haiv-lib (TUI helpers, wezterm wrapper, hook system)

## Commits and Files Changed

- cf0b19e fix: hv start recovers crashed TUI layout
  Key files: terminal.py, test_terminal_manager.py, app.py
- cdbb087 add atlas: TUI crash recovery + hook system journeys, new maps
  16 files across atlas/ and maps/
