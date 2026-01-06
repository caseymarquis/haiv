# Handoff: Mind Management Commands

**Task:** Implement mind management commands in mg_core
**Status:** ~70% complete
**Date:** 2026-01-05

---

## Context Documents to Load

```
Required:
- ./specs/memory-persistence.md          # The specification (defines behavior)
- ./temp-aar/tmux-class.md               # Tmux class design decisions

Reference (skim as needed):
- ./worktrees/main/mg/src/mg/tmux.py     # Tmux class implementation
- ./worktrees/main/mg/src/mg/cmd.py      # Command API
```

---

## Completed Work

### 1. Environment Variable
- `MG_MIND` added to `mg/src/mg/env.py`

### 2. Paths Extension
- `paths.minds` property added to `mg/src/mg/paths.py`
- Returns `users/{user}/state/minds/`

### 3. Mind Helper Module
**Location:** `mg-core/src/mg_core/helpers/minds.py`

Classes:
- `MindPaths` - paths for a mind (root, startup, docs, references_file)
- `Mind` - resolved mind with methods:
  - `name` (property, derived from folder name)
  - `ensure_structure(fix=True)` - creates missing dirs/files
  - `get_references()` - parses references.toml
  - `get_startup_files()` - lists files in startup/
- `MindStructureIssue` - issue found during validation

Functions:
- `list_mind_paths(minds_dir)` - returns `[(name, path), ...]`
- `resolve_mind(name, minds_dir)` - returns `Mind`
- `list_minds(minds_dir)` - returns `[Mind, ...]`

Errors:
- `MindNotFoundError`
- `DuplicateMindError`

**Tests:** 32 passing in `mg-core/tests/test_minds_helper.py`

### 4. Mind Resolver
**Location:** `mg-core/src/mg_core/resolvers/mind.py`

- Resolves mind name string → `Mind` object
- Calls `ensure_structure(fix=True)` and warns on issues
- Uses `ctx.paths.minds` for minds directory

### 5. Wake Command
**Location:** `mg-core/src/mg_core/commands/wake/_mind_.py`

- `mg wake {mind}` - outputs files for mind to read
- Lists references from `references.toml` first
- Then lists other files in `startup/` (except references.toml)

**Tests:** 7 passing in `mg-core/tests/test_wake.py`

---

## Remaining Work

### 1. Extend Tmux Class (mg/src/mg/tmux.py)

Add two methods:

```python
def new_window(self, name: str) -> None:
    """Create a new window with the given name."""
    self.run(f"new-window -n {name}", intent=f"create window '{name}'")

def setenv(self, var: str, value: str, global_: bool = False) -> None:
    """Set an environment variable in the session."""
    flag = "-g" if global_ else ""
    self.run(f"setenv {flag} -t {self.session} {var} '{value}'".strip(),
             intent=f"set {var} in session")
```

Add tests for these methods.

### 2. Start Command
**Location:** `mg-core/src/mg_core/commands/start/_mind_.py`

Per spec (`mg start {mind} [--tmux]`):

**Without --tmux (current terminal):**
- Clear terminal
- Set `MG_MIND` and `MG_ROOT` env vars
- `os.execlp("claude", "claude", "--prompt", "Run \`mg wake {mind}\`")`

**With --tmux:**
- Create new tmux window named `{mind}`
- Set `MG_MIND` and `MG_ROOT` via `tmux.setenv()`
- Send keys: `clear` then `claude --prompt "Run \`mg wake {mind}\`"`

Directory structure exists (`start/__init__.py` created), command file needs implementation.

Test file started at `mg-core/tests/test_start.py` but needs updating to match Tmux API.

### 3. Mine Command
**Location:** `mg-core/src/mg_core/commands/mine.py` (no param capture needed)

Per spec (`mg mine`):
- Requires `MG_MIND` env var (error if not set)
- Outputs:
  - Mind name and location
  - Startup context path
  - Role (from references.toml if present)

### 4. Run Full Test Suite
```bash
cd worktrees/main && uv run pytest mg-core/ -v
```

---

## Key Patterns

### Command Structure
```python
from mg import cmd
from mg_core.helpers.minds import Mind

def define() -> cmd.Def:
    return cmd.Def(
        description="...",
        flags=[cmd.Flag("tmux", type=bool)],
    )

def execute(ctx: cmd.Ctx) -> None:
    mind: Mind = ctx.args.get_one("mind")  # Resolver provides Mind object
    use_tmux = ctx.args.has("tmux")
    # ...
```

### Testing Commands
```python
from mg import test
from mg.args import ResolveRequest

def mock_resolve(req: ResolveRequest) -> Mind:
    return Mind(paths=MindPaths(root=some_path))

# Routing
match = test.routes_to("start wren --tmux")

# Parsing
ctx = test.parse("start wren", resolve=mock_resolve)

# Execution
test.execute("start wren", resolve=mock_resolve, setup=lambda ctx: ...)
```

---

## Verification

After completing all commands:
```bash
cd worktrees/main && uv run pytest mg-core/ -v
```

Manual test with an existing mind (if available):
```bash
mg wake wren
mg start wren --tmux
mg mine
```
