"""mg minds stage - Prep a mind for a new task.

If minds exist without active sessions, one is selected at random for reuse.
Otherwise creates a new mind with proper structure (work/, home/, references.toml)
in users/{user}/state/minds/. Creates a worktree for the mind.

Creates a session with status "staged" so the TUI can display the mind
before it's started.
"""

from __future__ import annotations

import os
import random

from mg import cmd
from mg._infrastructure.env import MG_SESSION
from mg.errors import CommandError

from mg.helpers.minds import (
    InvalidMindNameError,
    MindExistsError,
    generate_mind_name,
    list_minds,
    list_mind_paths,
    scaffold_mind,
    validate_mind_name,
)
from mg.helpers.sessions import create_session, find_session, load_sessions
from mg_core.mg_hook_points import AFTER_WORKTREE_CREATED, WorktreeCreated


def define() -> cmd.Def:
    return cmd.Def(
        description="Prep a mind for a new task",
        enable_mg_hooks=True,
        flags=[
            cmd.Flag("task", type=str, description="Task summary (required)"),
            cmd.Flag("description", type=str, min_args=0, max_args=1, description="Long-form description"),
            cmd.Flag("name", type=str, min_args=0, max_args=1, description="Mind name"),
            cmd.Flag(
                "from-branch",
                type=str,
                min_args=0,
                max_args=1,
                description="Base branch for worktree (defaults to parent's branch or project default)",
            ),
            cmd.Flag(
                "allow-dirty",
                type=bool,
                description="Skip clean working tree check",
            ),
        ],
    )


def execute(ctx: cmd.Ctx) -> None:
    minds_dir = ctx.paths.user.minds_dir

    # --task is required
    if not ctx.args.has("task"):
        raise CommandError("--task is required\n\n  mg minds stage --task \"description\"")

    task = ctx.args.get_one("task")
    description = ctx.args.get_one("description") if ctx.args.has("description") else ""

    # Check for available minds (no active session) when name not provided
    reused_mind = None
    if not ctx.args.has("name"):
        all_minds = list_minds(minds_dir, ctx.paths.root)
        sessions = load_sessions(ctx.paths.user.sessions_file)
        minds_with_sessions = {s.mind for s in sessions}
        available = [m for m in all_minds if m.name not in minds_with_sessions]

        if available:
            reused_mind = random.choice(available)

    # Get or generate mind name
    if reused_mind:
        name = reused_mind.name
    elif ctx.args.has("name"):
        name = ctx.args.get_one("name")
    else:
        existing = [n for n, _ in list_mind_paths(minds_dir)]
        name = generate_mind_name(existing)

    # Validate name (skip for reused minds)
    if not reused_mind:
        try:
            validate_mind_name(name)
        except InvalidMindNameError as e:
            raise CommandError(e.reason) from e

    # Determine base branch
    if ctx.args.has("from-branch"):
        base_branch = ctx.args.get_one("from-branch")
    else:
        base_branch = _detect_base_branch(ctx)

    # Check that the base branch's working tree is clean
    if not ctx.args.has("allow-dirty"):
        _check_clean_working_tree(ctx, base_branch)

    # Check if worktree directory already exists and has contents
    worktree_path = ctx.paths.root / "worktrees" / name
    if worktree_path.exists() and any(worktree_path.iterdir()):
        raise CommandError(
            f"Worktree directory already exists and is not empty: worktrees/{name}/\n"
            f"Use --name to choose a different mind name."
        )

    # Create the worktree
    ctx.git.run(
        f"worktree add -b {name} worktrees/{name} {base_branch}",
        intent=f"create worktree for mind '{name}'",
    )
    location = f"worktrees/{name}/"

    # Emit hook for post-worktree-creation tasks (e.g., uv sync)
    AFTER_WORKTREE_CREATED.emit(
        WorktreeCreated(
            worktree_path=worktree_path,
            branch=name,
            base_branch=base_branch,
            mind_name=name,
        ),
        ctx,
    )

    # Scaffold new mind or reuse existing
    if reused_mind:
        mind = reused_mind
    else:
        try:
            mind = scaffold_mind(name, minds_dir, ctx.templates, location=location)
        except MindExistsError as e:
            raise CommandError(str(e)) from e

    # Create session with status "staged"
    parent_id = os.environ.get(MG_SESSION, "")
    session = create_session(
        ctx.paths.user.sessions_file,
        task,
        name,
        status="staged",
        parent_id=parent_id,
        branch=name,
        base_branch=base_branch,
        description=description,
    )

    # Push to TUI
    ctx.tui.sessions_refresh()

    # Output guidance
    rel_path = mind.paths.root.relative_to(ctx.paths.root)
    if reused_mind:
        ctx.print(f"Reusing mind: {name}")
    else:
        ctx.print(f"Created mind: {name}")
    ctx.print(f"Location: {rel_path}")
    ctx.print(f"Task: {task}")
    ctx.print(f"Session: {session.short_id} (staged)")

    ctx.print(f"Worktree: worktrees/{name}/")

    ctx.print()
    ctx.print("Next steps:")
    ctx.print("1. Edit work/welcome.md with task details")
    ctx.print("2. Assign a role in references.toml (see src/mg_project/__assets__/roles/)")
    ctx.print(f"3. Start: mg start {name}")


def _detect_base_branch(ctx: cmd.Ctx) -> str:
    """Detect base branch from the parent session.

    Looks up the parent session via MG_SESSION env var. If the parent
    has a branch recorded, uses that. If the parent has no branch (top-level),
    falls back to default_branch. Raises CommandError if MG_SESSION is not set.
    """
    parent_id = os.environ.get(MG_SESSION, "")
    if not parent_id:
        raise CommandError(
            "MG_SESSION is not set — cannot detect base branch.\n\n"
            "  Set it to your session ID:  export MG_SESSION=<your-session-id>\n"
            "  Or specify explicitly:      --from-branch <branch>"
        )

    parent_session = find_session(ctx.paths.user.sessions_file, parent_id)
    if parent_session and parent_session.branch:
        return parent_session.branch

    return ctx.settings.default_branch


def _check_clean_working_tree(ctx: cmd.Ctx, base_branch: str) -> None:
    """Raise CommandError if the base branch's working tree has uncommitted changes."""
    worktree_path = ctx.git.worktree_path_for_branch(base_branch)
    if worktree_path is None:
        return  # Branch not checked out, nothing to check

    status = ctx.git.at_path(worktree_path).run(
        "status --porcelain", intent="check working tree status"
    ).strip()
    if status:
        raise CommandError(
            f"Working tree for '{base_branch}' has uncommitted changes.\n\n"
            f"Commit your changes before staging a new mind."
        )
