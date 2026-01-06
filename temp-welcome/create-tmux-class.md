# Task Assignment

Load the following documents into context:
- ./src/mg_project/roles/generalist.md (your role)
- ./worktrees/main/mg/src/mg/git.py (pattern reference - follow this structure)

---

## Task

**Create a Tmux class in mg**

Build a `Tmux` class similar to the existing `Git` class. The goal is a simple wrapper around subprocess that:
- Standardizes how we run common tmux commands
- Is easier to mock in tests

Follow the patterns established by the Git class.

**Location:** `worktrees/main/mg/`

---

## Success Criteria

- Tmux class created following Git class patterns
- Covers common tmux operations (list sessions/windows, capture-pane, send-keys, etc.)
- Tests pass
- Easy to mock for testing

---

## Verification

```bash
cd worktrees/main && uv run pytest mg/ -v
```

---

## Process

1. Study the Git class thoroughly
2. Propose your approach - which tmux commands to wrap
3. Implement incrementally, testing as you go
