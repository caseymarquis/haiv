"""mg pop - Wind down a mind's assignment.

Guides a mind through the steps to cleanly finish work:
review, commit, merge, and remove session.

With no flags, prints a checklist to follow. Flags automate
individual steps.
"""

from __future__ import annotations

from mg import cmd
from mg.errors import CommandError
from mg.helpers.sessions import get_current_session, remove_session


def define() -> cmd.Def:
    return cmd.Def(
        description="Wind down a mind's assignment",
        flags=[
            cmd.Flag(
                "merge",
                type=bool,
                description="Merge branch into base branch and clean up worktree",
            ),
            cmd.Flag(
                "session",
                type=bool,
                description="Remove current session (auto-detected from MG_SESSION)",
            ),
        ],
    )


def execute(ctx: cmd.Ctx) -> None:
    if ctx.args.has("merge"):
        _do_merge(ctx)
    elif ctx.args.has("session"):
        _do_session(ctx)
    else:
        _print_checklist(ctx)


def _print_checklist(ctx: cmd.Ctx) -> None:
    """Print the wind-down checklist."""
    ctx.print("Create TODOs for the following items and work through them in order:")
    ctx.print()
    ctx.print("  1. Review your original assignment for gaps in completion.")
    ctx.print("  2. Review for small improvements that are easy to add.")
    ctx.print("  3. Discuss your findings.")
    ctx.print("  4. Ensure proper test coverage and run tests.")
    ctx.print("  5. Commit all changes to your worktree branch.")
    cd_to = ctx.paths.root.relative_to(ctx.paths.called_from, walk_up=True)
    if cd_to != ".":
        ctx.print(f"  6. Run `cd \"{cd_to}\" && mg pop --merge`")
    else:
        ctx.print("  6. Run `mg pop --merge`")

    ctx.print("  7. Run `mg pop --session`")


def _do_merge(ctx: cmd.Ctx) -> None:
    """Merge current branch into its base branch, then clean up."""
    session = get_current_session(ctx.paths.user.sessions_file)

    if not session.branch or not session.base_branch:
        raise CommandError(
            f"Session [{session.short_id}] is missing branch or base_branch metadata.\n"
            f"  branch: {session.branch!r}\n"
            f"  base_branch: {session.base_branch!r}"
        )

    branch = session.branch
    base_branch = session.base_branch
    if branch == base_branch:
        return
    if base_branch.empty():
        return

    # Merge from the base branch's worktree
    base_git = ctx.git.at_worktree(base_branch)
    base_git.run(f"merge {branch}", intent=f"merge '{branch}' into '{base_branch}'")

    # Remove the worktree and branch (delete from base so git sees it as merged)
    ctx.git.run(f"worktree remove worktrees/{branch}", intent=f"remove worktree for '{branch}'")
    base_git.run(f"branch -d {branch}", intent=f"delete branch '{branch}'")


def _do_session(ctx: cmd.Ctx) -> None:
    """Remove the current session."""
    session = get_current_session(ctx.paths.user.sessions_file)
    remove_session(ctx.paths.user.sessions_file, session.id)
    ctx.tui.sessions_refresh()
