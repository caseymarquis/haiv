# Task Assignment

Load the following documents into context:
- ./temp-roles/generalist.md (your role - how to work)
- ./CLAUDE.md (project structure and conventions)
- ./src/mg_project/commands/dev/install.py (pattern reference - mg_project command)

---

## Task

**Implement `mg windows` command**

Create a command that shows the status of all tmux windows in the "mind-games" session, helping the manager quickly see which Claude instances need attention.

**Location:** `src/mg_project/commands/`

## What It Does

1. Lists all windows in the "mind-games" tmux session
2. Captures the last ~15 lines of each window
3. Prints window name + captured output for each

**Example output:**
```
=== 0:bash ===
casey@machine:~/code/mind-games$

=== 1:mg-users-new ===
Should I add tomli-w to mg-core's dependencies, or write a minimal helper?

> just write a simple helper                                                    ↵ send

=== 2:hr-onboarding ===
✶ Honking… (esc to interrupt · 32s · thinking)
```

## Technical Notes

- This is an **mg_project** command (project-specific, not core)
- Use `tmux list-windows -t mind-games` to get window list
- Use `tmux capture-pane -t mind-games:<window> -p` to capture content
- Handle case where tmux session doesn't exist gracefully
- No need for fancy state detection - human will interpret the output

## Success Criteria

- Command runs from any terminal (doesn't need to be inside tmux)
- Shows all windows with their recent output
- Human can scan in <5 seconds to know where attention is needed
- Handles missing session gracefully (clear error message)

## Verification

```bash
# Run tests
uv run pytest src/mg_project/ -v

# Manual test (requires mind-games tmux session)
mg windows
```

---

## Process

1. Read the context documents first
2. Propose your approach before coding
3. Ask clarifying questions if needed
4. Implement incrementally, testing as you go
