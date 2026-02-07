"""mg minds stage - Prep a mind for a new task.

If minds exist without active sessions, one is selected at random for reuse.
Otherwise creates a new mind with proper structure (work/, home/, references.toml)
in users/{user}/state/minds/. Optionally creates a worktree for the mind.

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
from mg.helpers.sessions import create_session, load_sessions


def define() -> cmd.Def:
    return cmd.Def(
        description="Prep a mind for a new task",
        flags=[
            cmd.Flag("task", type=str, description="Task summary (required)"),
            cmd.Flag("description", type=str, min_args=0, max_args=1, description="Long-form description"),
            cmd.Flag("name", type=str, min_args=0, max_args=1, description="Mind name"),
            cmd.Flag(
                "worktree",
                type=str,
                min_args=0,
                max_args=1,
                description="Create worktree (optional name, defaults to mind name)",
            ),
            cmd.Flag("no-worktree", type=bool, description="Create mind only"),
            cmd.Flag(
                "from-branch",
                type=str,
                min_args=0,
                max_args=1,
                description="Base branch for worktree (defaults to project default)",
            ),
        ],
    )


def execute(ctx: cmd.Ctx) -> None:
    minds_dir = ctx.paths.user.minds_dir

    # --task is required
    if not ctx.args.has("task"):
        raise CommandError("--task is required\n\n  mg minds stage --task \"description\" --worktree")

    task = ctx.args.get_one("task")
    description = ctx.args.get_one("description") if ctx.args.has("description") else ""

    # Check worktree flags (mutually exclusive, one required)
    has_worktree = ctx.args.has("worktree")
    has_no_worktree = ctx.args.has("no-worktree")

    if has_worktree and has_no_worktree:
        raise CommandError("Cannot use both --worktree and --no-worktree")

    if not has_worktree and not has_no_worktree:
        raise CommandError(
            "Must specify --worktree or --no-worktree\n\n"
            "  --worktree [name]  Create mind AND worktree (recommended)\n"
            "  --no-worktree      Create mind only"
        )

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

    # Handle worktree creation
    worktree_name: str | None = None
    location: str | None = None

    if has_worktree:
        # Get worktree name (from --worktree value, or default to mind name)
        worktree_values = ctx.args.get_list("worktree", default_value=[])
        if worktree_values:
            worktree_name = worktree_values[0]
        else:
            worktree_name = name

        # Check if worktree directory already exists and has contents
        worktree_path = ctx.paths.root / "worktrees" / worktree_name
        if worktree_path.exists() and any(worktree_path.iterdir()):
            raise CommandError(
                f"Worktree directory already exists and is not empty: worktrees/{worktree_name}/\n"
                f"Use a different worktree name or remove the existing directory."
            )

        # Get base branch
        if ctx.args.has("from-branch"):
            base_branch = ctx.args.get_one("from-branch")
        else:
            base_branch = ctx.settings.default_branch

        # Create the worktree
        ctx.git.run(
            f"worktree add -b {worktree_name} worktrees/{worktree_name} {base_branch}",
            intent=f"create worktree for mind '{name}'",
        )
        location = f"worktrees/{worktree_name}/"

    # Scaffold new mind or reuse existing
    if reused_mind:
        mind = reused_mind
    else:
        try:
            mind = scaffold_mind(name, minds_dir, ctx.templates, location=location)
        except MindExistsError as e:
            raise CommandError(str(e)) from e

    # Create session with status "staged"
    parent = os.environ.get(MG_SESSION, "")
    session = create_session(
        ctx.paths.user.sessions_file,
        task,
        name,
        status="staged",
        parent=parent,
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

    if has_worktree:
        ctx.print(f"Worktree: worktrees/{worktree_name}/")

    ctx.print()
    ctx.print("Next steps:")
    ctx.print("1. Edit work/welcome.md with task details")
    ctx.print("2. Assign a role in references.toml (see src/mg_project/__assets__/roles/)")
    ctx.print(f"3. Start: mg start {name}")
