# Immediate Plan

## Design Decisions (agreed with Casey)

- **`autonomous: bool = False`** on Session — not a mode string, avoids uncontrolled growth
- **`has_worktree: bool = True`** on Session — explicit, defaults to true when parsing older sessions
- **One welcome template** with conditional sections (`{% if autonomous %}`, `{% if has_worktree %}`) — scales better than separate templates, friendlier for future project-level overrides
- **Location is creator-specified** — template includes placeholder spots for the managing mind to fill in
- **Pop adapts** — checklist varies based on session's `autonomous` and `has_worktree`; `--merge` is a graceful no-op without a worktree
- **Independent flags** on `hv minds stage`: `--autonomous`, `--no-worktree`

## Implementation Plan

### 1. Session schema (helpers/sessions.py)
- Add `autonomous: bool = False` to `Session` dataclass
- Add `has_worktree: bool = True` to `Session` dataclass
- Update `load_sessions` — default to `False`/`True` when fields missing (backward compat)
- Update `_session_to_dict` — conditional inclusion (omit when default value)
- Update `create_session` — accept new params

### 2. Stage command (commands/minds/stage.py)
- Add `--autonomous` flag (bool)
- Add `--no-worktree` flag (bool)
- Gate worktree creation (lines 132-156) on `not no_worktree`
- Gate hook emission on `not no_worktree`
- Pass `autonomous` and `has_worktree` to `create_session`
- Pass `autonomous` and `has_worktree` to `scaffold_mind` (for template rendering)
- Adapt output guidance for no-worktree case

### 3. Welcome template (__assets__/minds/welcome.md.j2)
- Add conditional "Before You Begin" section for autonomous vs collaborative
- Add conditional location/worktree guidance
- Add placeholder spots for managing mind to customize

### 4. Pop command (commands/pop.py)
- `--merge`: check `session.has_worktree`, no-op with message if false
- Checklist: omit worktree-specific steps when `not has_worktree`
- Checklist: adjust collaborative steps when `autonomous` (e.g., skip "discuss your findings")

### 5. scaffold_mind (helpers/minds.py)
- Accept and pass through `autonomous` and `has_worktree` to template renderer

## Sequencing

1 → 2 → 5 → 3 → 4 (session schema first since everything depends on it)

## Key References

- **Exploration journey:** `atlas/journeys/autonomous-mode-foundations/` (5 entries)
  - 002 — Session dataclass schema and helpers
  - 003 — Stage command flow and insertion points
  - 004 — Pop command flow and worktree assumptions
  - 005 — Welcome template structure
- **Maps:** `atlas/maps/commands/stage.md`, `atlas/maps/commands/pop.md`

## Not in scope (noted for later)
- `--no-commits` flag on staging
- Reusable staging profiles
- Project-level template overrides
