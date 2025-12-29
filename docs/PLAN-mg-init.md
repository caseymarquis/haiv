# Plan: mg init and Infrastructure

**Created:** 2024-12-28
**Updated:** 2024-12-29
**Status:** Monorepo complete, peer mode next

---

## Summary

Fresh mode of `mg init` is working. Monorepo migration complete. Next: peer mode implementation.

---

## Completed Work

### Monorepo Migration ✅
- [x] Consolidated mg, mg-core, mg-cli into uv workspace
- [x] Root conftest.py prevents running tests from workspace root
- [x] `pyclean` installed as uv tool for cache cleanup
- [x] Vision document updated for monorepo structure
- [x] Initial commit: `195184b`

### Template System
- [x] jinja2 moved to `mg` package
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

### mg init Fresh Mode
- [x] `_init_mg_structure()` creates CLAUDE.md and commits before branches
- [x] CLAUDE.md.j2 template with reference-level architecture overview
- [x] `--empty`, `--force`, `--branch`, `--quiet` flags

---

## Current Test Status

```bash
# Run from each package directory
cd mg && uv run pytest        # 170 passed
cd mg-core && uv run pytest   # 39 passed, 15 failed (peer mode)
cd mg-cli && uv run pytest    # 4 passed
```

---

## Next Steps

### 1. Peer Mode

- Creates `project-mg/` alongside existing checkout
- Requires remote configured
- Requires clean working tree (unless `--force`)
- 15 tests already written, waiting for implementation

### 2. `mg start` Command (Deferred)

Session context for production use. Design in vision doc.

---

## Monorepo Structure

```
mind-games/
├── mg/           # API (170 tests)
├── mg-core/      # Commands (54 tests, 15 peer mode pending)
├── mg-cli/       # CLI entry point (4 tests)
├── docs/         # Working documents
├── conftest.py   # Prevents root-level pytest
└── pyproject.toml
```

---

## Key Files

| File | Purpose |
|------|---------|
| `mg/src/mg/paths.py` | Paths and PkgPaths dataclasses |
| `mg/src/mg/templates.py` | TemplateRenderer |
| `mg/src/mg/cmd.py` | Ctx class with templates/git properties |
| `mg/src/mg/test.py` | Test infrastructure with auto-discovery |
| `mg-core/src/mg_core/commands/init.py` | init command |
| `mg-core/src/mg_core/__assets__/init/CLAUDE.md.j2` | CLAUDE.md template |
