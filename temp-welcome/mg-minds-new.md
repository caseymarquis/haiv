# Task Assignment

Load the following documents into context:
- ./src/mg_project/__assets__/roles/generalist.md (your role)
- ./worktrees/main/mg-core/src/mg_core/helpers/minds.py (existing minds helper)
- ./worktrees/main/mg-core/src/mg_core/commands/start/_mind_.py (example command with mind resolver)
- ./specs/memory-persistence.md (mind folder structure spec)

---

## Task

**Implement `mg minds new [--name {mind}]` command**

Create a command that scaffolds a new mind folder with proper structure.

**Location:** `worktrees/main/mg-core/`

---

## Requirements

### 1. Name Handling
- If `--name` provided, use it
- If no name provided, generate one using `claude -p "Generate a single short, memorable name (one word, lowercase) for an AI assistant. Just output the name, nothing else."`
- Validate name doesn't already exist using minds helper

### 2. Directory Structure
Create in `users/{user}/state/minds/_new/{mind}/`:
```
{mind}/
├── startup/
│   ├── short-term.md      # template
│   ├── long-term.md       # template
│   └── references.toml    # template pointing to role
└── docs/                  # empty, for mind-specific docs
```

### 3. Templates
Create minimal templates that explain what needs to be filled in:
- `short-term.md` - current session state, active work
- `long-term.md` - role, vision, key documents
- `references.toml` - points to role file(s)

### 4. Output Prompt
After creating structure, output:
- The mind name (generated or provided)
- List available roles (search `__assets__/roles/` in all mg packages)
- Explain which files need editing before the mind can start
- Show the command to run when ready: `mg start {mind} --tmux --task "description"`

---

## Success Criteria

- `mg minds new` generates a name and creates structure
- `mg minds new --name robin` creates structure for "robin"
- Duplicate names are rejected with clear error
- Output clearly guides user on next steps
- Existing tests still pass
- Add tests for the new command

---

## Verification

```bash
cd worktrees/main && uv run pytest mg-core/ -v
mg minds new --name test-mind  # manual test
```

---

## Process

1. Read the existing minds helper to understand current capabilities
2. Design the command structure (define + execute)
3. Write tests first (TDD)
4. Implement the command
5. Verify all tests pass
6. Write AAR to temp-aar/mg-minds-new.md
