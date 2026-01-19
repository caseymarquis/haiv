# Immediate Plan: suggest_role Implementation

## Overview

**Role:** Project Manager - delegate work, don't implement.

**Goal:** Implement `mg minds suggest_role --name {mind}` command via sequential delegation.

**Worktree:** `worktrees/suggest-role/`

---

## Status

**Current phase:** Ready to delegate first work package

**Next action:** Create mind for WP4 (roles helper - no dependencies, straightforward)

---

## Completed Work

### claude helper skeleton (`mg/src/mg/helpers/claude.py`)

```python
class MatchCertainty(Enum):
    STRONG = "strong"    # Clearly fits
    GOOD = "good"        # Solid match
    PARTIAL = "partial"  # Some overlap
    WEAK = "weak"        # Tangential at best
    NONE = "none"        # Not relevant

@dataclass
class MatchOption:
    id: str        # Unique identifier
    context: str   # Content for Claude to evaluate

@dataclass
class ItemMatch:
    id: str                    # References MatchOption.id
    certainty: MatchCertainty
    explanation: str           # Why it matches (or doesn't)

@dataclass
class MatchingResult:
    matches: list[ItemMatch]   # Sorted by certainty (best first)
    summary: str               # Overall assessment
    needs_new: bool            # None of the options fit well
    new_suggestion: str | None # What kind of new item would help

def identify_matching_items(
    options: list[T],
    key_context: str,
    key_context_description: str,
    as_option: Callable[[T], MatchOption],
) -> MatchingResult:
    ...
```

### roles helper skeleton (`mg/src/mg/helpers/roles.py`)

```python
@dataclass
class Role:
    name: str      # Role identifier (filename without .md)
    path: Path     # Absolute path to the role file
    purpose: str   # Extracted purpose line
    content: str   # Full file content

def discover_roles(packages: list[PackageInfo]) -> list[Role]:
    """Discover roles from packages' __assets__/roles/ directories."""
    ...

def parse_role(path: Path) -> Role:
    """Parse a role file and extract metadata."""
    ...
```

### packages helper addition (`mg/src/mg/helpers/packages.py`)

```python
def discover_all_packages(ctx: cmd.Ctx) -> list[PackageInfo]:
    """Convenience wrapper for commands that need all packages."""
    ...
```

---

## Work Packages

### WP1: Convert `mg/test.py` to `mg/test/` module

**Location:** `mg/src/mg/`

**Current state:** Single 400-line file.

**Goal:** Convert to a module so we can add caching and other test infrastructure.

**Constraint:** Preserve public API - `from mg import test` must continue to work.

**Needs research:** How to best organize the split.

---

### WP2: Claude caching infrastructure

**Location:** TBD - likely `mg/src/mg/helpers/` (general purpose, not test-specific)

**Purpose:** Cache Claude responses to avoid repeated API calls. Useful for:
- Tests (deterministic, fast)
- Development (iterate without waiting)
- Cost control

**Research needed:**
- Where should this live? (helpers? separate module?)
- Cache storage format and location
- Integration pattern with `identify_matching_items`
- Refresh mechanism

**Not yet designed** - needs consumer-first API exploration.

---

### WP3: Implement `identify_matching_items`

**Location:** `mg/src/mg/helpers/claude.py`

**Problem:** Need to call Claude and get structured results matching our `MatchingResult` interface. Must handle the round-trip: our data structures → Claude → parsed response.

**Depends on:** WP2 (caching integration)

---

### WP4: Implement roles helper

**Location:** `mg/src/mg/helpers/roles.py`

**Tasks:**
1. Implement `parse_role(path)` - extract name, purpose, content
2. Implement `discover_roles(packages)` - search and deduplicate
3. Write unit tests

**No dependencies** - can proceed immediately.

---

### WP5: Implement `suggest_role` command

**Location:** `mg-core/src/mg_core/commands/minds/suggest_role.py`

**Intended calling code:**
```python
def execute(ctx: cmd.Ctx) -> None:
    mind = resolve_mind(ctx.args.get_one("name"), ctx.paths.user.minds_dir)

    if not mind.paths.welcome_file.exists():
        raise CommandError(f"No welcome.md found for {mind.name}")

    task = mind.paths.welcome_file.read_text()
    packages = discover_all_packages(ctx)
    roles = discover_roles(packages)

    if not roles:
        raise CommandError("No roles found")

    result = identify_matching_items(
        options=roles,
        key_context=task,
        key_context_description="A task assignment. Which roles fit?",
        as_option=lambda r: MatchOption(id=r.name, context=f"{r.purpose}\n\n{r.content}"),
    )

    # Output results...
```

**Depends on:** WP3, WP4

---

### WP6: Test infrastructure enhancements

**Location:** `mg/src/mg/test/`

**Problem:** Tests for commands using Claude need to:
- Set up minds and roles without verbose boilerplate
- Capture and verify command output
- Use cached Claude responses (from WP2)

**Intended test code:**
```python
def test_suggests_generalist_for_implementation_task(self, sandbox: Sandbox):
    sandbox.create_mind("robin", welcome="Implement OAuth2 feature...")
    sandbox.create_role("generalist", purpose="Own a feature end-to-end")
    sandbox.create_role("analyst", purpose="Research and produce documents")

    sandbox.run("minds suggest_role --name robin")
    output = sandbox.output()

    assert "generalist" in output
```

**Depends on:** WP1, WP2

---

## Delegation Sequence

Sequential delegation - one mind at a time:

1. **WP4** - Roles helper (no deps, straightforward start)
2. **WP1** - Test module refactor (no deps)
3. **WP2** - Caching infrastructure (needs design during WP1)
4. **WP3** - Claude helper implementation (after WP2)
5. **WP6** - Test infrastructure (after WP1, WP2)
6. **WP5** - Command integration (after WP3, WP4)

---

## Progress Tracker

| WP | Description | Mind | Status | AAR |
|----|-------------|------|--------|-----|
| WP4 | Roles helper | - | Not started | - |
| WP1 | Test module refactor | - | Not started | - |
| WP2 | Caching infrastructure | - | Not started | - |
| WP3 | Claude helper | - | Not started | - |
| WP6 | Test infrastructure | - | Not started | - |
| WP5 | Command integration | - | Not started | - |
