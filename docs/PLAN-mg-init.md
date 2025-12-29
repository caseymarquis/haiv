# Plan: mg init and Infrastructure

**Created:** 2024-12-28
**Updated:** 2024-12-29
**Status:** Fresh mode complete, infrastructure work next

---

## Summary

Fresh mode of `mg init` is working. Next priorities are infrastructure improvements (monorepo consolidation, session management) before completing peer mode.

---

## Completed Work

### Template System
- [x] jinja2 moved to `mg` package (stable, low-risk dependency)
- [x] `TemplateRenderer` class with `render()` and `write()` methods
- [x] `ctx.templates` lazy property accessing `pkg.assets`
- [x] `ctx.git` lazy property for Git operations at project root

### Package Paths
- [x] `PkgPaths` dataclass with `root`, `assets`, `commands` properties
- [x] Auto-discovery of calling package in tests via `_find_pkg_paths()`
- [x] `_find_commands_module()` for test auto-discovery

### Test Infrastructure
- [x] `test.routes_to("init")` works without explicit commands import
- [x] `test.parse()` and `test.execute()` also support auto-discovery
- [x] `Sandbox.run()` supports auto-discovery
- [x] mg-core tests updated to use auto-discovery

### mg init Fresh Mode
- [x] `_init_mg_structure()` creates CLAUDE.md and commits before branches
- [x] CLAUDE.md.j2 template with reference-level architecture overview
- [x] `--empty` flag creates worktree with empty commit (no README)
- [x] `--force` flag for non-empty directories
- [x] `--branch` flag to override default branch name
- [x] `--quiet` flag to suppress output
- [x] 32 tests passing (unit + integration)

---

## Current Test Status

```bash
# mg tests
cd /home/casey/code/mg && uv run pytest tests/ -v
# 170 passed

# mg-core fresh mode + unit tests
cd /home/casey/code/mg-core && uv run pytest tests/test_init_unit.py tests/test_init.py -v
# 32 passed, 15 failed (peer mode not implemented)
```

---

## Next Steps (Priority Order)

### 1. Monorepo Migration

**Goal:** Consolidate mg, mg-core, cli into one repository.

**Rationale:**
- Simpler development (atomic cross-package changes)
- One git history, simpler CI
- Packages are tightly coupled anyway
- uv supports subdirectory installs

**Structure:**
```
mind-games/
├── mg/
│   ├── pyproject.toml
│   └── src/mg/
├── mg-core/
│   ├── pyproject.toml
│   └── src/mg_core/
├── cli/
│   ├── pyproject.toml
│   └── src/cli/
├── pyproject.toml          # workspace root with [tool.uv.workspace]
└── CLAUDE.md
```

**Installation:**
```toml
dependencies = [
    "mg @ git+https://github.com/casey/mind-games.git#subdirectory=mg",
]
```

### 2. `mg start` Command

**Goal:** Establish project context at session start.

**Design:**
- Run at session start (CLAUDE.md instructs this)
- Auto-discovers project root from cwd
- Sets environment variable: `MG_SESSION=<session-id>`
- Creates state file: `{user}/state/sessions/<session-id>.json`
- State contains: project root, pkg paths, timestamps, user identity

**State file example:**
```json
{
  "session_id": "abc123",
  "project_root": "/home/casey/code/myproject-mg",
  "pkg": {
    "root": "/home/casey/code/myproject-mg/src/mg_project"
  },
  "user": "casey",
  "started_at": "2024-12-29T10:00:00Z"
}
```

**Session API (in mg package):**
```python
# ctx.session is lazy like ctx.templates and ctx.git
session = ctx.session  # reads MG_SESSION env var + state file

# Read
session.project_root
session.user
session.id

# Write
session.set("custom_key", value)
session.save()
```

**Subsequent commands:**
- Read `MG_SESSION` env var
- Load state from file via `ctx.session`
- `ctx.paths` populated from session state

**`mg status` prints session ID** - enables `mg resume` to restore context if Claude restarts.

### 3. Update CLAUDE.md Template

Add instruction to run `mg start` after launch:

```markdown
## Getting Started

Run `mg start` to initialize your session context.
```

### 4. Peer Mode

**Deferred** until infrastructure is solid.

- Creates `project-mg/` alongside existing checkout
- Requires remote configured
- Requires clean working tree (unless `--force`)
- 15 tests already written, waiting for implementation

---

## Architecture Decisions

### Template System
- Templates accessed via `ctx.templates.write("init/CLAUDE.md.j2", dest)`
- Templates live in `__assets__/<command>/` within each package
- `__assets__/` structure is package-defined; `mind_templates/` is a convention

### Package Paths
```python
@dataclass
class PkgPaths:
    root: Path  # module root, e.g., .../src/mg_core/

    @property
    def assets(self) -> Path:
        return self.root / "__assets__"

    @property
    def commands(self) -> Path:
        return self.root / "commands"
```

### Session Context
- Environment variable holds session ID (survives across commands)
- State file holds full context (paths, user, timestamps)
- `mg start` creates both; commands read them

---

## File Locations

| File | Purpose |
|------|---------|
| `mg/src/mg/paths.py` | Paths and PkgPaths dataclasses |
| `mg/src/mg/templates.py` | TemplateRenderer |
| `mg/src/mg/cmd.py` | Ctx class with templates/git properties |
| `mg/src/mg/test.py` | Test infrastructure with auto-discovery |
| `mg-core/src/mg_core/commands/init.py` | init command |
| `mg-core/src/mg_core/__assets__/init/CLAUDE.md.j2` | CLAUDE.md template |
| `mg-core/tests/test_init.py` | Integration tests |
| `mg-core/tests/test_init_unit.py` | Unit tests |
