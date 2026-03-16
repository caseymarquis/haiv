# chart

Atlas navigation and guided codebase exploration. Two subcommands that help minds find what they need and leave trails for those who follow.

**Location:** `worktrees/main/haiv-core/src/haiv_core/commands/chart/`

---

## `hv chart` (`_index_.py`)

Prints a briefing: where the atlas lives, how to find things (maps → quest board → journeys), charting rules for exploration, and the reward system. Bootstraps `atlas/journeys/` and `atlas/maps/` if missing. Pure text output built with `lines.append()` — no templates. Takes an optional `--goal` flag.

## `hv chart explore` (`explore.py`)

A state machine for one-file-at-a-time codebase exploration. The cycle:

```
new → research_logged → planned → embarked → reflected → planned → ... → return
```

Each step is a `--flag` (`--log`, `--plan`, `--embark <file>`, `--reflect`, `--return`). Running bare shows status or starts a new journey. State is stored per-mind in `work/exploration.json`, so multiple minds can explore simultaneously.

Creates journey directories and entry files from Jinja2 templates in `__assets__/chart/`. The bundled example journey (`__assets__/chart/example-journey/`) is shown to minds when they start their first exploration.

**Templates:** `explore-start.md.j2`, `explore-start-needs-name.md.j2`, `explore-plan.md.j2`, `explore-embark.md.j2`, `explore-entry.md.j2`, `explore-reflect.md.j2`, `explore-return.md.j2`, `research-log.md.j2`.

## Known issues

- `_find_example_journey()` points to the bundled asset in `__assets__/chart/example-journey/` rather than a project-local folder. The start template hardcodes specific filenames from that example. Being reworked — see `journeys/charting-tools-local-examples/`.
- The briefing text in `_index_.py` duplicates content from `atlas/welcome.md`.
