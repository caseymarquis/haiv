# 002 — The Start Command and TUI Layout

**Explorer:** Ember
**Date:** 2026-03-07

---

## Why I Came Here

I need to understand how `hv start` creates and detects the TUI workspace so I can fix crash recovery. I read four files: the `start` command itself, the helpers, the terminal manager, and the WezTerm wrapper.

## What I Found

### The command chain

```
hv start
  → commands/start/_index_.py:execute()    ctx.tui.start()
    → helpers.py:workspace_start()         terminal.ensure_workspace()
      → terminal.py:ensure_workspace()     ← the bug lives here
```

`hv start <mind>` is a separate path (`_mind_.py`) that calls `ctx.tui.mind_launch()`. My task is about bare `hv start`.

### ensure_workspace() — the decision tree

Three branches:

1. **Not in WezTerm** → Launch WezTerm with `hv start` (via `wezterm start -- hv start`)
2. **In WezTerm, no hud pane found** → `_create_window()`: spawn new window running TUI command, set tab title, split right 50% for mind pane, focus hud
3. **In WezTerm, hud pane found** → Activate it, print "ready". **This is the bug.**

### How the hud pane is found

`_find_hud_pane()` matches on: `pane.tab_title.startswith("hv({project})") and pane.left_col == 0`

This only checks the tab title and position. It does NOT check whether:
- The TUI process is actually running in that pane
- The split layout exists (right pane for minds)

### The healthy layout (what `_create_window()` builds)

```
Tab: hv(haiv)
┌──────────────┬──────────────┐
│  TUI process │  Empty shell │
│  (left_col=0)│  (mind slot) │
└──────────────┴──────────────┘
```

The TUI is launched via `self.tui_command + [self.project]` passed as `command=` to `wezterm.spawn()`.

### After a TUI crash

```
Tab: hv(haiv)
┌──────────────┬──────────────┐
│  Bare shell  │  Mind pane   │
│  (left_col=0)│  (may exist) │
└──────────────┴──────────────┘
```

The pane survives, the tab title survives, `_find_hud_pane()` finds it. `ensure_workspace()` says "ready" and does nothing.

### Detection possibilities

The `Pane` dataclass has a `title` field (distinct from `tab_title`) — this is the individual pane's title, typically set by the running process. If the TUI sets its own pane title, we could check for it. The `tui_command` is available as `self.tui_command` on the TerminalManager.

We can also count panes per tab — if the split is gone, there'd be only one pane with the hud tab title.

`wezterm.get_text(pane_id)` can read pane contents, but that's fragile for detection.

### WezTerm wrapper API

Available operations relevant to recovery:
- `list_panes()` → detect existing layout
- `spawn()` → can run a command in a new pane
- `split_pane()` → recreate the split, with optional `command=` to launch TUI directly
- `send_text()` → could send a command to an existing bare-shell pane
- `kill_pane()` → clean up a broken pane
- `get_text()` → read pane contents

## What I Don't Know Yet

- How to reliably detect whether the TUI process is running in a pane. The `Pane.title` field might work if the TUI sets it. Need to check what the TUI app does on startup.
- Whether recovery should reuse the existing pane (send TUI command to bare shell) or kill it and recreate.

## Where I'm Going Next

I should check `_base.py` and the TUI app itself (`haiv-tui/`) to understand if the TUI sets a pane title or has any other detectable signature. But first — let me discuss the approach with my human collaborator, because I may already have enough to propose a fix.
