# 004 — The Fix

**Explorer:** Ember
**Date:** 2026-03-08

---

## What Changed

Two files, one constant, one new method.

### 1. TUI app sets pane title (`haiv-tui/app.py`)

Added `sys.stdout.write(f"\033]2;{TUI_PANE_TITLE}\007")` to `HaivApp.on_mount()`. This emits an OSC 2 escape sequence that WezTerm picks up as the pane title. Textual doesn't set or clear terminal titles, so the title persists as long as the TUI is alive.

### 2. Detection constant (`haiv-lib/helpers/tui/terminal.py`)

`TUI_PANE_TITLE = "haiv-tui"` — shared between the TUI app (sets it) and the terminal manager (checks for it). Comment explains the full mechanism.

### 3. Refactored `ensure_workspace()` (`haiv-lib/helpers/tui/terminal.py`)

Old logic: hud tab exists → activate, done.

New logic uses two binary signals:
- **Hud tab exists?** — any pane with matching tab_title prefix
- **TUI pane alive?** — a pane in that tab with `title == TUI_PANE_TITLE`

Four branches: not in WezTerm → launch; no hud tab → create window; hud tab + TUI alive → activate; hud tab + no TUI → recover.

### 4. Recovery method `_recover_tui()`

Splits the surviving pane to the **left** with the TUI command. This guarantees the new TUI pane is leftmost regardless of what else exists in the tab. Simple, handles any state of remaining panes.

## Key design decision

We don't try to detect fine-grained state (is the split intact? is the bare shell from a crash or deliberate?). Two binary signals — tab exists, TUI pane exists — are all we can know with certainty, and they're enough.
