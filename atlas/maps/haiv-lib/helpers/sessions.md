# sessions

Session persistence and lifecycle. Sessions track mind assignments — who's doing what, who delegated it, and what state it's in.

**Location:** `worktrees/main/haiv-lib/src/haiv/helpers/sessions.py`

---

## Session dataclass

```
id: str                         # UUID, primary key
task: str                       # Short summary (commit-title style)
started: datetime               # When created
mind: str                       # Mind name
short_id: int                   # Rolling integer for human reference
status: str                     # "staged" or "started"
parent_id: str                  # Parent session UUID (empty = human root)
description: str                # Long-form body
branch: str                     # Mind's worktree branch
base_branch: str                # Branch the worktree was created from
claude_session_id: str          # Current Claude Code session ID
old_claude_session_ids: list    # Previous Claude session IDs (rotated on restart)
```

## Storage

- Stored in `sessions.ig.toml` (git-ignored), per user
- TOML array of tables, most-recent-first
- Capped at 20 entries (`MAX_SESSIONS`), oldest dropped
- One active session per mind — `create_session` removes any existing session for the same mind

## Serialization conventions

`_session_to_dict` uses **conditional inclusion**: optional fields are omitted when empty/default, keeping the TOML clean. When adding new fields, follow this pattern — omit when default, include when non-default. This means existing sessions don't need migration; they'll just lack new fields and get defaults on load.

## Lifecycle

1. **`create_session`** — creates with status "staged", generates UUID and short_id
2. **`resolve_session`** — transitions staged → started, sets `claude_session_id`. Creates a new session if none exists.
3. **`update_session`** — mutator callback pattern. Pass a function that modifies the session in place; handles load/save and `claude_session_id` rotation automatically.
4. **`remove_session`** — deletes by ID

## Key functions

| Function | Purpose |
|---|---|
| `create_session(file, task, mind, ...)` | Create and save a new session |
| `load_sessions(file)` | Load all sessions from TOML |
| `get_current_session(file)` | Get session from `HV_SESSION` env var |
| `get_most_recent_session_for_mind(file, name)` | Find a mind's latest session |
| `get_session(file, identifier)` | Find by short_id (numeric) or UUID prefix |
| `find_session(file, session_id)` | Find by UUID prefix |
| `update_session(file, id, mutator)` | Mutate and save |
| `resolve_session(file, mind, ...)` | Ensure a started session exists |
| `remove_session(file, id)` | Delete a session |
| `build_session_tree(sessions)` | Build delegation tree from parent_id links |

## Related

- [stage](../../haiv-core/commands/stage.md) — creates sessions
- [pop](../../haiv-core/commands/pop.md) — removes sessions
- `resolvers/session.py` — resolves session identifiers to `Session` objects via `get_session()`
