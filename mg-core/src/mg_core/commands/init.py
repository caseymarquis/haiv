"""Initialize mg in current directory."""

from pathlib import Path

from mg import cmd
from mg.errors import CommandError
from mg.git import Git


def define() -> cmd.Def:
    """Define the init command."""
    return cmd.Def(
        description="Initialize mg in current directory",
        flags=[
            cmd.Flag("force", type=bool),
            cmd.Flag("branch"),
            cmd.Flag("empty", type=bool),
            cmd.Flag("quiet", type=bool),
        ],
    )


def execute(ctx: cmd.Ctx) -> None:
    """Execute the init command."""
    quiet = ctx.args.has("quiet")
    force = ctx.args.has("force")
    empty = ctx.args.has("empty")
    branch = ctx.args.get_one("branch", default_value=None)

    # Detect mode: are we in a git repo?
    git_root = _find_git_root(ctx.called_from)

    if git_root:
        _init_peer_mode(ctx, git_root=git_root, quiet=quiet, force=force, branch=branch)
    else:
        _init_fresh_mode(ctx, quiet=quiet, force=force, empty=empty, branch=branch or "main")


# =============================================================================
# Helpers
# =============================================================================


def _find_git_root(start: Path) -> Path | None:
    """Walk up from start to find .git directory. Returns repo root or None."""
    current = start.resolve()
    while current != current.parent:
        if (current / ".git").exists():
            return current
        current = current.parent
    return None


def _is_empty_dir(path: Path) -> bool:
    """Check if directory is empty (no files or subdirectories)."""
    return not any(path.iterdir())


def _init_mg_structure(git: Git, ctx: cmd.Ctx) -> None:
    """Create base mg structure: git init, orphan branch, initial commit, worktrees dir."""
    git.run("init", intent="create git repository")
    git.run("checkout --orphan mg-state", intent="create mg-state orphan branch")

    # Create CLAUDE.md from template and commit (required before creating branches)
    ctx.templates.write("init/CLAUDE.md.j2", git.path / "CLAUDE.md")
    git.run("add CLAUDE.md", intent="stage CLAUDE.md")
    git.run('commit -m "Initialize mg"', intent="create initial commit")

    (git.path / "worktrees").mkdir()


def _create_worktree(git: Git, branch: str) -> Path:
    """Create branch and worktree, return worktree path."""
    git.run(f"branch {branch}", intent=f"create {branch} branch")
    git.run(
        f"worktree add worktrees/{branch} {branch}",
        intent=f"create worktree for {branch}",
    )
    return git.path / "worktrees" / branch

def _print_next_steps(ctx: cmd.Ctx, *, branch: str, quiet: bool) -> None:
    """Print next steps after initialization."""
    if quiet:
        return
    ctx.print()
    ctx.print(f"'worktrees/{branch}/' is your initial worktree.")
    ctx.print(f"Use 'mg worktree add <branch>' to add worktrees.")


# =============================================================================
# Fresh Mode
# =============================================================================


def _init_fresh_mode(
    ctx: cmd.Ctx,
    *,
    quiet: bool,
    force: bool,
    empty: bool,
    branch: str,
) -> None:
    """Initialize mg in a directory that's not in a git repo."""
    root = ctx.called_from

    # Check if directory is non-empty
    if _is_empty_dir(root):
        _init_fresh_empty(ctx, quiet=quiet, empty=empty, branch=branch)
    elif force:
        _init_fresh_nonempty(ctx, quiet=quiet, branch=branch)
    else:
        raise CommandError(
            f"Directory is not empty. Use --force to move existing files "
            f"into worktrees/{branch}/"
        )


def _init_fresh_empty(
    ctx: cmd.Ctx,
    *,
    quiet: bool,
    empty: bool,
    branch: str,
) -> None:
    """Initialize mg in an empty directory."""
    root = ctx.called_from
    git = Git(root, quiet=quiet)

    _init_mg_structure(git, ctx)

    worktree_path = _create_worktree(git, branch)
    worktree_git = Git(worktree_path, quiet=quiet)

    if empty:
        # Create empty initial commit
        worktree_git.run(
            'commit --allow-empty -m "Initial commit"',
            intent="create empty initial commit",
        )
    else:
        # Create README and commit
        (worktree_path / "README.md").write_text(f"# {branch}\n")
        worktree_git.run("add README.md", intent="stage README")
        worktree_git.run('commit -m "Initial commit"', intent="create initial commit")

    _print_next_steps(ctx, branch=branch, quiet=quiet)


def _init_fresh_nonempty(
    ctx: cmd.Ctx,
    *,
    quiet: bool,
    branch: str,
) -> None:
    """Initialize mg in a non-empty directory (--force required)."""
    root = ctx.called_from
    git = Git(root, quiet=quiet)

    # Collect existing files before creating structure
    existing_files = list(root.iterdir())

    _init_mg_structure(git, ctx)
    worktree_path = _create_worktree(git, branch)

    # Move existing files into worktree
    for item in existing_files:
        if item.name in (".git", "worktrees"):
            continue
        dest = worktree_path / item.name
        item.rename(dest)

    # Commit moved files
    worktree_git = Git(worktree_path, quiet=quiet)
    worktree_git.run("add .", intent="stage moved files")
    worktree_git.run('commit -m "Initial commit"', intent="commit moved files")

    _print_next_steps(ctx, branch=branch, quiet=quiet)


# =============================================================================
# Peer Mode
# =============================================================================


def _init_peer_mode(
    ctx: cmd.Ctx,
    *,
    git_root: Path,
    quiet: bool,
    force: bool,
    branch: str | None,
) -> None:
    """Initialize mg as a peer to an existing git repo."""
    source_git = Git(git_root, quiet=True)  # Quiet for prerequisite checks

    # Check prerequisites
    remote_url = _get_remote_url(source_git)
    if remote_url is None:
        raise CommandError(
            "No remote configured.\n\n"
            "Peer mode requires a remote to clone from. Add one with:\n"
            "  git remote add origin <url>"
        )

    if not _is_clean_working_tree(source_git):
        if force:
            if not quiet:
                ctx.print("Warning: uncommitted changes will not be in the clone.")
        else:
            raise CommandError(
                "Working tree has uncommitted changes.\n\n"
                "Commit or stash changes first, or use --force to proceed anyway.\n"
                "(Uncommitted changes won't be in the clone.)"
            )

    # Determine peer directory location
    peer_dir = git_root.parent / f"{git_root.name}-mg"

    if peer_dir.exists():
        raise CommandError(f"Peer directory already exists: {peer_dir}")

    # Get branch to create worktree for (current branch if not specified)
    target_branch = branch or source_git.branch_current()

    # Verify target branch exists on remote (before cloning)
    if not _remote_has_branch(source_git, remote_url, target_branch):
        raise CommandError(
            f"Branch '{target_branch}' does not exist on remote.\n\n"
            f"Available branches can be listed with: git ls-remote --heads origin"
        )

    # Clone from remote (--no-checkout to skip checking out files)
    if not quiet:
        ctx.print(f"Cloning from {remote_url}...")
    Git(git_root, quiet=quiet).run(
        f'clone --no-checkout "{remote_url}" "{peer_dir}"',
        intent="clone repository",
    )

    # Set up mg structure in peer directory
    git = Git(peer_dir, quiet=quiet)

    # Create mg-state orphan branch (working tree is already empty)
    git.run("checkout --orphan mg-state", intent="create mg-state orphan branch")

    # Create CLAUDE.md and initial commit
    ctx.templates.write("init/CLAUDE.md.j2", peer_dir / "CLAUDE.md")
    git.run("add CLAUDE.md", intent="stage CLAUDE.md")
    git.run('commit -m "Initialize mg"', intent="create initial commit on mg-state")

    # Create worktrees directory
    (peer_dir / "worktrees").mkdir()

    # Create worktree for target branch
    git.run(
        f"worktree add worktrees/{target_branch} {target_branch}",
        intent=f"create worktree for {target_branch}",
    )

    _print_next_steps(ctx, branch=target_branch, quiet=quiet)


def _get_remote_url(git: Git) -> str | None:
    """Get the URL of the 'origin' remote, or None if not configured."""
    try:
        return git.run("remote get-url origin", intent="get remote URL").strip()
    except Exception:
        return None


def _is_clean_working_tree(git: Git) -> bool:
    """Check if working tree is clean (no staged, unstaged, or untracked files)."""
    status = git.run("status --porcelain", intent="check working tree status").strip()
    return status == ""


def _remote_has_branch(git: Git, remote_url: str, branch: str) -> bool:
    """Check if a branch exists on the remote."""
    try:
        output = git.run(
            f'ls-remote --heads "{remote_url}" {branch}',
            intent=f"check if branch '{branch}' exists on remote",
        )
        return bool(output.strip())
    except Exception:
        return False
