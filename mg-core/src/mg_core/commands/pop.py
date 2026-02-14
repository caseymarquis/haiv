"""mg pop - Wind down a mind's assignment.

Guides a mind through the steps to cleanly finish work:
review, commit, merge, and remove session.

With no flags, prints a checklist to follow. Flags automate
individual steps.
"""

from __future__ import annotations

from mg import cmd
from mg.errors import CommandError
from mg.helpers.sessions import find_session, get_current_session, remove_session


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
    cd_to = ctx.paths.root.relative_to(ctx.paths.called_from, walk_up=True)
    if cd_to != ".":
        merge_step = f'Run `cd "{cd_to}" && mg pop --merge`'
    else:
        merge_step = "Run `mg pop --merge`"

    ctx.mind.checklist(
        postamble=(
            "This is an opportunity to consider your work as a whole "
            "and ensure it is aligned with the spirit of the original task."
        ),
        items=[
            "Review your original assignment for gaps in completion.",
            "Review for small improvements that are easy to add.",
            "Discuss your findings.",
            "Ensure proper test coverage and run tests.",
            "Commit all changes to your worktree branch.",
            merge_step,
            "Run `mg pop --session`",
        ],
    )


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

    # Check if the branch still exists
    base_git = ctx.git.at_worktree(base_branch)
    branch_exists = base_git.run(
        f"branch --list {branch}", intent=f"check if branch '{branch}' exists",
    ).strip()

    if not branch_exists:
        ctx.print(
            f"Branch '{branch}' is missing. This is expected if changes were\n"
            f"already synced or --merge was previously run."
        )
        return

    # Check if branch has commits to merge
    ahead = base_git.run(
        f"rev-list {base_branch}..{branch} --count",
        intent=f"check if '{branch}' has commits ahead of '{base_branch}'",
    ).strip()

    if int(ahead) > 0:
        base_git.run(f"merge {branch}", intent=f"merge '{branch}' into '{base_branch}'")
    else:
        ctx.print(f"'{branch}' has no new commits vs '{base_branch}', skipping merge.")

    # Remove the worktree and branch (delete from base so git sees it as merged)
    ctx.git.run(f"worktree remove worktrees/{branch}", intent=f"remove worktree for '{branch}'")
    base_git.run(f"branch -d {branch}", intent=f"delete branch '{branch}'")


def _do_session(ctx: cmd.Ctx) -> None:
    """Remove the current session, launch parent, and close pane."""
    session = get_current_session(ctx.paths.user.sessions_file)

    if not session.parent_id:
        raise CommandError(
            f"Session [{session.short_id}] has no parent session.\n"
            f"  To remove manually: mg sessions {session.short_id} remove"
        )

    parent = find_session(ctx.paths.user.sessions_file, session.parent_id)
    if not parent:
        raise CommandError(
            f"Parent session not found: {session.parent_id}\n"
            f"  To remove manually: mg sessions {session.short_id} remove"
        )

    mind_name = session.mind
    remove_session(ctx.paths.user.sessions_file, session.id)
    ctx.tui.sessions_refresh()
    ctx.tui.mind_launch(parent.mind)
    ctx.tui.mind_close_pane(mind_name)
