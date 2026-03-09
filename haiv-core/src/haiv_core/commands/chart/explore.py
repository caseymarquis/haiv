"""hv chart explore - Guided codebase exploration.

A cyclic tool that walks you through exploring the codebase one file
at a time, building the atlas as you go. Each step is small, focused,
and leaves something behind for the next explorer.

The cycle: plan -> embark -> read -> reflect -> plan -> ...
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from haiv import cmd
from haiv.errors import CommandError
from haiv.helpers.sessions import get_current_session
from haiv.paths import MindPaths


# --- State management ---

NEXT_STEP = {
    "new": "Write your research log (001), then run: hv chart explore --log",
    "research_logged": "Run: hv chart explore --plan",
    "planned": "Run: hv chart explore --embark <file-path>",
    "embarked": "Read the file, write your entry, then run: hv chart explore --reflect",
    "reflected": "Run: hv chart explore --plan  (or --return to finish)",
}


def _get_mind_paths(ctx: cmd.Ctx) -> MindPaths:
    session = get_current_session(ctx.paths.user.sessions_file)
    return MindPaths(root=ctx.paths.user.minds_dir / session.mind, haiv_root=ctx.paths.root)


def _load_state(mind: MindPaths) -> dict | None:
    path = mind.work.exploration_file
    if not path.exists():
        return None
    return json.loads(path.read_text())


def _save_state(mind: MindPaths, state: dict) -> None:
    mind.work.exploration_file.write_text(json.dumps(state, indent=2) + "\n")


def _journey_dir(ctx: cmd.Ctx, name: str) -> Path:
    return ctx.paths.atlas.journeys_dir / name


# --- Define ---

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


# --- Execute ---

def execute(ctx: cmd.Ctx) -> None:
    mind = _get_mind_paths(ctx)
    state = _load_state(mind)

    if ctx.args.has("log"):
        _do_log(ctx, mind, state)
    elif ctx.args.has("plan"):
        _do_plan(ctx, mind, state)
    elif ctx.args.has("embark"):
        _do_embark(ctx, mind, state)
    elif ctx.args.has("reflect"):
        _do_reflect(ctx, mind, state)
    elif ctx.args.has("return"):
        _do_return(ctx, mind, state)
    else:
        _do_status(ctx, mind, state)


def _require_state(state: dict | None) -> dict:
    if state is None:
        raise CommandError("No active journey. Run `hv chart explore` to start one.")
    return state


def _require_status(state: dict, allowed: tuple[str, ...], action: str) -> None:
    if state["status"] not in allowed:
        raise CommandError(
            f"Can't {action} right now. Status: {state['status']}\n"
            f"  {NEXT_STEP.get(state['status'], '')}"
        )


# --- Status (bare command) ---

def _do_status(ctx: cmd.Ctx, mind: MindPaths, state: dict | None) -> None:
    if state is None:
        _do_start(ctx, mind)
        return

    ctx.print(f"Journey: {state['journey']}")
    ctx.print(f"Entry: {state.get('entry', 1):03d}")
    ctx.print(f"Status: {state['status']}")
    ctx.print("")
    ctx.print(NEXT_STEP.get(state["status"], "Unknown state."))

    if state["status"] == "embarked":
        ctx.print(f"\nDestination: {state.get('destination', '?')}")


# --- Start ---

def _do_start(ctx: cmd.Ctx, mind: MindPaths) -> None:
    goal = ctx.args.get_one("goal", default_value=None)
    name = ctx.args.get_one("name", default_value=None)

    if not name:
        ctx.print(ctx.templates.render(
            "chart/explore-start-needs-name.md.j2", goal=goal,
        ))
        return

    journey_dir = _journey_dir(ctx, name)
    if journey_dir.exists():
        raise CommandError(f"Journey '{name}' already exists at {journey_dir}")

    # Create journey directory and research log
    journey_dir.mkdir(parents=True, exist_ok=True)

    session = get_current_session(ctx.paths.user.sessions_file)
    ctx.templates.write(
        "chart/research-log.md.j2",
        journey_dir / "001-research-log.md",
        mind=session.mind,
        date=date.today().isoformat(),
        goal=goal,
    )

    _save_state(mind, {
        "journey": name,
        "goal": goal,
        "status": "new",
        "entry": 1,
        "history": [],
    })

    ctx.print(ctx.templates.render(
        "chart/explore-start.md.j2",
        name=name,
        goal=goal,
        example_journey=_find_example_journey(ctx),
        journey_dir=journey_dir,
    ))


# --- Log ---

def _do_log(ctx: cmd.Ctx, mind: MindPaths, state: dict | None) -> None:
    state = _require_state(state)
    _require_status(state, ("new",), "log")

    journey_dir = _journey_dir(ctx, state["journey"])
    log_files = list(journey_dir.glob("001*"))

    if not log_files:
        ctx.print("Your research log (001) doesn't exist yet.")
        ctx.print(f"Create it at: {journey_dir / '001-research-log.md'}")
        return

    state["status"] = "research_logged"
    _save_state(mind, state)

    ctx.print("Research log recorded.")
    ctx.print("")
    ctx.print("Now it's time to plan your first destination. Run:")
    ctx.print("  hv chart explore --plan")


# --- Plan ---

def _do_plan(ctx: cmd.Ctx, mind: MindPaths, state: dict | None) -> None:
    state = _require_state(state)
    _require_status(state, ("research_logged", "reflected"), "plan")

    journey_dir = _journey_dir(ctx, state["journey"])
    entry = state["entry"]
    current_entries = sorted(journey_dir.glob(f"{entry:03d}*"))

    state["status"] = "planned"
    _save_state(mind, state)

    ctx.print(ctx.templates.render(
        "chart/explore-plan.md.j2",
        current_file=current_entries[0] if current_entries else None,
    ))


# --- Embark ---

def _do_embark(ctx: cmd.Ctx, mind: MindPaths, state: dict | None) -> None:
    state = _require_state(state)
    _require_status(state, ("planned", "research_logged"), "embark")

    destination = ctx.args.get_one("embark")
    journey_dir = _journey_dir(ctx, state["journey"])
    next_entry = state["entry"] + 1
    entry_label = f"{next_entry:03d}"
    entry_file = journey_dir / f"{entry_label}.md"

    # Create entry from template
    ctx.templates.write(
        "chart/explore-entry.md.j2", entry_file,
        entry=entry_label, destination=destination,
    )

    # Update state
    state["entry"] = next_entry
    state["destination"] = destination
    state["status"] = "embarked"
    state["history"].append({"entry": next_entry, "file": destination})
    _save_state(mind, state)

    ctx.print(ctx.templates.render(
        "chart/explore-embark.md.j2",
        entry=entry_label, entry_file=entry_file, destination=destination,
    ))


# --- Reflect ---

def _do_reflect(ctx: cmd.Ctx, mind: MindPaths, state: dict | None) -> None:
    state = _require_state(state)
    _require_status(state, ("embarked",), "reflect")

    state["status"] = "reflected"
    _save_state(mind, state)

    ctx.print(ctx.templates.render("chart/explore-reflect.md.j2"))


# --- Return ---

def _do_return(ctx: cmd.Ctx, mind: MindPaths, state: dict | None) -> None:
    state = _require_state(state)
    _require_status(state, ("reflected", "research_logged"), "return")

    journey_dir = _journey_dir(ctx, state["journey"])
    entries = sorted(journey_dir.glob("*.md"))

    ctx.print(ctx.templates.render(
        "chart/explore-return.md.j2",
        journey_name=state["journey"],
        entry_count=len(entries),
        journey_dir=journey_dir,
    ))

    mind.work.exploration_file.unlink(missing_ok=True)


# --- Helpers ---

def _find_example_journey(ctx: cmd.Ctx) -> Path | None:
    """Find the bundled example journey asset.

    Returns the path to the example journey in __assets__/chart/.
    Projects can override this via hook (TODO).
    """
    example = ctx.paths.pkgs.current.assets_dir / "chart" / "example-journey.md"
    if example.exists():
        return example
    return None
