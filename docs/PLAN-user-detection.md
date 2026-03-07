# Plan: User Detection in haiv-cli

**Status:** Implemented (Phase D remaining)
**Date:** 2025-01-02

---

## Goal

Integrate user detection into haiv-cli so that:
- User identity is detected automatically when running any `hv` command
- User-specific commands (`haiv_user`) become available when a user is detected
- Session data is cached for the duration of the process

---

## Architecture

### Package Responsibilities

```
haiv/                              # Implementation (reusable)
├── identity.py                  # ✓ User detection logic
└── paths.py                     # ✓ Extended with user paths

haiv_cli/                          # Thin integration
└── __init__.py                  # ✓ Calls into haiv identity functions

haiv_core/                         # Commands
└── commands/users/new.py        # TODO: hv users new --name <name>
```

### Key Principle

CLI stays thin. All real logic lives in `haiv` package so it can be:
- Unit tested independently
- Reused by other commands
- Extended by packages

---

## Data Structures

### identity.toml Format

Lives at `users/{name}/identity.toml`:

```toml
[match]
git_email = ["casey@example.com", "casey@work.com"]
git_name = ["Casey"]
system_user = ["casey", "caseym"]
```

All fields are optional. Any single match is sufficient. Matching is case-insensitive (using `casefold()`).

### CurrentEnv Dataclass

Source of truth for valid match field names:

```python
@dataclass
class CurrentEnv:
    git_email: str | None = None
    git_name: str | None = None
    system_user: str | None = None
```

### Identity Dataclass

```python
@dataclass
class Identity:
    name: str                    # User folder name
    path: Path                   # Full path to user directory
    matched_by: str              # Which field matched (for debugging)
```

### HV_SESSION Environment Variable (Deferred)

TOML-encoded session state - design not yet finalized. Will cache user detection for child processes. Additional session data will be added here in the future.

---

## Detection Flow

### 1. CLI Entry (haiv_cli/__init__.py) ✓

```
main()
  ├── Parse command string
  ├── Find haiv_root (existing logic)
  ├── Find command:
  │     ├── Try haiv_user (calls _detect_user_cached())
  │     ├── Try haiv_project
  │     └── Try haiv_core
  └── Execute command
```

### 2. User Detection (haiv/identity.py) ✓

```python
def detect_user(users_dir: Path) -> Identity | None:
    """Detect current user from environment.

    Raises:
        AmbiguousIdentityError: If multiple users match
    """
```

Steps:
1. Return None if users_dir doesn't exist
2. Get current environment via `get_current_env()`:
   - `git config user.email` (via Git class)
   - `git config user.name` (via Git class)
   - `os.environ.get("USER")` or `os.getlogin()`
3. Scan `users/` subdirectories for `identity.toml`
4. For each identity file, check if any matcher matches (case-insensitive)
5. Return match or None
6. Raise `AmbiguousIdentityError` if multiple matches

### 3. Error Handling ✓

**No match found:**
- CLI treats as error (source not checked)
- Error message: `No user identity found. Run 'hv users new --name <name>' to create one.`
- Command continues via fallback sources (haiv_project, haiv_core)

**Multiple matches:**
- Raise `AmbiguousIdentityError`
- Message includes both identity.toml paths
- User must edit one to resolve conflict

**No users/ directory:**
- Same as no match

---

## Environment Sources ✓

| Source | How to get | Notes |
|--------|------------|-------|
| git_email | `Git(cwd, quiet=True).config("user.email")` | Most reliable identifier |
| git_name | `Git(cwd, quiet=True).config("user.name")` | Secondary |
| system_user | `$USER` or `os.getlogin()` | Fallback |

---

## Paths Integration ✓

Extended `haiv/paths.py`:

```python
@dataclass
class Paths:
    _user_name: str | None = None

    @property
    def users(self) -> Path:
        """The users/ directory."""
        return self.root / "users"

    @property
    def user(self) -> PkgPaths:
        """User package paths. Raises if no user detected."""
        if self._user_name is None:
            raise RuntimeError("No user identity found...")
        return PkgPaths(root=self.users / self._user_name / "src" / "haiv_user")

    @property
    def state(self) -> Path:
        """User state directory. Raises if no user detected."""
        if self._user_name is None:
            raise RuntimeError("No user identity found...")
        return self.users / self._user_name / "state"
```

---

## New Command: hv users new (TODO)

**Location:** `haiv_core/commands/users/new.py`

**Usage:** `hv users new --name casey`

**Behavior:**
1. Validate name (alphanumeric, lowercase, no spaces)
2. Check `users/{name}/` doesn't exist
3. Create directory structure:
   ```
   users/{name}/
   ├── identity.toml        # Pre-populated with current env
   ├── pyproject.toml       # User-level dependencies
   ├── src/haiv_user/
   │   ├── __init__.py
   │   └── commands/
   │       └── __init__.py
   └── state/
       └── .gitkeep
   ```
4. Print success message with next steps

**Flags:**
- `--name` (required): User folder name
- `--force`: Overwrite existing (for recovery)

---

## Implementation Status

### Phase A: Core Identity Module ✓

- [x] `CurrentEnv` dataclass - source of truth for match fields
- [x] `Identity` dataclass
- [x] `AmbiguousIdentityError` exception
- [x] `IdentityLoadError` exception
- [x] `valid_match_fields()` - returns field names from CurrentEnv
- [x] `get_current_env()` - gather git/system info using Git class
- [x] `load_match_config(path)` - parse identity.toml [match] section
- [x] `matches(match_config, env)` - case-insensitive matching
- [x] `detect_user(users_dir)` - main entry point
- [x] 32 tests in `haiv/tests/test_identity.py`

### Phase B: CLI Integration ✓

- [x] `_detect_user_cached()` - cached user detection
- [x] `_get_user_commands()` - load haiv_user commands via Paths
- [x] Updated `_find_command()` - haiv_user → haiv_project → haiv_core precedence
- [x] No user = error shown as unchecked source with helpful message
- [x] 4 integration tests in `haiv-cli/tests/test_command_sources.py`

### Phase C: Paths Extension ✓

- [x] `_user_name` field on Paths dataclass
- [x] `paths.users` property
- [x] `paths.user` property (throws if no user)
- [x] `paths.state` property (throws if no user)

### Phase C.5: Context Integration ✓

- [x] `build_ctx()` accepts `haiv_username` parameter
- [x] CLI passes detected username to `build_ctx`
- [x] `haiv/test.py` uses `TEST_USERNAME = "testinius"` as default
- [x] Test utilities auto-create `users/testinius/state/` folder
- [x] `Sandbox` respects `explicit` mode (no auto-creation when True)

### Phase D: hv users new Command

- [ ] Create `haiv_core/commands/users/new.py`
- [ ] Templates in `haiv_core/__assets__/users/`
- [ ] Tests for user creation

---

## Success Criteria

- [x] User commands (`haiv_user`) are discoverable when user exists
- [x] Precedence: haiv_user → haiv_project → haiv_core
- [x] Multiple users on same machine can use different identities
- [x] Matching is case-insensitive (using casefold())
- [x] Ambiguous matches raise clear error with paths
- [ ] `hv users new --name casey` creates valid user structure
- [ ] Running `hv` in a project shows user detection info if no user
- [ ] Session caching works (HV_SESSION - deferred)
