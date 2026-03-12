"""hv chart - Navigate and extend the atlas.

Helps a mind find what they need in the codebase, and when they
venture beyond what's known, gives them the rules for charting
new territory.
"""

from haiv import cmd
from haiv.helpers.chart import ensure_chart_templates, get_briefing
from haiv.templates import TemplateRenderer


def define() -> cmd.Def:
    return cmd.Def(
        description="Navigate the atlas or explore uncharted territory",
        flags=[
            cmd.Flag("goal", description="What you're trying to find or accomplish"),
        ],
    )


def execute(ctx: cmd.Ctx) -> None:
    bundled_dir = ctx.paths.pkgs.current.assets_dir / "chart"
    chart_templates_dir = ensure_chart_templates(
        ctx.paths.atlas.templates_dir / "chart",
        bundled_dir,
    )
    templates = TemplateRenderer(chart_templates_dir)

    ctx.print(get_briefing(
        atlas=ctx.paths.atlas,
        goal=ctx.args.get_one("goal", default_value=None),
        templates=templates,
    ))
