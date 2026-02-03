# Scratchpad

Rough thinking, debugging notes, half-formed ideas.

---

## Current Session Notes

- TUI is running live in WezTerm — can capture HUD state via `wezterm cli get-text`
- Reload hotkey works for testing code changes on the fly
- Entry point partially wired — needs `get_mg_root` + `detect_user` → `Paths` to finish
- Sessions file has one entry: wren, short_id=2, task="Figure out how to start delegating again"

## Architecture Decisions Made

- **helpers.py pattern**: Standalone functions with all deps as params. Tui class is thin wrapper only. Keeps TUI app decoupled from dependency bag.
- **Naming convention**: `noun_verb` in helpers (sessions_refresh, errors_append) for sorting
- **Poll model**: Textual polls model at 100ms via set_interval. No cross-thread callbacks. Avoids deadlock where model thread calls back into Textual.
- **Version-based diffing**: TuiStore compares `_version` ints per section. Cheaper than value equality, race-free.
- **Internal errors**: deque(maxlen=5) on app, separate from model errors. Store subscriber errors routed via error_sink callback.
- **Session index**: Task-first display in sidebar ("task (mind)"), not mind-first. Humans remember what was happening, not who was doing it.
- **Parent/tree**: Deferred — sessions are flat for now, delegation tree comes later.

## Things to Remember

- Use `claude "prompt"` syntax, not separate Enter key
- AARs go in `temp-aar/`
- Can skip formal process for simple/urgent tasks, write welcome docs directly
- `flatpak run org.wezfurlong.wezterm` is the wezterm command on this system
