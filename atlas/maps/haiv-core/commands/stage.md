# stage

Prep a mind for a new task. Creates a worktree, scaffolds the mind's directory structure, and creates a session with status "staged."

**Location:** `worktrees/main/haiv-core/src/haiv_core/commands/minds/stage.py`

---

## Flags

- `--task` (required) — Short summary, commit-title style. 72 char max, 50 recommended.
- `--description` — Longer context for the task.
- `--name` — Mind name. If omitted, reuses an idle mind or auto-generates a name.
- `--from-branch` — Base branch for worktree. Defaults to parent session's branch or project default.
- `--allow-dirty` — Skip clean working tree check on the base branch.

## Flow

1. Validate `--task` (required, length check)
2. **Mind selection** — if no `--name`, looks for existing minds without active sessions and picks one at random for reuse. Otherwise uses the given name or auto-generates one.
3. Validate mind name (skipped for reused minds)
4. Determine base branch (`--from-branch` or auto-detect from parent session via `HV_SESSION`)
5. Check base branch's working tree is clean (unless `--allow-dirty`)
6. **Create worktree** — `git worktree add -b {name} worktrees/{name} {base_branch}`
7. **Emit hook** — `AFTER_WORKTREE_CREATED` with worktree path, branch, base_branch, mind_name
8. **Scaffold mind** — `scaffold_mind()` creates directory structure and writes templates into `users/{user}/state/minds/{name}/`
9. **Create session** — status "staged", records branch, base_branch, parent_id
10. Refresh TUI, print next steps

## Key details

- **Mind name = branch name = worktree folder name.** Tightly coupled — all three are the same string.
- **Mind reuse is the default path.** Prefers recycling idle minds over creating new ones.
- **Session created last.** Only after worktree + hook + scaffold all succeed.
- **`location` is a display string** passed to the welcome template (`"worktrees/{name}/"`), not a path object.
- **Base branch detection** reads the parent session's `branch` field. Falls back to `settings.default_branch` if the parent has no branch (top-level session).

## Related

- `helpers/sessions.py` — `create_session()` called in step 9
- `helpers/minds.py` — `scaffold_mind()` called in step 8
- `__assets__/minds/welcome.md.j2` — template rendered during scaffolding
- `haiv_hook_points.py` — `AFTER_WORKTREE_CREATED` definition
- Journey: `journeys/autonomous-mode-foundations/003`
