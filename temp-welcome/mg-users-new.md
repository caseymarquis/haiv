# Task Assignment

Load the following documents into context:
- ./temp-roles/generalist.md (your role - how to work)
- ./docs/mind-games-vision-exploration.md (project vision and architecture)
- ./docs/PLAN-user-detection.md (spec - focus on Phase D: mg users new)
- ./worktrees/main/mg-core/src/mg_core/commands/init.py (pattern reference)

---

## Task

**Implement mg users new command**

Create the `mg users new --name <name>` command that sets up a new user directory with the standard structure.

**Location:** `worktrees/main/mg-core/`

## Success Criteria

- Command creates user directory structure per spec in PLAN-user-detection.md
- Pre-populates identity.toml with current environment (git email, git name, system user)
- Templates live in `mg_core/__assets__/users/`
- Tests pass
- Works when run manually from an mg-managed repo

## Patterns to Follow

- Follow structure of existing commands in mg-core (especially `init.py`)
- Use `__assets__/` for template files
- Use `ctx.paths` for directory resolution
- TDD encouraged - write tests alongside implementation

## Verification

```bash
cd worktrees/main && uv run pytest mg-core/
```

---

## Process

1. Read the context documents first
2. Propose your approach before coding
3. Ask clarifying questions if needed
4. Implement incrementally, testing as you go
