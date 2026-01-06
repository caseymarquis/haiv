# Task Assignment

**Implement `mg minds suggest_role --name {mind}` command**

Create a command that reads a mind's welcome.md, analyzes the task description, and suggests appropriate roles from available role files.

**Location:** `worktrees/main/mg-core/`

---

## Requirements

1. Accept `--name {mind}` to identify the mind
2. Read the mind's `startup/welcome.md` file
3. Find all role files in `__assets__/roles/` across all mg packages
4. Output a list of roles with brief descriptions and paths
5. Optionally suggest which role(s) seem most relevant based on the task

---

## Success Criteria

- `mg minds suggest_role --name sage` reads sage's welcome.md
- Lists available roles with descriptions
- Suggests relevant role(s) based on task content
- Handles missing welcome.md gracefully
- Existing tests pass
- Add tests for the new command

---

## Verification

```bash
cd worktrees/main && uv run pytest mg-core/ -v
mg minds suggest_role --name sage  # manual test
```

---

## Process

1. Read the existing minds new command for patterns
2. Write tests first (TDD)
3. Implement role discovery (search __assets__/roles/ in packages)
4. Implement welcome.md parsing
5. Implement suggestion logic
6. Verify all tests pass
7. Write AAR to temp-aar/mg-minds-suggest-role.md
