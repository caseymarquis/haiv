"""hv chart - Navigate and extend the atlas.

Helps a mind find what they need in the codebase, and when they
venture beyond what's known, gives them the rules for charting
new territory.
"""

from haiv import cmd
from haiv.helpers.chart import get_briefing


def define() -> cmd.Def:
    return cmd.Def(
        description="Navigate the atlas or explore uncharted territory",
        flags=[
            cmd.Flag("goal", description="What you're trying to find or accomplish"),
        ],
    )


def execute(ctx: cmd.Ctx) -> None:
    ctx.print(get_briefing(
        atlas=ctx.paths.atlas,
        goal=ctx.args.get_one("goal", default_value=None),
        templates=ctx.templates,
    ))
