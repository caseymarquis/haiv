# pop

Wind down a mind's assignment. Guides through review, merge, and session cleanup. Three modes depending on flags.

**Location:** `worktrees/main/haiv-core/src/haiv_core/commands/pop.py`

---

## Modes

### Bare — `hv pop`

Prints a checklist for the mind to follow:
1. Review assignment for completion gaps
2. Review for easy improvements
3. Discuss findings
4. Ensure test coverage, run tests
5. Commit all changes
6. Fill in AAR (if parent session exists — scaffolded in parent's `work/aars/`)
7. `hv pop --merge`
8. `hv pop --session`

Uses `ctx.mind.checklist()` to present the list. The AAR template (`pop/aar.md.j2`) is written to the parent mind's directory on first view (`skip_existing=True`).

### `--merge`

Merges the mind's branch into its base branch and cleans up the worktree.

1. Get current session, read `branch` and `base_branch`
2. **Hard fails if either is missing** — `CommandError`
3. Check if branch still exists (graceful if already merged)
4. Check if branch has commits ahead of base
5. Merge into base branch (from the base worktree)
6. Remove worktree, delete branch

### `--session`

Removes the session and cleans up the mind for reuse.

1. Get current session (requires `HV_SESSION`)
2. **Requires a parent session** — can't pop a root session this way
3. Notify parent mind via TUI (`mind_try_send_text` — best-effort)
4. Remove session from sessions file
5. **Clear `work/` directory** — `shutil.rmtree` then `mkdir`. This is mind recycling.
6. Refresh TUI, launch parent mind, close this mind's pane

## Key details

- **Merge assumes worktree exists.** No-worktree minds cannot use `--merge` — it will error on missing branch metadata.
- **Checklist is worktree-centric.** Steps like "commit all changes" and the merge step don't apply to worktree-less minds.
- **Session cleanup is mode-agnostic.** Removing sessions, clearing `work/`, and TUI operations work regardless of worktree status.
- **Mind recycling happens in `--session`.** After pop, the mind's `work/` is empty and ready for the next assignment.

## Related

- `helpers/sessions.py` — `get_current_session()`, `find_session()`, `remove_session()`
- `__assets__/pop/aar.md.j2` — AAR template scaffolded for parent mind
- Journey: `journeys/autonomous-mode-foundations/004`
