# 003 — Pane Title Detection

**Explorer:** Ember
**Date:** 2026-03-07

---

## Why I Came Here

Needed to find a reliable way to detect whether the TUI process is alive in the hud pane. The hud pane survives a TUI crash (tab title intact, pane still exists), so we need a signal that distinguishes "TUI running" from "bare shell after crash."

## What I Found

### WezTerm pane titles

`wezterm cli list` returns both `tab_title` (set via `set-tab-title`) and `title` (the individual pane title). There's no `set-pane-title` CLI command — pane titles come from **OSC 2 escape sequences** emitted by the process running in the pane: `\033]2;title\007`.

### The shell resets pane titles

The user's shell has PS1/PROMPT_COMMAND that sets the pane title to `casey@casey-lappy: ~/code/haiv` on every prompt. Sending an OSC sequence via `send-text` to a shell pane gets immediately overwritten. This is actually useful for detection — crashed panes revert to the shell's default title.

### Textual doesn't touch pane titles

Searched the entire Textual package — no OSC title sequences. Textual doesn't set or clear pane titles. The current TUI pane shows `title='wezterm'` (WezTerm's default when nothing sets a title).

### Confirmed: OSC 2 works from a process

Spawned a test pane running `python3 -c "sys.stdout.write('\033]2;haiv-tui\007'); ..."`. Result: `hv tui debug` showed `title='haiv-tui'` for that pane. Clean, immediate, reliable.

### The full picture

| State | pane.title |
|-------|-----------|
| TUI running (current) | `'wezterm'` (default, nothing sets it) |
| TUI running (with fix) | `'haiv-tui'` (OSC 2 from on_mount) |
| TUI crashed → bare shell | `'casey@casey-lappy: ~/code/haiv'` (shell prompt) |

## Detection strategy

1. Add `sys.stdout.write('\033]2;haiv-tui\007')` to `HaivApp.on_mount()`
2. In `TerminalManager.ensure_workspace()`, after finding the hud pane, check `pane.title`
3. If title doesn't match the expected marker → TUI has crashed, trigger recovery

## Where I'm Going Next

I have the detection mechanism. Now I need to design the recovery flow — what does `ensure_workspace()` do when it detects a crashed hud pane? Options: kill and recreate, or relaunch TUI in place and restore the split.
