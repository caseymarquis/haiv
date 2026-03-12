"""Chart command helpers.

Domain logic for atlas navigation and guided codebase exploration.
Commands in the chart family delegate here for anything beyond
user interaction.
"""

from __future__ import annotations

import json
import shutil
from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING

from haiv.errors import CommandError
from haiv.paths import AtlasPaths, MindPaths

if TYPE_CHECKING:
    from haiv.templates import TemplateRenderer


# --- Status guidance ---

NEXT_STEP = {
    "new": "Write your research log (001), then run: hv chart explore --log",
    "research_logged": "Run: hv chart explore --plan",
    "planned": "Run: hv chart explore --embark <file-path>",
    "embarked": "Read the file, write your entry, then run: hv chart explore --reflect",
    "reflected": "Run: hv chart explore --plan  (or --return to finish)",
}


# --- Atlas structure ---

def ensure_atlas_structure(atlas: AtlasPaths) -> None:
    """Ensure the atlas directory structure exists.

    Creates journeys/, maps/, and examples/ if missing.
    """
    atlas.journeys_dir.mkdir(parents=True, exist_ok=True)
    atlas.maps_dir.mkdir(exist_ok=True)
    atlas.examples_dir.mkdir(exist_ok=True)


def get_briefing(
    atlas: AtlasPaths,
    goal: str | None,
    templates: TemplateRenderer,
) -> str:
    """Return the atlas briefing text.

    Ensures atlas structure exists, then renders the briefing template.
    """
    ensure_atlas_structure(atlas)

    return templates.render(
        "chart/briefing.md.j2",
        atlas_root=atlas.root,
        has_welcome=atlas.welcome_file.exists(),
        welcome_file=atlas.welcome_file,
        goal=goal,
    )


def ensure_example_journey(
    atlas: AtlasPaths,
    bundled_dir: Path,
) -> list[Path]:
    """Ensure the project-local example journey folder has content.

    If the examples folder is empty or missing, copies from bundled_dir.
    Returns sorted list of example files found.
    """
    examples_dir = atlas.examples_dir

    if not _has_content(examples_dir) and bundled_dir.is_dir():
        examples_dir.mkdir(parents=True, exist_ok=True)
        for src in sorted(bundled_dir.iterdir()):
            if src.is_file():
                shutil.copy2(src, examples_dir / src.name)

    if not examples_dir.is_dir():
        return []

    return sorted(f for f in examples_dir.iterdir() if f.is_file() and f.suffix == ".md")


# --- Exploration state ---

def load_exploration(mind: MindPaths) -> dict | None:
    """Load the current exploration state for a mind."""
    path = mind.work.exploration_file
    if not path.exists():
        return None
    return json.loads(path.read_text())


def save_exploration(mind: MindPaths, state: dict) -> None:
    """Save exploration state for a mind."""
    mind.work.exploration_file.write_text(json.dumps(state, indent=2) + "\n")


def clear_exploration(mind: MindPaths) -> None:
    """Remove exploration state for a mind."""
    mind.work.exploration_file.unlink(missing_ok=True)


def _require_active(state: dict | None) -> dict:
    """Require an active exploration, raising if none exists."""
    if state is None:
        raise CommandError("No active journey. Run `hv chart explore` to start one.")
    return state


def _require_status(state: dict, allowed: tuple[str, ...], action: str) -> None:
    """Require the exploration to be in one of the allowed statuses."""
    if state["status"] not in allowed:
        raise CommandError(
            f"Can't {action} right now. Status: {state['status']}\n"
            f"  {NEXT_STEP.get(state['status'], '')}"
        )


# --- Journey lifecycle ---

def prompt_for_name(
    goal: str | None,
    templates: TemplateRenderer,
) -> str:
    """Return prompt text asking the user to provide a journey name."""
    return templates.render("chart/explore-start-needs-name.md.j2", goal=goal)


def start_journey(
    atlas: AtlasPaths,
    mind: MindPaths,
    name: str,
    goal: str | None,
    mind_name: str,
    bundled_examples_dir: Path,
    templates: TemplateRenderer,
) -> str:
    """Start a new exploration journey.

    Creates the journey directory, writes a research log template,
    saves initial state, and returns the start message.
    """
    journey_dir = atlas.journeys_dir / name
    if journey_dir.exists():
        raise CommandError(f"Journey '{name}' already exists at {journey_dir}")

    journey_dir.mkdir(parents=True, exist_ok=True)

    templates.write(
        "chart/research-log.md.j2",
        journey_dir / "001-research-log.md",
        mind=mind_name,
        date=date.today().isoformat(),
        goal=goal,
    )

    save_exploration(mind, {
        "journey": name,
        "goal": goal,
        "status": "new",
        "entry": 1,
        "history": [],
    })

    example_files = ensure_example_journey(atlas, bundled_examples_dir)

    return templates.render(
        "chart/explore-start.md.j2",
        name=name,
        goal=goal,
        example_files=example_files,
        journey_dir=journey_dir,
    )


def show_status(state: dict) -> str:
    """Return status text for an active exploration."""
    lines = [
        f"Journey: {state['journey']}",
        f"Entry: {state.get('entry', 1):03d}",
        f"Status: {state['status']}",
        "",
        NEXT_STEP.get(state["status"], "Unknown state."),
    ]

    if state["status"] == "embarked":
        lines.append(f"\nDestination: {state.get('destination', '?')}")

    return "\n".join(lines)


def log_research(
    mind: MindPaths,
    state: dict | None,
    atlas: AtlasPaths,
) -> str:
    """Record that the research log has been written.

    Returns guidance text for the next step.
    """
    state = _require_active(state)
    _require_status(state, ("new",), "log")

    journey_dir = atlas.journeys_dir / state["journey"]
    log_files = list(journey_dir.glob("001*"))

    if not log_files:
        return (
            "Your research log (001) doesn't exist yet.\n"
            f"Create it at: {journey_dir / '001-research-log.md'}"
        )

    state["status"] = "research_logged"
    save_exploration(mind, state)

    return (
        "Research log recorded.\n"
        "\n"
        "Now it's time to plan your first destination. Run:\n"
        "  hv chart explore --plan"
    )


def plan_next(
    mind: MindPaths,
    state: dict | None,
    atlas: AtlasPaths,
    templates: TemplateRenderer,
) -> str:
    """Advance to planning state and return guidance text."""
    state = _require_active(state)
    _require_status(state, ("research_logged", "reflected"), "plan")

    journey_dir = atlas.journeys_dir / state["journey"]
    entry = state["entry"]
    current_entries = sorted(journey_dir.glob(f"{entry:03d}*"))

    state["status"] = "planned"
    save_exploration(mind, state)

    return templates.render(
        "chart/explore-plan.md.j2",
        current_file=current_entries[0] if current_entries else None,
    )


def embark(
    mind: MindPaths,
    state: dict | None,
    atlas: AtlasPaths,
    destination: str,
    templates: TemplateRenderer,
) -> str:
    """Commit to a destination, create an entry file, and return guidance text."""
    state = _require_active(state)
    _require_status(state, ("planned", "research_logged"), "embark")

    journey_dir = atlas.journeys_dir / state["journey"]
    next_entry = state["entry"] + 1
    entry_label = f"{next_entry:03d}"
    entry_file = journey_dir / f"{entry_label}.md"

    templates.write(
        "chart/explore-entry.md.j2", entry_file,
        entry=entry_label, destination=destination,
    )

    state["entry"] = next_entry
    state["destination"] = destination
    state["status"] = "embarked"
    state["history"].append({"entry": next_entry, "file": destination})
    save_exploration(mind, state)

    return templates.render(
        "chart/explore-embark.md.j2",
        entry=entry_label, entry_file=entry_file, destination=destination,
    )


def reflect(
    mind: MindPaths,
    state: dict | None,
    templates: TemplateRenderer,
) -> str:
    """Record reflection and return guidance text."""
    state = _require_active(state)
    _require_status(state, ("embarked",), "reflect")

    state["status"] = "reflected"
    save_exploration(mind, state)

    return templates.render("chart/explore-reflect.md.j2")


def finish_journey(
    mind: MindPaths,
    state: dict | None,
    atlas: AtlasPaths,
    templates: TemplateRenderer,
) -> str:
    """End the journey and return the closing message."""
    state = _require_active(state)
    _require_status(state, ("reflected", "research_logged"), "return")

    journey_dir = atlas.journeys_dir / state["journey"]
    entries = sorted(journey_dir.glob("*.md"))

    message = templates.render(
        "chart/explore-return.md.j2",
        journey_name=state["journey"],
        entry_count=len(entries),
        journey_dir=journey_dir,
    )

    clear_exploration(mind)

    return message


# --- Internal ---

def _has_content(directory: Path) -> bool:
    """Check if a directory exists and contains any files."""
    if not directory.is_dir():
        return False
    return any(directory.iterdir())
