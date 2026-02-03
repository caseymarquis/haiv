# Task Assignment

**Implement `mg start` for WezTerm workspace management**

Build the user-facing `mg start` command (no arguments) that sets up the WezTerm workspace for the current project.

---

## Context

We're transitioning from tmux to WezTerm for cross-platform support. Each mg project gets its own WezTerm workspace, with a standard tab layout for managing minds.

The `mg start` command (no args) is distinct from `mg start <mind>`:
- `mg start` - User startup: ensures workspace exists, launches TUI
- `mg start <mind>` - Mind startup: spawns a specific mind (existing behavior)

---

## Behavior: `mg start` (no arguments)

When a user runs `mg start` from within an mg-managed repo:

1. **Determine workspace name** from the repo folder (e.g., "mind-games")

2. **Check if workspace exists** in WezTerm
   - If yes: focus it
   - If no: create it with the standard tab layout

3. **Standard tab layout:**
   - `mg-hud` tab: Left pane runs the Textual TUI (`mg-tui`), right pane is for active mind
   - `mg-buffer` tab: Staging area for inactive mind panes

4. **End state:** User is looking at the TUI, ready to work

---

## Implementation Notes

- The `mg start` command should be a thin wrapper
- Core logic lives in `mg/helpers/tui/`
- Use the WezTerm wrapper (`ctx.wezterm`) for all WezTerm operations
- WezTerm command is configured in `mg.toml`, not hardcoded

---

## WezTerm Operations You'll Need

The wrapper provides these (see `mg_core.helpers.wezterm`):
- `list_panes()` - includes workspace info
- `spawn()` - create panes, `--workspace` flag for workspace creation
- `split_pane()` - create the hud layout
- `set_tab_title()` - label tabs as mg-hud/mg-buffer
- `activate_pane()` - focus the TUI pane

---

## Success Criteria

- Running `mg start` from a project creates/focuses the workspace
- Workspace has mg-hud and mg-buffer tabs
- TUI is running in mg-hud left pane
- User lands in the TUI ready to navigate

---

## Out of Scope

- Mind spawning (`mg start <mind>` is separate)
- TUI functionality (that's a separate task)
- The TUI just needs to launch - it can be the basic skeleton for now
