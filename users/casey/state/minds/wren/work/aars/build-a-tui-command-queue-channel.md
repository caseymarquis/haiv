# AAR: Build a TUI command queue channel

## Summary

Added a typed command queue alongside the existing `write_raw` data channel. Commands flow through the same server message queue but drain independently — no interaction with the dirty/signal system. Two concrete commands (restart, bounce) are implemented end-to-end.

### Deliverables

- **Command transport** (`_infrastructure/TuiServer/`): `TuiCommandType` enum, `TuiCommand` envelope, `CommandRequest`, server buffering via `Atom[list]`, `drain_commands()`.
- **Typed command helpers** (`helpers/tui/commands.py`): `RestartRequest`, `BounceRequest` dataclasses with `tui_restart()` and `tui_bounce()` helper functions. Wired to `ctx.tui.restart()` / `ctx.tui.bounce()` facade.
- **CommandDispatcher** (`haiv-tui/command_dispatcher.py`): Owns type translation (Any → typed request) and routes to handler callables injected via constructor.
- **Poll loop integration** (`app.py`): Drains commands independently of model updates, passes to dispatcher.
- **Both IPC paths**: `send_command()` on `TuiLocalClient` (in-process) and `TuiClient` (remote IPC).
- **Atlas**: Charting journey (`the-tui-transport/`, 6 entries) and infrastructure maps (`maps/haiv-lib/infrastructure/`).

## Key Decisions

### Commands on the protocol, not TuiModel

Commands are UI control requests, not data sections. They don't belong in `TuiModel` (which represents state). Instead, `send_command()` is a new method on the `ModelClient` protocol, parallel to `write_raw()`.

### Typed envelope with Any payload in transit

`TuiCommand(type: TuiCommandType, payload: Any)` — the enum is typed on both ends, the payload is `Any` only in the transport layer. Helpers construct typed payloads, the dispatcher deserializes them back. Neither caller nor handler ever sees `Any`.

### Infrastructure owns the envelope, helpers own the payloads

`TuiCommand`, `TuiCommandType`, `CommandRequest` live in `_infrastructure/`. Typed command dataclasses and helper functions live in `helpers/tui/commands.py`. Infrastructure doesn't import any typed command — it's blind to payload contents.

### CommandDispatcher takes handler callables

Dispatcher is decoupled from widgets/app via constructor-injected handlers. The app wires handlers at construction time. This follows the existing widget DI pattern.

### Bounce uses mind_launch

`_handle_bounce()` cycles to the next session sorted by mind name, then calls `helpers.mind_launch()` which handles all three cases (already active, parked, or new). A TODO marks where filtering by a future `session.bounce` attribute will go.

## Open Items

- **Bounce filtering**: Currently cycles all sessions. Needs a `bounce` attribute on `Session` to filter the bounce list (TODO in `haiv-tui/src/haiv_tui/app.py:_handle_bounce`).
- **mind_launch chattiness**: `mind_launch` prints user-facing messages ("Mind X is already active..."). For command-driven invocations this is noise — may want a `quiet` parameter later.
- **Atlas infrastructure maps**: Created `maps/haiv-lib/infrastructure/` with routing, resolvers, and tui-server maps. The overview was refactored to keep infrastructure detail separate from command-author-facing content.

## Commits and Files Changed

- e55b8cc add TUI command queue: typed channel for UI control requests
  Key files: `_TuiIpc.py`, `_TuiServer.py`, `_TuiLocalClient.py`, `protocol.py`, `TuiClient.py`, `commands.py`, `tui.py`, `command_dispatcher.py`, `app.py`
  Tests: `test_tui_server.py`, `test_tui_client.py`, `test_tui_commands.py`, `test_command_dispatcher.py`
