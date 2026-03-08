"""hv chart - Navigate and extend the atlas.

Helps a mind find what they need in the codebase, and when they
venture beyond what's known, gives them the rules for charting
new territory.
"""

from haiv import cmd


def define() -> cmd.Def:
    return cmd.Def(
        description="Navigate the atlas or explore uncharted territory",
        flags=[
            cmd.Flag("goal", description="What you're trying to find or accomplish"),
        ],
    )


def execute(ctx: cmd.Ctx) -> None:
    atlas_dir = ctx.paths.root / "atlas"
    journeys_dir = atlas_dir / "journeys"
    maps_dir = atlas_dir / "maps"

    # Ensure atlas structure exists
    journeys_dir.mkdir(parents=True, exist_ok=True)
    maps_dir.mkdir(exist_ok=True)

    has_welcome = (atlas_dir / "welcome.md").exists()
    goal = ctx.args.get_one("goal", default_value=None)

    # Build the briefing
    lines = []

    lines.append(f"The atlas lives at: {atlas_dir}")
    if has_welcome:
        lines.append(f"Read {atlas_dir / 'welcome.md'} for how the atlas works.")
    lines.append("")

    if goal:
        lines.append(f'Your goal: "{goal}"')
        lines.append("")

    # --- Finding what you need (advice, not rules) ---

    lines.append("FINDING WHAT YOU NEED")
    lines.append("")
    lines.append("You might try this path:")
    lines.append("")
    lines.append("  1. Check the maps — they distill what's known.")
    lines.append("  2. Check the quest board — someone may have seen signs of what you need.")
    lines.append("  3. Search the journals — someone may have passed through relevant territory.")
    lines.append("  4. If none of that has what you need — explore.")
    lines.append("")

    # --- Charting rules (explicit, these matter) ---

    lines.append("RULES FOR CHARTING NEW TERRITORY")
    lines.append("")
    lines.append("When you go beyond what the atlas covers, you're an explorer.")
    lines.append("These rules exist because other minds depend on what you leave behind.")
    lines.append("")
    lines.append("  - Create a journey: atlas/journeys/your-journey-name/")
    lines.append("    Name it after where you're headed, not who you are.")
    lines.append("  - Your first entry (001) is your research log. Before you explore, write down:")
    lines.append("      - What you searched for in the atlas and what you found")
    lines.append("      - What's missing — what you needed but the atlas didn't have")
    lines.append("      - Where you plan to go and why")
    lines.append("    This helps future minds improve the atlas itself.")
    lines.append("  - Number the rest of your entries from there: 002, 003, ...")
    lines.append("  - Every file you read gets an entry. No silent reads.")
    lines.append("    What did you learn? Why did you go there?")
    lines.append("    What would help the next explorer? Where are you going next?")
    lines.append("  - Tangents go on the quest board, not into your journal.")
    lines.append("  - If something in the atlas doesn't match what you see in the code,")
    lines.append("    post a mystery to the quest board. Note what confused you, when the")
    lines.append("    entry was written, when the file was last modified. Leave the clues.")
    lines.append("  - When you're done, update the quest board with anything you completed or discovered.")
    lines.append("")

    # --- Rewards ---

    lines.append("REWARDS")
    lines.append("")
    lines.append("Completing a quest earns a reward. Each reward lets you nickname")
    lines.append("something on a map — a lasting mark on the atlas.")
    lines.append("")
    lines.append("  Landmark       — You mapped something foundational.")
    lines.append("  Trade Route    — You documented how two things connect.")
    lines.append("  Compass        — You captured *why* something was built this way.")
    lines.append("  Inbeeyana Combs — You solved a mystery. Followed the clues, found the truth.")
    lines.append("")
    lines.append("Track your rewards in your home folder.")

    ctx.print("\n".join(lines))
