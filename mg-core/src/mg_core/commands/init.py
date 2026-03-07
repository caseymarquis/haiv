"""Initialize haiv in current directory."""

from pathlib import Path

from haiv import cmd
from haiv.errors import CommandError
from haiv.wrappers.git import Git


def define() -> cmd.Def:
    """Define the init command."""
    return cmd.Def(
        description="Initialize haiv in current directory",
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
    git_root = _find_git_root(ctx.paths.called_from)

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


def _write_hv_state_files(root: Path, ctx: cmd.Ctx) -> None:
    """Write all haiv files to root directory."""
    ctx.templates.write("init/CLAUDE.md.j2", root / "CLAUDE.md")
    ctx.templates.write("init/.gitignore.j2", root / ".gitignore")
    ctx.templates.write("init/pyproject.toml.j2", root / "pyproject.toml")

    claude_dir = root / ".claude"
    ctx.templates.write("init/.claude/.gitkeep.j2", claude_dir / ".gitkeep")

    hv_project = root / "src" / "hv_project"
    ctx.templates.write("init/src/hv_project/__init__.py.j2", hv_project / "__init__.py")

    commands = hv_project / "commands"
    ctx.templates.write("init/src/hv_project/commands/__init__.py.j2", commands / "__init__.py")

    tests = root / "tests"
    ctx.templates.write("init/tests/__init__.py.j2", tests / "__init__.py")
    ctx.templates.write("init/tests/test_example.py.j2", tests / "test_example.py")

    users = root / "users"
    ctx.templates.write("init/users/.gitkeep.j2", users / ".gitkeep")

    worktrees = root / "worktrees"
    ctx.templates.write("init/worktrees/.gitignore.j2", worktrees / ".gitignore")


def _init_hv_structure(git: Git, ctx: cmd.Ctx) -> None:
    """Create base haiv structure: git init, orphan branch, initial commit, worktrees dir."""
    git.run("init", intent="create git repository")
    git.run("checkout --orphan haiv", intent="create haiv orphan branch")

    _write_hv_state_files(git.path, ctx)

    git.run("add .", intent="stage haiv files")
    git.run('commit -m "Initialize haiv"', intent="create initial commit")


def _create_orphan_worktree(git: Git, branch: str) -> Path:
    """Create orphan branch and worktree for fresh mode."""
    git.run(
        f"worktree add --orphan -b {branch} worktrees/{branch}",
        intent=f"create worktree for {branch}",
    )
    return git.path / "worktrees" / branch

def _print_next_steps(ctx: cmd.Ctx, *, branch: str, quiet: bool) -> None:
    """Print next steps after initialization."""
    if quiet:
        return
    ctx.print()
    ctx.print(f"'worktrees/{branch}/' is your initial worktree.")
    ctx.print(f"Use 'haiv worktree add <branch>' to add worktrees.")


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
    """Initialize haiv in a directory that's not in a git repo."""
    root = ctx.paths.called_from

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
    """Initialize haiv in an empty directory."""
    root = ctx.paths.called_from
    git = Git(root, quiet=quiet)

    _init_hv_structure(git, ctx)

    worktree_path = _create_orphan_worktree(git, branch)
    worktree_git = Git(worktree_path, quiet=quiet)

    if empty:
        # Create empty initial commit
        worktree_git.run(
            'commit --allow-empty -m "Initial commit"',
            intent="create empty initial commit",
        )
    else:
        # Create README and commit
        (worktree_path / "README.md").write_text(f"# {branch}\n", encoding="utf-8")
        worktree_git.run("add README.md", intent="stage README")
        worktree_git.run('commit -m "Initial commit"', intent="create initial commit")

    _print_next_steps(ctx, branch=branch, quiet=quiet)


def _init_fresh_nonempty(
    ctx: cmd.Ctx,
    *,
    quiet: bool,
    branch: str,
) -> None:
    """Initialize haiv in a non-empty directory (--force required)."""
    root = ctx.paths.called_from
    git = Git(root, quiet=quiet)

    # Collect existing files before creating structure
    existing_files = list(root.iterdir())

    _init_hv_structure(git, ctx)
    worktree_path = _create_orphan_worktree(git, branch)

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
    """Initialize haiv as a peer to an existing git repo."""
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
    peer_dir = git_root.parent / f"{git_root.name}-hv"

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

    # Check if local branch is ahead of remote (unpushed commits)
    ahead_count = _commits_ahead_of_remote(source_git, target_branch)
    if ahead_count > 0:
        if force:
            if not quiet:
                ctx.print(f"Warning: {ahead_count} unpushed commit(s) will not be in the clone.")
        else:
            raise CommandError(
                f"Branch '{target_branch}' is {ahead_count} commit(s) ahead of remote.\n\n"
                f"Push your changes first, or use --force to proceed anyway.\n"
                f"(Unpushed commits won't be in the clone.)"
            )

    # Clone from remote (--no-checkout to skip checking out files)
    if not quiet:
        ctx.print(f"Cloning from {remote_url}...")
    Git(git_root, quiet=quiet).run(
        f'clone --no-checkout "{remote_url}" "{peer_dir}"',
        intent="clone repository",
    )

    # Set up haiv structure in peer directory
    git = Git(peer_dir, quiet=quiet)

    # Set up haiv branch
    if _has_remote_hv_state(git):
        git.run("switch haiv", intent="switch to existing haiv branch")
    else:
        git.run("switch --orphan haiv", intent="create haiv orphan branch")
        _write_hv_state_files(peer_dir, ctx)
        git.run("add .", intent="stage haiv files")
        git.run('commit -m "Initialize haiv"', intent="create initial commit on haiv")

    # Create worktree for target branch
    git.run(
        f"worktree add worktrees/{target_branch} {target_branch}",
        intent=f"create worktree for {target_branch}",
    )

    _print_next_steps(ctx, branch=target_branch, quiet=quiet)


def _has_remote_hv_state(git: Git) -> bool:
    """Check if haiv exists as a remote tracking branch after clone."""
    output = git.run("branch -r --list origin/haiv", intent="check for existing haiv")
    return bool(output.strip())


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


def _commits_ahead_of_remote(git: Git, branch: str) -> int:
    """Count how many commits the local branch is ahead of origin."""
    try:
        output = git.run(
            f"rev-list --count origin/{branch}..{branch}",
            intent=f"check if '{branch}' is ahead of remote",
        )
        return int(output.strip())
    except Exception:
        return 0
