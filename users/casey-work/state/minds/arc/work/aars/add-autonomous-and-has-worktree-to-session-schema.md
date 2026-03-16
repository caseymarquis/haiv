# AAR: add autonomous and has_worktree to session schema

## Summary

Added `autonomous: bool = False` and `has_worktree: bool = True` fields to the Session dataclass, with full support across load, save, create, and scaffold operations. All 710 existing tests pass; 12 new tests cover the additions.

## Key Decisions

- **`is not None` guards in `_session_to_dict`** — The existing string fields use truthiness checks (`if s.parent_id:`), which works because their defaults are falsy. For bools, truthiness would swallow `False`, so we use `is not None` instead. This was discussed with Casey. If more bool fields are added later, we may want to unify all fields to `is not None` for consistency.
- **Always write bool fields to TOML** — Rather than omitting default values (the pattern used for strings), bool fields are always written when not None. This is clearer for anyone reading the TOML — you can see the mode at a glance without needing to know the defaults.
- **Backward compatibility via `.get()` defaults** — Old sessions missing the new fields load cleanly with `autonomous=False` and `has_worktree=True`. No migration needed.

## Open Items

None.

## Commits and Files Changed

- 34c9140 add autonomous and has_worktree fields to session schema
  Key files: sessions.py, minds.py, test_sessions_helper.py, test_minds_helper.py
