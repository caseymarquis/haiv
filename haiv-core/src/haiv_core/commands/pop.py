"""hv pop - Wind down a mind's assignment.

Guides a mind through the steps to cleanly finish work:
review, commit, merge, and remove session.

With no flags, prints a checklist to follow. Flags automate
individual steps.
"""

from __future__ import annotations

import shutil

from haiv import cmd
from haiv.errors import CommandError
from haiv.helpers.sessions import find_session, get_current_session, remove_session
from haiv.paths import MindPaths


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
                description="Remove current session (auto-detected from HV_SESSION)",
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
    """Print the wind-down checklist, scaffolding an AAR for the parent mind."""
    session = get_current_session(ctx.paths.user.sessions_file)
    parent = find_session(ctx.paths.user.sessions_file, session.parent_id) if session.parent_id else None

    aar_item = None
    if parent:
        parent_paths = MindPaths(root=ctx.paths.user.minds_dir / parent.mind, haiv_root=ctx.paths.root)
        aar_path = parent_paths.work.aars_dir / f"{session.as_filename()}.md"
        parent_paths.work.aars_dir.mkdir(parents=True, exist_ok=True)
        ctx.templates.write("pop/aar.md.j2", aar_path, skip_existing=True, task=session.task)
        aar_rel = aar_path.relative_to(ctx.paths.root)
        aar_item = f"Fill in your AAR at `{aar_rel}`. (This lives in {parent.mind}'s directory — you write it, they read it.)"

    cd_to = ctx.paths.root.relative_to(ctx.paths.called_from, walk_up=True)
    if cd_to != ".":
        merge_step = f'Run `cd "{cd_to}" && hv pop --merge`'
    else:
        merge_step = "Run `hv pop --merge`"

    items = [
        "Review your original assignment for gaps in completion.",
        "Review for small improvements that are easy to add.",
        "Discuss your findings.",
        "Ensure proper test coverage and run tests.",
        "Commit all changes to your worktree branch.",
    ]
    if aar_item:
        items.append(aar_item)
    items.append(merge_step)
    items.append("Run `hv pop --session`")

    ctx.mind.checklist(
        postamble=(
            "This is an opportunity to consider your work as a whole "
            "and ensure it is aligned with the spirit of the original task."
        ),
        items=items,
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
            f"  To remove manually: hv sessions {session.short_id} remove"
        )

    parent = find_session(ctx.paths.user.sessions_file, session.parent_id)
    if not parent:
        raise CommandError(
            f"Parent session not found: {session.parent_id}\n"
            f"  To remove manually: hv sessions {session.short_id} remove"
        )

    mind_name = session.mind

    # Notify parent mind about the AAR (best-effort, pane may not exist)
    parent_paths = MindPaths(root=ctx.paths.user.minds_dir / parent.mind, haiv_root=ctx.paths.root)
    aar_path = parent_paths.work.aars_dir / f"{session.as_filename()}.md"
    aar_rel = aar_path.relative_to(ctx.paths.root)
    ctx.tui.mind_try_send_text(
        parent.mind,
        f"<haiv>{mind_name} finished. Their work has been reviewed and merged into your worktree. Please read '{aar_rel}'</haiv>",
    )

    remove_session(ctx.paths.user.sessions_file, session.id)

    # Clear work/ directory for next assignment
    work_dir = ctx.paths.user.minds_dir / mind_name / "work"
    if work_dir.exists():
        shutil.rmtree(work_dir)
        work_dir.mkdir()

    ctx.tui.sessions_refresh()
    ctx.tui.mind_launch(parent.mind)
    ctx.tui.mind_close_pane(mind_name)
