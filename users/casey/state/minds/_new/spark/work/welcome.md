# Task Assignment

**PM: Mind Folder Structure Migration**

You are a Project Manager coordinating the migration from `startup/` to `work/` + `home/` folder structure for minds.

---

## Context

We've restructured how minds organize their files:

**Old structure (what the code expects):**
```
minds/{mind}/
├── startup/           # Everything loads on wake
│   ├── welcome.md
│   ├── immediate-plan.md
│   ├── long-term-vision.md
│   ├── my-process.md
│   ├── scratchpad.md
│   └── references.toml
└── docs/
```

**New structure (what wren and sage already have):**
```
minds/{mind}/
├── work/              # All assignment/role docs (cleared between assignments)
│   ├── welcome.md
│   ├── immediate-plan.md
│   ├── long-term-vision.md
│   ├── my-process.md
│   ├── scratchpad.md
│   └── docs/          # Assignment-related documents
├── home/              # Personal continuity (persists, mind-owned, structure is up to the mind)
└── references.toml    # At root level now
```

**Current state:**
- wren and sage are ALREADY on the new structure
- The code still expects the old `startup/` structure
- `mg become wren` is currently broken until code is updated

---

## Work Packages

### WP1: Update MindPaths (code change)
**Location:** `worktrees/main/mg/src/mg/paths.py`

Update the `MindPaths` class to use new paths:
- `startup_dir` → `work_dir`
- `references_file` → at root level (not in startup/)
- Add `home_dir` property
- Add `journal_file` property

### WP2: Update minds helper (code change)
**Location:** `worktrees/main/mg/src/mg/helpers/minds.py`

Update functions:
- `get_startup_files()` → load from both `work/` and `home/`
- `ensure_structure()` → check for `work/` + `home/` instead of `startup/`
- `scaffold_mind()` → create new structure

### WP3: Update tests
**Location:** `worktrees/main/mg/tests/`, `worktrees/main/mg-core/tests/`

Update tests to expect new structure.

### WP4: Verify commands work
Test that `mg become`, `mg start`, `mg minds stage` all work with the new structure.

---

## Requirements

- No data loss for existing minds (wren, sage)
- All mind-related commands continue to work
- New minds created with `mg minds stage` get the new structure

---

## Success Criteria

- `mg become wren` works and loads files from `work/` + `home/`
- `mg minds stage` creates minds with new structure
- All tests pass

---

## Verification

```bash
# Test become works
mg become wren

# Test new mind creation
mg minds stage --no-worktree
# Check it has work/ and home/ directories

# Run tests
cd worktrees/main/mg && uv run pytest
cd worktrees/main/mg-core && uv run pytest
```

---

## Process

1. Assign worker for WP1+WP2 (paths and helper changes)
2. Review changes, run tests
3. Assign worker for WP3 if tests need updating
4. Verify all commands work end-to-end
5. Write AAR documenting the migration

---

## Role Reference

See `src/mg_project/__assets__/roles/project-manager.md` for PM guidance.
