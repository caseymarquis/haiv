# Task Assignment

Load the following documents into context:
- ./temp-roles/generalist.md (your role)
- ./worktrees/main/mg/src/mg/routing.py (current routing system)
- ./worktrees/main/mg/src/mg/cmd.py (command API)

---

## Task

**Port the resolvers system from the alpha project**

This is collaborative work with Casey. The alpha project has a resolvers system that needs to be ported to the current mg codebase.

Casey has the alpha project knowledge - ask questions to understand:
- What resolvers do
- How they integrate with routing
- What the alpha implementation looked like

**Location:** `worktrees/main/mg/`

---

## Success Criteria

- Resolvers system ported and working
- Tests pass
- Integrated with existing command routing

---

## Verification

```bash
cd worktrees/main && uv run pytest mg/ -v
```

---

## Process

1. Read the current routing system
2. Ask Casey about the alpha resolvers system
3. Propose your approach
4. Implement incrementally, testing as you go
