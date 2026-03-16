"""hv minds stage - Prep a mind for a new task.

If minds exist without active sessions, one is selected at random for reuse.
Otherwise creates a new mind with proper structure (work/, home/, references.toml)
in users/{user}/state/minds/. Creates a worktree for the mind.

Creates a session with status "staged" so the TUI can display the mind
before it's started.
"""

from __future__ import annotations

import os
import random
import shutil

from haiv import cmd
from haiv._infrastructure.env import HV_SESSION
from haiv.errors import CommandError

from haiv.helpers.minds import (
    InvalidMindNameError,
    MindExistsError,
    generate_mind_name,
    list_minds,
    list_mind_paths,
    scaffold_mind,
    validate_mind_name,
)
from haiv.helpers.sessions import create_session, find_session, load_sessions
from haiv_core.haiv_hook_points import AFTER_WORKTREE_CREATED, WorktreeCreated


def define() -> cmd.Def:
    return cmd.Def(
        description="Prep a mind for a new task (run 'hv help --for minds.stage' before use)",
        enable_haiv_hooks=True,
        flags=[
            cmd.Flag(
                "task",
                type=str,
                min_args=0,
                max_args=1,
                description=(
                    "A short label for *you* to track this delegation — not instructions "
                    "for the new mind. Think git commit subject: 50 chars recommended, "
                    "72 max. Conventional commit style encouraged, e.g. "
                    '"feat(session): add timeout support". '
                    "The new mind's actual briefing goes in work/welcome.md, "
                    "which is created after staging."
                ),
            ),
            cmd.Flag(
                "description",
                type=str,
                min_args=0,
                max_args=1,
                description=(
                    "Optional additional context for *you*, the coordinator. "
                    "Like --task, this is a label for tracking — the new mind "
                    "does not see it. Their actual assignment goes in work/welcome.md."
                ),
            ),
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
            cmd.Flag(
                "autonomous",
                type=bool,
                description="Enable autonomous mode for the mind",
            ),
            cmd.Flag(
                "no-worktree",
                type=bool,
                description="Skip worktree creation",
            ),
            cmd.Flag(
                "allow-path",
                type=str,
                description=(
                    "Paths the mind is allowed to edit in autonomous mode. "
                    "The worktree path is included automatically when a worktree is created. "
                    "Use this to grant access to additional directories."
                ),
            ),
        ],
    )


def execute(ctx: cmd.Ctx) -> None:
    minds_dir = ctx.paths.user.minds_dir

    # --task is required
    help_hint = "  Run 'hv help --for minds.stage' for full details."
    if not ctx.args.has("task"):
        raise CommandError(
            "--task is missing.\n\n"
            "  It is HIGHLY recommended to read the help before using this command.\n"
            "  It explains what --task and --description are for, and what goes\n"
            "  in welcome.md instead.\n\n"
            f"{help_hint}"
        )

    task = ctx.args.get_one("task")
    if len(task) > 72:
        raise CommandError(
            f"--task is too long ({len(task)} chars, max 72).\n\n"
            "  --task is a short label for *you* to track this delegation.\n"
            "  The new mind's actual briefing goes in welcome.md, which is\n"
            "  created after staging.\n\n"
            f"{help_hint}"
        )
    if len(task) > 50:
        ctx.print(f"Hint: --task is {len(task)} chars (recommended: 50 or fewer)")
    description = ctx.args.get_one("description") if ctx.args.has("description") else ""
    autonomous = ctx.args.has("autonomous")
    no_worktree = ctx.args.has("no-worktree")

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

    # Worktree creation (skipped with --no-worktree)
    if no_worktree:
        branch = ""
        base_branch = ""
        location = None
    else:
        # Determine base branch
        if ctx.args.has("from-branch"):
            base_branch = ctx.args.get_one("from-branch")
        else:
            base_branch = _detect_base_branch(ctx)

        # Check that the base branch's working tree is clean
        if not ctx.args.has("allow-dirty"):
            _check_clean_working_tree(ctx, base_branch)

        # Try to clear stale worktree if one exists
        worktree_path = ctx.paths.root / "worktrees" / name
        if worktree_path.exists() and any(worktree_path.iterdir()):
            if not _try_remove_stale_worktree(ctx, name, base_branch):
                raise CommandError(
                    f"Worktree directory already exists and is not empty: worktrees/{name}/\n"
                    f"Use --name to choose a different mind name."
                )

        # Create the worktree
        ctx.git.run(
            ["worktree", "add", "-b", name, f"worktrees/{name}", base_branch],
            intent=f"create worktree for mind '{name}'",
        )
        location = f"worktrees/{name}/"
        branch = name

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

    # Build allowed paths for autonomous mode
    allowed_paths: list[str] = []
    if not no_worktree:
        allowed_paths.append(f"worktrees/{name}/")
    if ctx.args.has("allow-path"):
        allowed_paths.extend(ctx.args.get_list("allow-path"))

    # Scaffold mind (non-destructive for reused minds)
    try:
        mind = scaffold_mind(
            name, minds_dir, ctx.templates,
            location=location, skip_existing=reused_mind is not None,
            autonomous=autonomous, has_worktree=not no_worktree,
        )
    except MindExistsError as e:
        raise CommandError(str(e)) from e

    # Create session with status "staged"
    parent_id = os.environ.get(HV_SESSION, "")
    session = create_session(
        ctx.paths.user.sessions_file,
        task,
        name,
        status="staged",
        parent_id=parent_id,
        branch=branch,
        base_branch=base_branch,
        description=description,
        autonomous=autonomous,
        has_worktree=not no_worktree,
        allowed_paths=allowed_paths,
    )

    # Push to TUI
    ctx.tui.sessions_refresh()

    # Output guidance
    rel_path = mind.paths.root.relative_to(ctx.paths.root)
    if reused_mind:
        ctx.print(f"Reusing mind: {name}")
    else:
        ctx.print(f"Created mind: {name}")
    ctx.print(f"Location: {rel_path.as_posix()}")
    ctx.print(f"Task: {task}")
    ctx.print(f"Session: {session.short_id} (staged)")

    if not no_worktree:
        ctx.print(f"Worktree: worktrees/{name}/")

    welcome_path = mind.paths.work.root / "welcome.md"
    welcome_rel = welcome_path.relative_to(ctx.paths.root).as_posix()

    if autonomous:
        ctx.print()
        ctx.print("!! Autonomous mode: this mind will run without human approval for edits.")
        ctx.print("   Commit and push all branches before starting to protect against mistakes.")

    ctx.print()
    ctx.print("Next steps:")
    ctx.print(f"1. Edit {welcome_rel} — this is the assignment {name} reads when they wake up.")
    ctx.print("   (--task and --description are labels for *you* to track this delegation —")
    ctx.print(f"   {name} doesn't see them.)")
    ctx.print("2. Assign a role in references.toml (see src/haiv_project/__assets__/roles/)")
    ctx.print(f"3. Start: hv start {name}")


def _detect_base_branch(ctx: cmd.Ctx) -> str:
    """Detect base branch from the parent session.

    Looks up the parent session via HV_SESSION env var. If the parent
    has a branch recorded, uses that. If the parent has no branch (top-level),
    falls back to default_branch. Raises CommandError if HV_SESSION is not set.
    """
    parent_id = os.environ.get(HV_SESSION, "")
    if not parent_id:
        raise CommandError(
            "HV_SESSION is not set — cannot detect base branch.\n\n"
            "  Set it to your session ID:  export HV_SESSION=<your-session-id>\n"
            "  Or specify explicitly:      --from-branch <branch>"
        )

    parent_session = find_session(ctx.paths.user.sessions_file, parent_id)
    if parent_session and parent_session.branch:
        return parent_session.branch

    return ctx.settings.default_branch


def _try_remove_stale_worktree(ctx: cmd.Ctx, name: str, base_branch: str) -> bool:
    """Try to remove a stale worktree if it's empty or fully merged.

    Returns True if the worktree was successfully removed, False otherwise.
    """
    worktree_path = ctx.paths.root / "worktrees" / name

    # Case 1: directory exists but is not a git worktree (e.g. leftover empty dir)
    if not (worktree_path / ".git").exists():
        try:
            shutil.rmtree(worktree_path)
            return True
        except OSError:
            return False

    # Case 2: git worktree — check if branch is fully merged into base
    try:
        base_git = ctx.git.at_worktree(base_branch)
        ahead = base_git.run(
            ["rev-list", f"{base_branch}..{name}", "--count"],
            intent=f"check if '{name}' has commits ahead of '{base_branch}'",
        ).strip()
        if int(ahead) > 0:
            return False
        ctx.git.run(
            ["worktree", "remove", f"worktrees/{name}"],
            intent=f"remove stale worktree for '{name}'",
        )
        base_git.run(["branch", "-d", name], intent=f"delete stale branch '{name}'")
        return True
    except Exception:
        return False


def _check_clean_working_tree(ctx: cmd.Ctx, base_branch: str) -> None:
    """Raise CommandError if the base branch's working tree has uncommitted changes."""
    worktree_path = ctx.git.worktree_path_for_branch(base_branch)
    if worktree_path is None:
        return  # Branch not checked out, nothing to check

    status = ctx.git.at_path(worktree_path).run(
        ["status", "--porcelain"], intent="check working tree status"
    ).strip()
    if status:
        raise CommandError(
            f"Working tree for '{base_branch}' has uncommitted changes.\n\n"
            f"Commit your changes before staging a new mind."
        )
