# Plan: CLI Error Handling

**Status:** Planned

---

## Problem

Currently, unhandled exceptions print full tracebacks to the user. For `CommandError` and similar expected errors, users should see just the message.

## Solution

1. **Catch errors in CLI entry point** (`mg-cli/src/mg_cli/__init__.py`)
   - `CommandError`: Print just the message, exit 1
   - Other exceptions: Print brief message, log full traceback

2. **Log location** (stable, always works)
   - `~/.local/share/mind-games/logs/` (XDG_DATA_HOME)
   - Fallback: `~/.mind-games/logs/`
   - Log file: `error-{date}.log` or similar

3. **Fallback behavior**
   - If logging fails, print full traceback to stderr

4. **User guidance**
   - Print "See ~/.local/share/mind-games/logs/... for details" on unexpected errors

## Implementation

```python
# In mg-cli main()
try:
    run_command(command, ctx)
except CommandError as e:
    print(str(e), file=sys.stderr)
    sys.exit(1)
except Exception as e:
    log_path = log_exception(e)  # Returns path or None
    print(f"Error: {e}", file=sys.stderr)
    if log_path:
        print(f"Details: {log_path}", file=sys.stderr)
    else:
        traceback.print_exc()
    sys.exit(1)
```
