# Immediate Plans

**Date:** 2026-01-02
**Goal:** Bootstrap haiv development using haiv itself

---

## Strategy

Use `worktrees/main/` as the stable haiv installation. Develop features on branches, merge to main when tested. This prevents breaking the tool while using it.

**Location:** This docs folder now lives in the control plane (haiv-hq), not in the code worktree.

---

## Phase 1: Complete Scaffold ✓

Scaffold is complete. `hv init` now creates:
- [x] .claude/ directory
- [x] pyproject.toml (project-level)
- [x] src/haiv_project/ (minimal package)
- [x] tests/ (with example test)
- [x] users/ directory
- [ ] Update CLAUDE.md with common commands (deferred - no commands yet)

---

## Phase 2: Multi-Source Commands + Dev Install ✓

### 2.1: Multi-Source Command Loading ✓

CLI now loads commands from multiple sources in precedence order:
- [x] `load_commands_module(init_file: Path)` in loader.py using importlib
- [x] `CommandSource` dataclass tracks checked/unchecked sources with error messages
- [x] CLI tries haiv_project first, falls back to haiv_core
- [x] Helpful error messages show which sources were checked
- [x] Scaffold creates `haiv_project/commands/__init__.py`

### 2.2: Dev Install Command ✓

`hv dev install` implemented as project command:
- [x] `--branch <name>` - which worktree to use (default: "main")
- [x] `--force` - overwrite existing installation
- [x] Validates worktree and haiv-cli existence
- [x] Creates shell script at `~/.local/bin/hv`

### 2.3: Test Framework Improvements ✓

Enhanced `haiv.test` module for better unit testing:
- [x] `parse()` and `execute()` auto-create temp haiv_root
- [x] `setup` callback on `execute()` to modify ctx before running
- [x] Auto-cleanup of temp directories at module exit
- [x] Commands module auto-discovery (no need to pass explicitly)

### 2.4: pyproject.toml for Development ✓

- [x] Use `[tool.uv.sources]` with `editable = true` for local development
- [x] Clean dependency declaration with source override separate

---

## Phase 3: User Identity Detection ✓

### 3.1: Core Identity Module ✓

Implemented `haiv/identity.py`:
- [x] `CurrentEnv` dataclass - source of truth for match field names
- [x] `Identity` dataclass - detected user result
- [x] `detect_user(users_dir)` - scan for matching identity.toml
- [x] `matches()` - case-insensitive matching using `casefold()`
- [x] `load_match_config()` - parse identity.toml [match] section
- [x] `get_current_env()` - gather git config + $USER
- [x] `AmbiguousIdentityError` - raised when multiple users match
- [x] 32 tests in `haiv/tests/test_identity.py`

### 3.2: CLI Integration ✓

Updated `haiv_cli/__init__.py`:
- [x] `_detect_user_cached()` - cached user detection with error handling
- [x] `_get_user_commands()` - load haiv_user commands module
- [x] Updated `_find_command()` - precedence: haiv_user → haiv_project → haiv_core
- [x] No user found raises error (shown as unchecked source)
- [x] 4 new integration tests in `haiv-cli/tests/test_command_sources.py`

### 3.3: Paths Extension ✓

Extended `haiv/paths.py`:
- [x] `_user_name` field on Paths dataclass
- [x] `paths.users` - the users/ directory
- [x] `paths.user` - PkgPaths for user's package (throws if no user)
- [x] `paths.state` - user's state directory (throws if no user)

### 3.4: Context Integration ✓

Extended `haiv/args.py` and test utilities:
- [x] `build_ctx()` accepts `haiv_username` parameter
- [x] CLI passes detected username to `build_ctx`
- [x] `haiv/test.py` uses `TEST_USERNAME = "testinius"` as default
- [x] Test utilities auto-create `users/testinius/state/` folder
- [x] `Sandbox` respects `explicit` mode (no auto-creation when True)

### 3.5: hv users new Command

- [ ] Create `haiv_core/commands/users/new.py`
- [ ] Templates in `haiv_core/__assets__/users/`
- [ ] Tests for user creation

---

## Phase 4: Parallel Development (CURRENT)

**Decision:** Use tmux as foundation, manual-first approach. See vision doc for details.

### 4.1: Concepts (emerging)

**Window = task, not worktree:**
- Window named by task (e.g., `implement-oauth`, `research-caching`)
- Worktree is optional resource - some tasks need code isolation, some don't
- A task could involve multiple worktrees

**Manager role = context assembly:**
- Decide what context a task needs (role, task description, worktree, docs)
- Launch mind with composed context
- Monitor progress via `tmux capture-pane`

**Task artifacts (needed):**
- Some representation of a task that haiv can use to:
  - Create tmux window with right name/cwd
  - Compose initial prompt with context
  - Track state (pending, in-progress, blocked, done)
- Format TBD - probably markdown or TOML in `state/tasks/`

### 4.2: Manual Workflow (now)

```bash
# Session already exists: haiv

# Create window for a task (with or without worktree)
tmux new-window -n task-name -c /path/to/working/dir

# Switch to window, start Claude, give initial context manually
```

### 4.3: Friction Points to Watch

- Switching attention between windows
- Knowing which minds need input
- Composing initial context (repetitive, error-prone)
- Tracking what each mind is working on
- Loading/saving persistent memory

### 4.4: Automation Candidates

| Command | Purpose | Priority |
|---------|---------|----------|
| `hv task new` | Create task artifact + tmux window | High |
| `hv task start` | Launch mind with context from artifact | High |
| `hv status` | Show all tasks and their state | Medium |
| `hv worktree add` | Simplify worktree creation | Medium |

### 4.5: Delegable Now

**`hv users new` (Phase 3.5)** - finish the remaining Phase 3 work:
- Create `haiv_core/commands/users/new.py`
- Templates in `haiv_core/__assets__/users/`
- Tests for user creation

This is a good first delegation candidate - well-defined scope, existing patterns to follow.

---

## Test Coverage

| Package | Tests |
|---------|-------|
| haiv | 228 |
| haiv-core | 63 |
| haiv-cli | 13 |
| **Total** | **304** |

---

## Open Questions

- Does the shell script approach work with uv's caching?
- How should hv dev install interact with `uv tool install haiv`?
- HV_SESSION design - what additional data should be cached?
