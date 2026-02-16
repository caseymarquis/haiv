# After Action Report: `mg pop` Needs a No-Merge Worktree Cleanup Mode

**Date:** 2026-02-12
**Task:** Add parent-child tree display to sessions (echo worktree)

---

## Summary

During collaborative development, changes were committed directly to main instead of the assigned worktree branch. At wrap-up, `mg pop --merge` has nothing to merge but the worktree still needs cleanup.

## What Happened

Echo was assigned to work in `worktrees/echo/` on the echo branch. During iterative manual testing with the user, we started committing directly to `worktrees/main/` for faster feedback loops. The echo branch fell behind main — main has all the work, echo has only the early commits.

Running `mg pop --merge` would attempt to merge echo into main, which is either a no-op (already there) or confusing (echo is behind). What we actually need is just the worktree cleanup portion: remove the worktree, clean up the branch, close the session.

## Proposed Change

Add a `--no-merge` flag (or similar) to `mg pop` that skips the merge step and only performs cleanup:

- Remove the worktree
- Delete the branch
- Close the session

This covers the case where work was merged by other means (direct commits to main, manual merge, cherry-pick, etc.).

## Workaround

For now: manually clean up the worktree and branch, then run `mg pop --session` to close the session.
