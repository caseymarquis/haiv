"""Section-level change dispatcher for TUI state.

TuiStore holds the last frozen TuiModel snapshot and fires per-section
blinker signals when the server reports a section as dirty. Widgets
subscribe to the sections they care about.

Signals are auto-discovered from dataclasses.fields(TuiModel), so
adding a new section to TuiModel automatically creates a signal here
with zero maintenance.
"""

from __future__ import annotations

import dataclasses
from typing import Callable

import blinker

from haiv.helpers.tui.TuiModel import TuiModel


def _section_signals() -> dict[str, blinker.Signal]:
    """Create one signal per TuiModel section field."""
    return {
        f"{f.name}_changed": blinker.Signal(f"{f.name}_changed")
        for f in dataclasses.fields(TuiModel)
    }


class TuiStore:
    """Dirty-driven store that fires per-section blinker signals.

    Usage:
        store = TuiStore()
        store.sessions_changed.connect(my_widget.on_sessions_changed)
        store.update(frozen_model, dirty={"sessions"})

    Subscriber errors are caught and routed to the error_sink callback
    (typically app.internal_errors.append) to avoid crashing the poll loop.
    """

    def __init__(self, error_sink: Callable[[str], None] | None = None) -> None:
        self._snapshot: TuiModel | None = None
        self._signals = _section_signals()
        self._error_sink = error_sink
        # Expose signals as attributes (e.g. store.sessions_changed)
        for name, signal in self._signals.items():
            setattr(self, name, signal)

    def update(self, model: TuiModel, dirty: frozenset[str]) -> None:
        """Store the snapshot and fire signals for dirty sections."""
        self._snapshot = model

        for name in dirty:
            signal_name = f"{name}_changed"
            signal = self._signals.get(signal_name)
            if signal is None:
                continue
            section = getattr(model, name, None)
            try:
                signal.send(section)
            except Exception as e:
                if self._error_sink is not None:
                    self._error_sink(f"{signal_name}: {e}")

    @property
    def snapshot(self) -> TuiModel | None:
        """The last frozen snapshot, or None if no update has occurred."""
        return self._snapshot
