# TUI Server — Data Transport

**Location:** `haiv-lib/src/haiv/_infrastructure/TuiServer/`

The TUI's data transport. Runs inside the TUI process. All external access — both IPC (remote `hv` commands) and local (Textual widgets) — goes through a single message queue processed by a dedicated model thread. No locks needed on the model because only the model thread touches it.

```
_infrastructure/TuiServer/
├── _TuiServer.py       # Server: model thread, dirty tracking, submit()
├── _TuiLocalClient.py  # In-process client: wraps submit() as ModelClient
├── _TuiIpc.py          # Request/response types, pipe address resolution
├── _TuiIpcListener.py  # IPC listener thread: accept(), deserialize, submit()
├── _freeze.py          # Deep-freeze model snapshots for safe read access
└── __init__.py          # Re-exports
```

## Threading Model

Two threads, neither managed by Textual:

- **Model thread** — owns the authoritative `TuiModel`. Drains the message queue, processes reads (deepcopy) and writes (overwrite + mark dirty), resolves callers' futures.
- **IPC listener thread** — blocks on `Listener.accept()`, deserializes incoming messages, submits them via `submit()`. Has no access to the model.
- **Textual's main thread** — uses `TuiLocalClient`, which also only holds a reference to `submit()`. Same boundary as the IPC listener.

## Key Mechanisms

**`submit(request) -> Future`** is the single entry point. Both clients construct typed request objects (`ReadRequest`, `WriteRequest`) and submit them. The model thread dispatches on type and resolves the future. Operations are pure in-memory (microseconds), so callers safely block on `future.result()`.

**Dirty tracking:** `_dirty` is an `Atom[set[str]]` holding section names changed since last drain. `drain_dirty()` atomically swaps the set with an empty one. The TUI poll loop calls this every 0.1s, reads a frozen snapshot, and pushes dirty sections through `TuiStore` for signal dispatch.

**Stale socket recovery:** On startup, if the socket is already bound: try to connect. If connection succeeds, another instance is live — refuse to start. If connection refused — stale socket from a crash, unlink and rebind.

## Data Flow

```
Producer (hv command / background worker)
    → TuiLocalClient.write_raw() or TuiClient (IPC)
    → submit(WriteRequest) → queue
    → model thread: _apply_write() + mark dirty
    → poll loop: drain_dirty() → read snapshot → store.update() → signals → widgets
```

See `journeys/the-tui-transport/` for the full story.
