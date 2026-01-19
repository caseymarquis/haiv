# Task Assignment

**Update Python code to support new mind folder structure**

Update the mg Python code (paths.py and minds.py) to work with the new folder structure. This is a **code change task**, not a file migration - the folder structure change has already happened for existing minds.

**Location:** `worktrees/nova/`

---

## Context

The folder structure has changed from:
```
minds/{mind}/
├── startup/           # Everything loads on wake
│   ├── welcome.md
│   ├── immediate-plan.md
│   ├── references.toml
│   └── ...
└── docs/
```

To this structure:
```
minds/{mind}/
├── work/              # Assignment docs (cleared between assignments)
│   ├── welcome.md
│   ├── immediate-plan.md
│   ├── scratchpad.md
│   └── docs/          # Assignment-related documents
├── home/              # Personal continuity (persists, mind-owned)
└── references.toml    # At root level now
```

Two minds (wren and sage) already have the new folder structure. The Python code still expects the old structure. Your job is to update the Python code to match the new reality.

---

## Requirements

### WP1: Update MindPaths (`mg/src/mg/paths.py`)

- Rename `startup_dir` property to `work_dir` (returns `root / "work"`)
- Move `references_file` to root level (returns `root / "references.toml"`)
- Add `home_dir` property (returns `root / "home"`)
- Update all file properties (welcome, immediate_plan, etc.) to use `work_dir`

### WP2: Update minds helper (`mg/src/mg/helpers/minds.py`)

- `ensure_structure()`: Check for `work/` + `home/` instead of `startup/` + `docs/`
- `get_startup_files()`: Return ALL files to load on wake - external docs from `references.toml` (call `get_references()` internally) + top-level files from `work/` + top-level files from `home/`
- **Note:** Calling code may currently use both `get_startup_files()` and `get_references()` separately. Update callers to only use `get_startup_files()` to avoid duplicates.
- `scaffold_mind()`: Create `work/` + `home/` + `work/docs/` instead of `startup/` + `docs/`
- Update module docstring to reflect new structure

---

## Success Criteria

- `mg become wren` works and loads files from `work/`
- `mg minds stage` creates minds with new structure
- All tests pass

---

## Workflow (TDD)

Follow the generalist workflow:

### 1. Understand
Read both files completely:
- `mg/src/mg/paths.py` - MindPaths class
- `mg/src/mg/helpers/minds.py` - Mind class and helper functions

### 2. Design
Sketch the changes needed - what properties change, what stays the same.

### 3. Write Tests First
Update/create tests in:
- `mg/tests/` for paths and helper changes
- `mg-core/tests/test_become.py` - update to use `work/` instead of `startup/`
- `mg-core/tests/test_minds_new.py` - update expected structure

### 4. Implement
Make the tests pass by updating:
- `mg/src/mg/paths.py`
- `mg/src/mg/helpers/minds.py`

### 5. Verify
```bash
cd worktrees/nova/mg && uv run pytest
cd worktrees/nova/mg-core && uv run pytest
```

### 6. Write AAR
Write AAR in `temp-aar/` summarizing changes made.

