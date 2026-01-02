# Immediate Plans

**Date:** 2025-01-01
**Goal:** Bootstrap mg development using mg itself

---

## Strategy

Use `worktrees/main/` as the stable mg installation. Develop features on branches, merge to main when tested. This prevents breaking the tool while using it.

**Location:** This docs folder now lives in the control plane (mg-state), not in the code worktree.

---

## Phase 1: Complete Scaffold ✓

Scaffold is complete. `mg init` now creates:
- [x] .claude/ directory
- [x] pyproject.toml (project-level)
- [x] src/mg_project/ (minimal package)
- [x] tests/ (with example test)
- [x] users/ directory
- [ ] Update CLAUDE.md with common commands (deferred - no commands yet)

---

## Phase 2: Multi-Source Commands + Dev Install ✓

### 2.1: Multi-Source Command Loading ✓

CLI now loads commands from multiple sources in precedence order:
- [x] `load_commands_module(init_file: Path)` in loader.py using importlib
- [x] `CommandSource` dataclass tracks checked/unchecked sources with error messages
- [x] CLI tries mg_project first, falls back to mg_core
- [x] Helpful error messages show which sources were checked
- [x] Scaffold creates `mg_project/commands/__init__.py`

### 2.2: Dev Install Command ✓

`mg dev install` implemented as project command:
- [x] `--branch <name>` - which worktree to use (default: "main")
- [x] `--force` - overwrite existing installation
- [x] Validates worktree and mg-cli existence
- [x] Creates shell script at `~/.local/bin/mg`

### 2.3: Test Framework Improvements ✓

Enhanced `mg.test` module for better unit testing:
- [x] `parse()` and `execute()` auto-create temp mg_root
- [x] `setup` callback on `execute()` to modify ctx before running
- [x] Auto-cleanup of temp directories at module exit
- [x] Commands module auto-discovery (no need to pass explicitly)

### 2.4: pyproject.toml for Development ✓

- [x] Use `[tool.uv.sources]` with `editable = true` for local development
- [x] Clean dependency declaration with source override separate

---

## Phase 3: mg start

Properly initialize a session:
- Detect mg-state root (walk up from cwd, or use MG_PROJECT_ROOT)
- Scan users/ for identity.toml matches
- Create user folder if no match (prompt for name)
- Set session context (could set MG_PROJECT_ROOT for subprocesses)

This enables project-level and user-level commands without manual env vars.

---

## Phase 4: Parallel Development

Start running multiple Claude sessions:

1. Create additional worktrees for feature branches
2. Spawn tmux sessions, one per worktree
3. Each Claude instance works independently
4. Coordinate via git (push/pull/merge)

**Blockers to identify:**
- What's the manual tmux workflow?
- What friction points emerge?
- What coordination is actually needed?

---

## Open Questions

- Does the shell script approach work with uv's caching?
- How should mg dev install interact with `uv tool install mind-games`?
- How do we handle user identity across parallel sessions?
