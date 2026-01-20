# After Action Report: Update Mind Folder Structure

**Date:** 2026-01-19
**Task:** Update Python code to support new mind folder structure (startup/ → work/ + home/)

---

## Summary

Updated the mg Python code to work with the new mind folder structure. The folder structure changed from `startup/` + `docs/` to `work/` + `home/` + `work/docs/`, with `references.toml` moved to the mind's root level. This was a code update task - the folder structure had already been changed for existing minds.

## Implementation

### paths.py Changes

Restructured `MindPaths` into three classes:

- `WorkPaths` - Paths within `work/` directory (welcome, immediate-plan, scratchpad, etc.)
- `HomePaths` - Paths within `home/` directory (journal)
- `MindPaths` - Root paths with `work`, `home`, and `references_file` properties

Added `mg_root: Path | None` to `MindPaths` - needed to resolve reference paths to absolute paths.

### minds.py Changes

- **`get_startup_files()`** - Now returns ALL files to load on wake:
  - Resolved paths from `references.toml` (using `mg_root`)
  - Top-level files from `work/`
  - Top-level files from `home/`
  - All sorted by filename

- **`ensure_structure()`** - Updated to check for `work/`, `home/`, `work/docs/`, and `references.toml` at root

- **`scaffold_mind()`** - Creates new structure: `work/`, `home/`, `work/docs/`

- **`resolve_mind()`** and **`list_minds()`** - Now require `mg_root` parameter

### Command Updates

- **`become/_mind_.py`** - Simplified to only call `get_startup_files()` (previously called both `get_references()` and `get_startup_files()` separately)

- **`mine.py`** - Updated to show `work/` path instead of `startup/`

- **`resolvers/mind.py`** - Passes `ctx.paths.root` as `mg_root`

## Key Decisions

1. **mg_root on MindPaths** - Stored on `MindPaths` rather than `Mind` since it's path-related context
2. **RuntimeError for missing mg_root** - When `get_startup_files()` needs to resolve references but `mg_root` is None, raises `RuntimeError` (dev mistake, not user error)
3. **Sorted by filename** - `get_startup_files()` returns all files sorted by name for consistent output
4. **Required mg_root** - Made `mg_root` required on `resolve_mind()` and `list_minds()` rather than optional

## Verification

- mg: 480 tests pass
- mg-core: 177 tests pass
- mg-cli: 18 tests pass
- Type checking: all packages pass

## Files Changed

**Modified (mg package):**
- `mg/src/mg/paths.py` - Added WorkPaths, HomePaths, mg_root to MindPaths
- `mg/src/mg/helpers/minds.py` - Updated get_startup_files, ensure_structure, scaffold_mind, resolve_mind, list_minds
- `mg/tests/test_minds_helper.py` - Updated tests for new structure

**Modified (mg-core package):**
- `mg-core/src/mg_core/commands/become/_mind_.py` - Simplified to use only get_startup_files()
- `mg-core/src/mg_core/commands/mine.py` - Updated path output
- `mg-core/src/mg_core/resolvers/mind.py` - Pass mg_root to resolve_mind()
- `mg-core/tests/test_become.py` - Updated for new structure
- `mg-core/tests/test_minds_new.py` - Updated expected paths
- `mg-core/tests/test_mine.py` - Updated expected output
