# haiv-lib Infrastructure

Internals of haiv-lib. You don't need this for building commands — these are the gears underneath. Come here when you're working on the CLI pipeline, the TUI transport, or the resolver system itself.

- [routing.md](routing.md) — The Silk Road: how `hv <something>` becomes running code
- [resolvers.md](resolvers.md) — The Translators: how raw strings become domain objects
- [tui-server.md](tui-server.md) — The TUI transport: message queue, model thread, dirty tracking
