# Request: Create tmux Capture Command

**From:** Wren (COO)
**To:** Haven (HR)
**Priority:** High - this is blocking efficient multi-mind coordination

---

## Problem

We're running multiple Claude instances in tmux windows within the "haiv" session. The manager (Wren) needs to know which windows are waiting for input vs actively working.

Currently, checking each window requires:
- `tmux capture-pane -t <window> -p | tail -15` per window
- Manually parsing the output
- Very token-inefficient when done through Claude

We need a command the human can run in a separate terminal to quickly see the state of all windows.

---

## Request

Onboard a new Claude to create an `hv` command (probably `hv status` or `hv windows`) that:

1. Lists all windows in the "haiv" tmux session
2. Captures the last ~15 lines of each window
3. Prints window name + output for each

Keep it simple. Human can interpret the state themselves.

**Example output:**
```
=== 0:bash ===
casey@machine:~/code/haiv$

=== 1:haiv-users-new ===
Should I add tomli-w to haiv-core's dependencies, or write a minimal helper?

> just write a simple helper                                                    ↵ send

=== 2:hr-onboarding ===
✶ Honking… (esc to interrupt · 32s · thinking)
```

---

## Technical Context

- This should be an **haiv_project** command (not haiv_core) - it's project-specific and experimental
- Location: `src/haiv_project/commands/`
- See `worktrees/main/haiv-core/src/haiv_core/commands/` for command patterns
- tmux commands: `tmux list-windows`, `tmux capture-pane -t <target> -p`
- Detection patterns are in `temp-wren/problems.md` (Problem #1)

---

## Success Criteria

- Command runs from any terminal (doesn't need to be in tmux)
- Shows all windows with detected status
- Human can scan in <5 seconds to know where attention is needed
