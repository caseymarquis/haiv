"""hv chart explore - Guided codebase exploration.

A cyclic tool that walks you through exploring the codebase one file
at a time, building the atlas as you go. Each step is small, focused,
and leaves something behind for the next explorer.

The cycle: plan -> embark -> read -> reflect -> plan -> ...
"""

from haiv import cmd
from haiv.helpers.chart import (
    embark,
    ensure_chart_templates,
    finish_journey,
    load_exploration,
    log_research,
    plan_next,
    prompt_for_name,
    reflect,
    show_status,
    start_journey,
)
from haiv.helpers.sessions import get_current_session
from haiv.paths import MindPaths
from haiv.templates import TemplateRenderer


def define() -> cmd.Def:
    return cmd.Def(
        description="Guided codebase exploration — run bare for status, flags for each step",
        flags=[
            cmd.Flag("log", type=bool, description="Record that your research log (001) is written"),
            cmd.Flag("plan", type=bool, description="Think about where to go next"),
            cmd.Flag("embark", description="Commit to a destination and go"),
            cmd.Flag("reflect", type=bool, description="Process what you found"),
            cmd.Flag("return", type=bool, description="End the journey and come home"),
            cmd.Flag("goal", description="What you're curious about (used when starting)"),
            cmd.Flag("name", description="Journey name (used when starting)"),
        ],
    )


def execute(ctx: cmd.Ctx) -> None:
    mind = _get_mind_paths(ctx)
    state = load_exploration(mind)
    atlas = ctx.paths.atlas

    bundled_dir = ctx.paths.pkgs.current.assets_dir / "chart"
    chart_templates_dir = ensure_chart_templates(
        atlas.templates_dir / "chart",
        bundled_dir,
    )
    templates = TemplateRenderer(chart_templates_dir)

    if ctx.args.has("log"):
        ctx.print(log_research(mind, state, atlas))
    elif ctx.args.has("plan"):
        ctx.print(plan_next(mind, state, atlas, templates))
    elif ctx.args.has("embark"):
        ctx.print(embark(mind, state, atlas, ctx.args.get_one("embark"), templates))
    elif ctx.args.has("reflect"):
        ctx.print(reflect(mind, state, templates))
    elif ctx.args.has("return"):
        ctx.print(finish_journey(mind, state, atlas, templates))
    elif state is None:
        _start_or_prompt(ctx, mind, templates)
    else:
        ctx.print(show_status(state))


def _get_mind_paths(ctx: cmd.Ctx) -> MindPaths:
    session = get_current_session(ctx.paths.user.sessions_file)
    return MindPaths(root=ctx.paths.user.minds_dir / session.mind, haiv_root=ctx.paths.root)


def _start_or_prompt(ctx: cmd.Ctx, mind: MindPaths, templates: TemplateRenderer) -> None:
    name = ctx.args.get_one("name", default_value=None)
    goal = ctx.args.get_one("goal", default_value=None)

    if not name:
        ctx.print(prompt_for_name(goal, templates))
        return

    session = get_current_session(ctx.paths.user.sessions_file)
    bundled_dir = ctx.paths.pkgs.current.assets_dir / "chart" / "example-journey"

    ctx.print(start_journey(
        atlas=ctx.paths.atlas,
        mind=mind,
        name=name,
        goal=goal,
        mind_name=session.mind,
        bundled_examples_dir=bundled_dir,
        templates=templates,
    ))
