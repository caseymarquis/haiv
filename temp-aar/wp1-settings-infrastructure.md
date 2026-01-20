# After Action Report: Settings Infrastructure

**Task:** Build foundational settings system for mg (mg.toml)
**Date:** 2026-01-18

---

## Summary

Added layered configuration system using `mg.toml` files at project and user levels. User values override project values. Settings are lazy-loaded and cached for performance. The implementation keeps the public API minimal (just `MgSettings` dataclass) while hiding loading/caching complexity in `_infrastructure/`.

---

## Deliverables

| Item | Location |
|------|----------|
| MgSettings dataclass | `mg/src/mg/settings.py` |
| SettingsCache, loading, merging | `mg/src/mg/_infrastructure/settings.py` |
| Path properties | `mg/src/mg/paths.py` (project_settings_file, settings_file) |
| Ctx integration | `mg/src/mg/cmd.py` (settings property) |
| Tests | `mg/tests/test_settings.py` |

---

## Design Decisions

### 1. Split Public/Private

`MgSettings` dataclass lives in `mg/settings.py` - this is what users interact with. Loading, caching, and merging live in `mg/_infrastructure/settings.py` - implementation details users don't need to know.

Rationale: Reduces token count when new minds read `cmd.py`. They see `settings` returns `MgSettings`, not all the caching logic.

### 2. Private Fields with Public Properties

```python
@dataclass
class MgSettings:
    _default_branch: str | None = None

    @property
    def default_branch(self) -> str:
        return self._default_branch if self._default_branch is not None else "main"
```

Private fields hold raw loaded values (None = not set). Public properties provide effective values with fallbacks. This allows merge logic to distinguish "not set" from "explicitly set to X".

### 3. SettingsCache as Dumb Data Holder

```python
@dataclass
class SettingsCache:
    project: MgSettings | None = None
    user: MgSettings | None = None
```

Cache is just data. Functions do the work. Cleaner than a SettingsLoader class, easier to test.

### 4. Dynamic Merge via Dataclass Introspection

```python
for field in fields(MgSettings):
    if not field.name.startswith("_"):
        continue
    # merge logic
```

Adding new settings only requires adding the private field and public property. Merge handles it automatically.

### 5. Path Naming

- `paths.project_settings_file` - project-level `mg.toml`
- `paths.user.settings_file` - user-level `mg.toml`

UserPaths uses just `settings_file` since the "user" context is implied by the class.

---

## Files

| File | Purpose |
|------|---------|
| `mg.toml` (project root) | Project-level settings, created with commented defaults |
| `users/{name}/mg.toml` | User-level settings, created empty |

---

## Tests

| Test Class | Count | Coverage |
|------------|-------|----------|
| `TestMgSettings` | 2 | Fallback behavior |
| `TestLoadProjectSettings` | 3 | Load, create, empty file |
| `TestLoadUserSettings` | 3 | Load, create, empty file |
| `TestMergeSettings` | 4 | Override behavior |
| `TestSettingsCache` | 2 | Cache storage |
| `TestGetSettings` | 4 | Integration with paths |
| `TestCtxSettings` | 3 | Ctx property behavior |

Total: 21 tests passing.

---

## Usage

```python
# In any command
def execute(ctx: Ctx) -> None:
    branch = ctx.settings.default_branch  # "main" or configured value
```

```toml
# Project mg.toml
default_branch = "develop"

# User mg.toml (overrides project)
default_branch = "my-feature"
```

---

## Open Items

- Only `default_branch` setting implemented - add more as needed
- No CLI command to view/edit settings (could be useful)
- No validation of setting values (e.g., branch name format)
