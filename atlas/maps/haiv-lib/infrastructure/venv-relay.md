# Venv Relay

## Problem

Commands live in packages with their own venvs — haiv_project, haiv_user, and eventually external packages. The `hv` CLI runs in the workspace venv (haiv-cli), which doesn't have those packages' dependencies. A project command that imports `pandas` will crash if loaded in the workspace venv.

## Design

The CLI is a pure router. It finds the command file, detects the venv, and relays execution — either in-process or via subprocess.

```
CLI (haiv-cli)
├── route (filesystem walk across all command sources)
├── resolve venv (VenvResolver)
├── same venv? → relay.run_route() directly
└── different venv? → relay.subprocess_relay() via uv run --project
```

The relay module (`haiv-lib/src/haiv/relay.py`) is the single execution path for all commands. It loads the command, builds context with resolvers and hooks from the command's own venv, and runs it. The CLI never loads or executes commands itself.

For subprocess relay, the route data is serialized to JSON and passed as an argument to `python -m haiv.relay`. The relay deserializes, reconstructs the route, and runs — zero state crosses the boundary beyond what's in the JSON.

**Resolver isolation:** Each command gets resolvers from its own package only. If a project command needs the mind resolver from haiv-core, it calls the helper directly — no cross-venv resolver inheritance.

**Error handling:** `haiv.errors.handle_error()` is used by both the CLI and relay. CommandError gets a clean message; unexpected errors get logged to `~/.local/state/haiv/logs/` with a details path printed.

**Help / enumeration:** The relay supports a `define_all` mode — given a list of command files, it loads each, calls `define()`, and returns the definitions as pickled data. The help command uses this to batch-load definitions from external venvs in a single subprocess call.

## Key Files

| File | Role |
|------|------|
| `haiv-lib/src/haiv/relay.py` | Relay: run_route, subprocess_relay, define_all |
| `haiv-lib/src/haiv/_infrastructure/venv_resolver.py` | VenvResolver protocol + PyprojectVenvResolver |
| `haiv-lib/src/haiv/errors.py` | Shared error handling (handle_error) |
| `haiv-cli/src/haiv_cli/__init__.py` | Router: find command, resolve venv, delegate to relay |
| `haiv-core/src/haiv_core/commands/help.py` | Uses relay define_all for external package enumeration |
| `haiv-lib/tests/integration/test_venv_relay.py` | Integration tests (run explicitly with `-m integration`) |
