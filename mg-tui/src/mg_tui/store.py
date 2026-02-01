"""Section-level change dispatcher for TUI state.

TuiStore holds the last frozen TuiModel snapshot and, on each update,
diffs sections against the previous snapshot. Changed sections fire a
blinker signal so widgets can subscribe to exactly the sections they
care about.

Signals are auto-discovered from dataclasses.fields(TuiModel), so
adding a new section to TuiModel automatically creates a signal here
with zero maintenance.
"""

from __future__ import annotations

import dataclasses

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
        store.update(frozen_model)  # fires hud_changed if hud differs
    """

    def __init__(self) -> None:
        self._snapshot: TuiModel | None = None
        self._signals = _section_signals()
        # Expose signals as attributes (e.g. store.hud_changed)
        for name, signal in self._signals.items():
            setattr(self, name, signal)

    def update(self, model: TuiModel) -> None:
        """Compare model against last snapshot, fire signals for changed sections."""
        old = self._snapshot
        self._snapshot = model

        for f in dataclasses.fields(TuiModel):
            new_section = getattr(model, f.name)
            if old is None:
                # First update — always fire
                self._signals[f"{f.name}_changed"].send(new_section)
                continue

            old_section = getattr(old, f.name)
            if new_section != old_section:
                self._signals[f"{f.name}_changed"].send(new_section)

    @property
    def snapshot(self) -> TuiModel | None:
        """The last frozen snapshot, or None if no update has occurred."""
        return self._snapshot
