# Scratchpad

## Understanding the codebase

**Key patterns to follow:**
- Resolvers: file-based discovery in `resolvers/` dirs, loaded dynamically, layered (core → project → user)
- Commands: file-based routing, `define()` + `execute()` + optional `setup()`/`teardown()`
- CLI wiring: `_find_command()` → `load_command()` → `make_resolver()` → `build_ctx()` → `run_command()`
- Package hierarchy: core (installed) → project_local (src/haiv_project/) → user_local (users/*/src/haiv_user/)

**Hook integration points identified:**
- `minds/stage.py:111-114` — after worktree creation (git worktree add)
- `minds/stage.py:118-124` — after mind scaffolding
- `pop.py:98` — after merge
- `pop.py:125-128` — after session removal

## Design considerations

**Core question:** How does `HookPoint.emit()` know about registered hooks?

Flow:
1. CLI starts, discovers packages
2. Before running command, load all hook modules from all packages (hooks/ dirs)
3. Loading triggers `@hook()` decorators → register handlers on HookPoints
4. Command runs → `emit()` calls registered handlers

**Follows resolver pattern:** hooks/ directory alongside commands/ and resolvers/, file-based discovery, dynamic loading. Same layered approach.

**Difference from resolvers:** resolvers override (later wins), hooks accumulate (all run, returns list).

**Cross-package imports:** haiv_project hooks import HookPoints from haiv_core — this is fine since haiv_core is an installed package dependency.
