"""mg minds new - Scaffold a new mind folder.

Creates a new mind with proper startup structure in users/{user}/state/minds/_new/.
Optionally creates a worktree for the mind to work in.
"""

from __future__ import annotations

from mg import cmd
from mg.errors import CommandError

from mg.helpers.minds import (
    InvalidMindNameError,
    MindExistsError,
    generate_mind_name,
    list_mind_paths,
    scaffold_mind,
    validate_mind_name,
)


def define() -> cmd.Def:
    return cmd.Def(
        description="Scaffold a new mind folder",
        flags=[
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

    # Get or generate mind name
    if ctx.args.has("name"):
        name = ctx.args.get_one("name")
    else:
        existing = [n for n, _ in list_mind_paths(minds_dir)]
        name = generate_mind_name(existing)

    # Validate name
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

    # Scaffold the mind
    try:
        mind = scaffold_mind(name, minds_dir, ctx.templates, location=location)
    except MindExistsError as e:
        raise CommandError(str(e)) from e

    # Output guidance
    rel_path = mind.paths.root.relative_to(ctx.paths.root)
    ctx.print(f"Created mind: {name}")
    ctx.print(f"Location: {rel_path}")

    if has_worktree:
        ctx.print(f"Worktree: worktrees/{worktree_name}/")

    ctx.print()
    ctx.print("Next steps:")
    ctx.print("1. Edit startup/welcome.md with task context for this mind")
    ctx.print(f"2. Run: mg minds suggest_role --name {name}")
    ctx.print(f'3. Start the mind: mg start {name} --tmux --task "description"')
