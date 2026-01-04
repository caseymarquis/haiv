# Task Assignment

Load the following documents into context:
- ./temp-roles/generalist.md (your role)
- ./specs/memory-persistence.md (the specification to implement)
- ./temp-aar/memory-persistence-design.md (summary of design decisions)
- ./worktrees/main/mg/src/mg/cmd.py (command API)
- ./worktrees/main/mg-core/src/mg_core/commands/init.py (pattern reference)

Optional deeper context:
- ./explorations/memory-persistence.md (background exploration)

---

## Task

**Implement mind management commands in mg_core**

Implement the following commands per the specification:
- `mg start {mind} [--tmux]` - launch a mind
- `mg wake` - reload after compaction
- `mg mine` - list user's minds

**Location:** `worktrees/main/mg-core/`

---

## Success Criteria

- Commands implemented in mg_core following existing patterns
- Tests pass
- Works when run manually from an mg-managed repo

---

## Verification

```bash
cd worktrees/main && uv run pytest mg-core/ -v
```

---

## Process

1. Read the spec thoroughly - it defines the behavior
2. Study existing command patterns in mg-core
3. Propose your approach before coding
4. Implement incrementally, testing as you go
