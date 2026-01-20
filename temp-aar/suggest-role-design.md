# After Action Report: Design `mg minds suggest_role` Command

**Date:** 2026-01-15
**Task:** Design command and supporting infrastructure for suggesting roles based on a mind's task

---

## Summary

Designed the `mg minds suggest_role` command and discovered it requires broader infrastructure: a generalized Claude helper for AI-powered matching, a roles helper for discovery, and caching infrastructure for testability. Created API skeletons and a work breakdown for delegation.

## Design Process

Used consumer-first API design:
1. Identified the real use case (suggest_role command)
2. Wrote ideal calling code first
3. Iterated on the surface until clear
4. Worked backward to supporting infrastructure

This approach was added to the generalist role documentation.

## Designed Interfaces

### Claude Helper (`mg/src/mg/helpers/claude.py`)

Generalized AI-powered item matching, not role-specific:

```python
@dataclass
class MatchOption:
    id: str        # Unique identifier
    context: str   # Content for Claude to evaluate

class MatchCertainty(Enum):
    STRONG = "strong"
    GOOD = "good"
    PARTIAL = "partial"
    WEAK = "weak"
    NONE = "none"

@dataclass
class ItemMatch:
    id: str
    certainty: MatchCertainty
    explanation: str

@dataclass
class MatchingResult:
    matches: list[ItemMatch]
    summary: str
    needs_new: bool
    new_suggestion: str | None

def identify_matching_items(
    options: list[T],
    key_context: str,
    key_context_description: str,
    as_option: Callable[[T], MatchOption],
) -> MatchingResult:
    ...
```

### Roles Helper (`mg/src/mg/helpers/roles.py`)

```python
@dataclass
class Role:
    name: str      # Filename without .md
    path: Path
    purpose: str   # From **Purpose:** line
    content: str

def discover_roles(packages: list[PackageInfo]) -> list[Role]: ...
def parse_role(path: Path) -> Role: ...
```

### Packages Helper Addition (`mg/src/mg/helpers/packages.py`)

```python
def discover_all_packages(ctx: cmd.Ctx) -> list[PackageInfo]:
    """Convenience wrapper for commands."""
```

## Key Decisions

1. **Generalized matching over role-specific:** `identify_matching_items` works with any item type via `as_option` callable, enabling reuse for process documents, etc.

2. **MatchOption as dataclass, not tuple:** Better API clarity at call sites despite slight verbosity.

3. **Caching is general-purpose:** Not test-specific. Useful for development iteration and cost control.

4. **Roles helper takes packages list:** Caller owns package discovery, keeping roles helper focused.

5. **Problem descriptions over solutions:** Work packages describe problems to solve, not prescribed implementations.

## Work Packages Identified

| WP | Description | Dependencies |
|----|-------------|--------------|
| WP1 | Convert `mg/test.py` to module | None |
| WP2 | Claude caching infrastructure | None (needs design) |
| WP3 | Implement `identify_matching_items` | WP2 |
| WP4 | Implement roles helper | None |
| WP5 | Implement `suggest_role` command | WP3, WP4 |
| WP6 | Test infrastructure enhancements | WP1, WP2 |

**Can start immediately:** WP1, WP4
**Needs design first:** WP2

## Files Created/Modified

**Created (skeletons):**
- `worktrees/suggest-role/mg/src/mg/helpers/claude.py`
- `worktrees/suggest-role/mg/src/mg/helpers/roles.py`

**Modified:**
- `worktrees/suggest-role/mg/src/mg/helpers/packages.py` - Added `discover_all_packages()`
- `src/mg_project/__assets__/roles/generalist.md` - Added API design process

## Open Questions

- Where should caching infrastructure live?
- How to best organize `mg/test/` module split?
- Cache storage format and refresh mechanism?

## References

- Detailed plan: `users/casey/state/minds/_new/sage/startup/immediate-plan.md`
- Worktree: `worktrees/suggest-role/`
