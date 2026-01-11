"""mg minds new - Scaffold a new mind folder.

Creates a new mind with proper startup structure in users/{user}/state/minds/_new/.
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
        ],
    )


def execute(ctx: cmd.Ctx) -> None:
    minds_dir = ctx.paths.user.minds_dir

    # Get or generate name
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

    # Scaffold the mind
    try:
        mind = scaffold_mind(name, minds_dir, ctx.templates)
    except MindExistsError as e:
        raise CommandError(str(e)) from e

    # Output guidance
    rel_path = mind.paths.root.relative_to(ctx.paths.root)
    ctx.print(f"Created mind: {name}")
    ctx.print(f"Location: {rel_path}")
    ctx.print()
    ctx.print("Next steps:")
    ctx.print("1. Edit startup/welcome.md with task context for this mind")
    ctx.print(f"2. Run: mg minds suggest_role --name {name}")
    ctx.print(f'3. Start the mind: mg start {name} --tmux --task "description"')
