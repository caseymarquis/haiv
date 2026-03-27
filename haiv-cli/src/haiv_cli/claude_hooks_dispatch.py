"""Claude Code hooks dispatch.

Receives hook events from Claude Code and forwards them
to the TUI over IPC.

Set HV_CLAUDE_HOOK_TRACE=1 to log dispatch activity to
~/.cache/haiv/claude-hooks-trace.log
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

_TRACE = os.environ.get("HV_CLAUDE_HOOK_TRACE", "") == "1"
_TRACE_FILE = Path.home() / ".cache" / "haiv" / "claude-hooks-trace.log"


def _trace(msg: str) -> None:
    if not _TRACE:
        return
    try:
        _TRACE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(_TRACE_FILE, "a") as f:
            ts = time.strftime("%H:%M:%S")
            f.write(f"{ts}  {msg}\n")
    except Exception:
        pass


def dispatch(args: list[str]) -> None:
    ts = time.time()
    hook_name = args[0] if args else "unknown"

    session_id = os.environ.get("HV_SESSION", "")
    ipc_address = os.environ.get("HV_CLAUDE_HOOK_DISPATCH", "")

    _trace(f"hook={hook_name} session={session_id[:8]} ipc={ipc_address or '(none)'}")

    if not ipc_address:
        _trace("no IPC address, skipping")
        return

    stdin_data = None
    if not sys.stdin.isatty():
        try:
            stdin_data = sys.stdin.read().strip() or None
        except Exception:
            pass

    payload = {}
    if stdin_data:
        try:
            payload = json.loads(stdin_data)
        except json.JSONDecodeError:
            payload = {"raw": stdin_data}

    from haiv.helpers.tui.commands import ClaudeHookEventRequest

    event = ClaudeHookEventRequest(
        ts=ts,
        hook=hook_name,
        session_id=session_id,
        payload=payload,
    )

    try:
        from multiprocessing.connection import Client
        conn = Client(ipc_address)
        try:
            from haiv._infrastructure.TuiServer._TuiIpc import (
                CommandRequest,
                TuiCommand,
                TuiCommandType,
            )
            conn.send(CommandRequest(command=TuiCommand(
                type=TuiCommandType.CLAUDE_HOOK_EVENT,
                payload=event,
            )))
            conn.recv()
            _trace(f"sent ok")
        finally:
            conn.close()
    except Exception as e:
        _trace(f"error: {e}")
