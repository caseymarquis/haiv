"""TUI IPC server package.

Contains the server, IPC listener, local client, and shared IPC contract.
External callers import from this package — internal modules are prefixed
with underscore.
"""

from mg._infrastructure.TuiServer._freeze import TuiModelSection, freeze_model
from mg._infrastructure.TuiServer._TuiIpc import (
    ConcurrencyError,
    ErrorResponse,
    OkResponse,
    ReadRequest,
    Request,
    Response,
    WriteRequest,
    pipe_address,
)
from mg._infrastructure.TuiServer._TuiLocalClient import TuiLocalClient
from mg._infrastructure.TuiServer._TuiServer import TuiServer

__all__ = [
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
