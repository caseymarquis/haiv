# Task: Relay Infrastructure for Cross-Venv Command Execution

## Context

haiv is a CLI tool that manages communities of AI minds across different projects. It's built as a uv workspace with packages: `haiv` (core lib), `haiv-core` (core commands), `haiv-cli` (entrypoint), `haiv-tui`.

Currently, `hv` always runs in the haiv-cli venv (hardcoded in `~/.local/bin/hv`). This works when the project IS haiv, but breaks when haiv manages a different project (e.g., "dnd") — that project's `haiv_project` and `haiv_user` packages have their own dependencies that aren't in the haiv-cli venv.

## The Design

**Rule:** Core commands run in-process. Project and user commands always relaunch in the correct venv via `uv run`.

**Flow:**
```
hv <command>
  └─ haiv-cli (haiv-cli venv): route command
       ├─ core command → execute in-process (current behavior)
       └─ project/user command → relay:
            uv run --project {path} python -m haiv.relay exec \
              --file /abs/path/to/command.py \
              --args '...' \
              --ipc {tmpfile}    # only if parent needs data back
            └─ child inherits stdio, builds ctx, executes command
               writes structured response to ipc file if needed
```

**Key decisions already made:**
- IPC via tempfile (cross-platform, simple, swappable later behind abstraction)
- Parent passes the already-routed command file path to child (no re-routing)
- Child inherits stdio for interactive commands
- The IPC file is only created/read when data needs to come back (e.g., `hv help` collecting command lists from multiple venvs)
- `haiv.relay` lives in the `haiv` package so it's available in every project venv (they all depend on `haiv`)
- Always relay non-core commands (no venv comparison optimization)

## What to Build

1. **IPC abstraction** — A simple module for parent/child communication. Tempfile-backed. Parent creates channel, passes path via env var or arg. Child writes response. Parent reads after child exits. Abstract enough to swap backends later.

2. **`haiv.relay` module** — Entry point for relayed commands. Receives: command file path, serialized args. Does: load command, build ctx, execute, optionally write response to IPC channel. Needs to handle the same setup the current `main()` does after routing (resolvers, hooks, etc.).

3. **haiv-cli changes** — After routing, if the command came from project or user source, relay instead of executing in-process. Pass the resolved file path. For `help`, collect structured data from relay calls to each venv.

## Key Files

| File | Role |
|------|------|
| `haiv-cli/src/haiv_cli/__init__.py` | CLI entrypoint — needs relay dispatch |
| `haiv/src/haiv/_infrastructure/loader.py` | Command loading |
| `haiv/src/haiv/_infrastructure/runner.py` | Command lifecycle (setup/execute/teardown) |
| `haiv/src/haiv/_infrastructure/args.py` | Context building (`build_ctx`) |
| `haiv/src/haiv/paths.py` | Path resolution, `get_haiv_root()` |
| `haiv/src/haiv/_infrastructure/resolvers.py` | Resolver discovery |

## Testing

Use TDD. The relay module should be testable in isolation — you can verify it loads a command file and executes it without needing a full cross-venv setup. Integration testing with actual `uv run` is valuable too.

The dnd project at `/home/casey/code/dnd/` is the test case. It has haiv-hq set up with `haiv_project` but no `.venv` yet (also still needs rename from mg_ to haiv_).

## Design Notes from Discussion

- The common case is just "re-exec this command in the right venv" — stdio passthrough, no data back. `help` is the outlier where you need to collect structured data from multiple venvs.
- A tempfile in `/tmp` is already in-memory on Linux (tmpfs). The "in-memory file" concern doesn't exist in practice.
- The IPC file is only created when the child has data to return. The common case never touches it.
- Full re-routing in the child was considered but rejected as wasteful — the parent already did the routing work.
