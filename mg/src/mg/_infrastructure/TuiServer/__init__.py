"""TUI IPC server package.

Contains the server, IPC listener, local client, and shared IPC contract.
External callers import from this package — internal modules are prefixed
with underscore.
"""

from haiv._infrastructure.TuiServer._freeze import freeze_model
from haiv.helpers.tui._base import TuiModelSection
from haiv._infrastructure.TuiServer._TuiIpc import (
    RESTART_EXIT_CODE,
    ConcurrencyError,
    ErrorResponse,
    OkResponse,
    ReadRequest,
    Request,
    Response,
    WriteRequest,
    pipe_address,
)
from haiv._infrastructure.TuiServer._TuiLocalClient import TuiLocalClient
from haiv._infrastructure.TuiServer._TuiServer import TuiServer

__all__ = [
    "RESTART_EXIT_CODE",
    "TuiModelSection",
    "freeze_model",
    "ConcurrencyError",
    "ErrorResponse",
    "OkResponse",
    "ReadRequest",
    "Request",
    "Response",
    "TuiLocalClient",
    "TuiServer",
    "WriteRequest",
    "pipe_address",
]
