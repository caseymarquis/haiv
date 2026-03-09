# 001 — Research Log

**Explorer:** Ember
**Date:** 2026-03-07
**Goal:** Understand how `hv start` manages the TUI layout so I can fix crash recovery — when the TUI process dies but its WezTerm pane survives, `hv start` should detect the broken state and restore the layout.

---

## What I Searched For

**Maps:** Checked `maps/haiv-lib.md`. It shows the haiv-lib structure. Relevant entries:
- `helpers/tui/` — listed under "Uncharted." Utility functions for TUI management. This is almost certainly where the layout detection and recovery logic lives (or should live).
- `wrappers/wezterm.py` — also "Uncharted." Wraps the WezTerm CLI. Since `hv start` creates WezTerm panes and splits, this wrapper is how it talks to the terminal.
- `helpers/minds.py` — uncharted, but `hv start` probably interacts with mind state.

**Quest board:** No quests related to `hv start`, TUI layout, or crash recovery. The existing quests (Port City, Resolver Mystery, Context Factory) are about command infrastructure, not TUI management.

**Journeys:** Luna's routing-table journey maps how commands go from text to execution — useful background but doesn't cover `start` specifically. The mind-templates journey covers `hv minds stage`, not `hv start`. No journey has explored the TUI system.

## What's Missing

The atlas has no documentation of:
- The `start` command — where it lives, what it does, how it decides whether to create vs. reuse a layout
- `helpers/tui/` — how TUI state is tracked, what "healthy" vs. "broken" means
- `wrappers/wezterm.py` — the WezTerm API surface available to commands
- How the TUI process itself is launched and managed

## Where I Plan to Go

1. **The `start` command** — find it via routing (probably `haiv-core` or `haiv-project` commands). This is the entry point; I need to see what it currently does when it finds an existing tab.
2. **`helpers/tui/`** — the TUI helper module. This likely has the functions `start` calls to check pane state, create splits, launch the TUI process.
3. **`wrappers/wezterm.py`** — the WezTerm wrapper. I need to know what WezTerm operations are available (listing panes, checking processes, splitting, etc.).
4. **The TUI app itself** — `haiv-tui/` was mentioned on the quest board. I may need to understand how it's launched to know how to relaunch it.

The first three are essential. The fourth depends on what I find — if recovery just means re-running a command in the right pane, I may not need to go deep into the TUI app itself.
