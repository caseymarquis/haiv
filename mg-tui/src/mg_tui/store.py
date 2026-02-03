"""Section-level change dispatcher for TUI state.

TuiStore holds the last frozen TuiModel snapshot and, on each update,
compares per-section versions against the last seen values. Changed
sections fire a blinker signal so widgets can subscribe to exactly the
sections they care about.

Version-based diffing (comparing a single int per section) is both
cheaper and race-free compared to value equality — versions are
authoritative from the model thread.

Signals are auto-discovered from dataclasses.fields(TuiModel), so
adding a new section to TuiModel automatically creates a signal here
with zero maintenance.
"""

from __future__ import annotations

import dataclasses
from typing import Callable

import blinker

from mg.helpers.tui.TuiModel import TuiModel


def _section_signals() -> dict[str, blinker.Signal]:
    """Create one signal per TuiModel section field."""
    return {
        f"{f.name}_changed": blinker.Signal(f"{f.name}_changed")
        for f in dataclasses.fields(TuiModel)
    }


class TuiStore:
    """Diffing store that fires per-section blinker signals on change.

    Usage:
        store = TuiStore()
        store.hud_changed.connect(my_widget.on_hud_changed)
        store.update(frozen_model)  # fires hud_changed if version differs

    Subscriber errors are caught and routed to the error_sink callback
    (typically app.internal_errors.append) to avoid crashing the poll loop.
    """

    def __init__(self, error_sink: Callable[[str], None] | None = None) -> None:
        self._snapshot: TuiModel | None = None
        self._versions: dict[str, int] = {}
        self._signals = _section_signals()
        self._error_sink = error_sink
        # Expose signals as attributes (e.g. store.hud_changed)
        for name, signal in self._signals.items():
            setattr(self, name, signal)

    def update(self, model: TuiModel) -> None:
        """Compare section versions against last seen, fire signals for changes."""
        self._snapshot = model

        for f in dataclasses.fields(TuiModel):
            section = getattr(model, f.name)
            version = section._version
            last_version = self._versions.get(f.name)

            if last_version is None or last_version != version:
                self._versions[f.name] = version
                try:
                    self._signals[f"{f.name}_changed"].send(section)
                except Exception as e:
                    if self._error_sink is not None:
                        self._error_sink(f"{f.name}_changed: {e}")

    @property
    def snapshot(self) -> TuiModel | None:
        """The last frozen snapshot, or None if no update has occurred."""
        return self._snapshot
