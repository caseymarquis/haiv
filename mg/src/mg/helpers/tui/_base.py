"""Shared base types for the TUI layer.

Lives here to avoid circular imports between TuiModel and TuiServer.
Both sides import from this module.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable, Protocol, runtime_checkable

if TYPE_CHECKING:
    from haiv.helpers.tui.TuiModel import TuiModel


@dataclass
class TuiModelSection:
    """Base class for all TUI model sections.

    Carries a version integer used for optimistic concurrency control.
    Version is managed exclusively by the server — clients should never
    set it directly.
    """

    _version: int = field(default=0, repr=False)


@runtime_checkable
class ModelClient(Protocol):
    """Protocol for TUI model access (TuiClient or TuiLocalClient)."""

    def read(self) -> TuiModel: ...
    def write(self, mutator: Callable[[TuiModel], None]) -> None: ...
