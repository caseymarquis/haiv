"""Claude Code hooks dispatch.

Receives hook events from Claude Code and forwards them
to the TUI over IPC.
"""

from __future__ import annotations

import json
import os
import sys
import time


def dispatch(args: list[str]) -> None:
    ts = time.time()
    hook_name = args[0] if args else "unknown"

    session_id = os.environ.get("HV_SESSION", "")
    ipc_address = os.environ.get("HV_CLAUDE_HOOK_DISPATCH", "")

    if not ipc_address:
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

    from haiv.helpers.tui.commands import ClaudeHookEventRequest, tui_claude_hook_event
    from haiv.helpers.tui.TuiClient import TuiClient

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
        finally:
            conn.close()
    except Exception:
        pass
