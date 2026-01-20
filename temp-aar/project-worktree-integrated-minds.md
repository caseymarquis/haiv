# Project AAR: Worktree-integrated Mind Creation

**Project Manager:** Luna
**Date:** 2026-01-18

---

## Summary

Delivered `mg minds new --worktree` - a single command that creates both a mind and its dedicated worktree. This eliminates the manual two-step process and ensures minds start with proper workspace isolation.

---

## Deliverables

### Feature: `mg minds new` with worktree integration

**Usage:**
```bash
mg minds new --worktree              # Creates mind + worktree (branch = mind name)
mg minds new --worktree --branch X   # Creates mind + worktree named X
mg minds new --no-worktree           # Creates mind only (old behavior)
mg minds new                         # Error with helpful message
```

**Behavior:**
- Worktree branched from `default_branch` setting (defaults to "main")
- welcome.md automatically populated with `**Location:** worktrees/{branch}/`
- Clean error message when neither flag provided

### Infrastructure: Layered Settings System

**Files:**
- `mg.toml` at project root (created with commented defaults)
- `users/{user}/mg.toml` (created empty, user overrides project)

**Access:**
```python
ctx.settings.default_branch  # Returns effective value with fallback
```

**Design:**
- Lazy-loaded on first access
- Project and user settings cached separately
- Merge recomputed on each access (picks up user when available)
- Private fields (`_default_branch`) with public property fallbacks

---

## Work Packages

| WP | Description | Worker | Status |
|----|-------------|--------|--------|
| 1 | Settings infrastructure (mg.toml) | prism | Complete |
| 2 | `mg minds new` worktree flags | pulse | Complete |

---

## Lessons Learned

### 1. UV Monorepo Worktree Setup
**Issue:** New worktrees need `uv sync` run for each package before tests work.
**Impact:** Workers hit failing imports until manually synced.
**Future:** Add project hooks that run after worktree creation (e.g., sync all packages).

### 2. Worker Commit Discipline
**Issue:** Workers sometimes finish without committing their changes.
**Impact:** PM had to commit on their behalf before merging.
**Future:** Emphasize commit step in task assignments, or add verification to AAR process.

### 3. Design Iteration Value
**Observation:** Upfront design discussion (settings caching strategy, module placement) saved rework.
**Takeaway:** PM-human design sessions before delegation reduce worker confusion.

---

## Open Items

1. **Project hooks for worktree setup** - Auto-run commands (like `uv sync`) after worktree creation
2. **Settings CLI** - `mg settings show` / `mg settings set` for discoverability
3. **Settings validation** - Validate setting values (e.g., branch name format)
4. **More settings** - Only `default_branch` exists; add others as needed

---

## Files Changed

### WP1: Settings Infrastructure
- `mg/src/mg/settings.py` (new)
- `mg/src/mg/_infrastructure/settings.py` (new)
- `mg/src/mg/paths.py` (added settings_file properties)
- `mg/src/mg/cmd.py` (added settings property to Ctx)
- `mg/tests/test_settings.py` (new)

### WP2: Worktree Integration
- `mg-core/src/mg_core/commands/minds/new.py` (updated)
- `mg/src/mg/helpers/minds.py` (updated scaffold_mind)
- `mg-core/src/mg_core/__assets__/minds/welcome.md.j2` (updated template)

---

## Verification

```bash
# All tests pass
cd worktrees/main/mg && uv run pytest
cd worktrees/main/mg-core && uv run pytest

# Integration test
mg minds new --worktree --name test-mind
# Creates: users/{user}/state/minds/_new/test-mind/
# Creates: worktrees/test-mind/
# welcome.md has: **Location:** worktrees/test-mind/
```
