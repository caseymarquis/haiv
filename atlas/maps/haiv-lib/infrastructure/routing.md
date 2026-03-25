# The Silk Road — Command Routing

**Location:** `haiv-lib/src/haiv/_infrastructure/`

The full path a command travels from `hv <something>` to running code. Starts at `haiv-cli/__init__.py:main()`, searches user → project → core for a match, loads the file, builds context, runs the lifecycle.

Key files: `routing.py`, `loader.py`, `runner.py`, `args.py`.

See `journeys/the-routing-table/` for the full story.
