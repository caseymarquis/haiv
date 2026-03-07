"""Deep-freeze helpers for TUI model snapshots.

freeze_model() is used by TuiClient and TuiLocalClient to produce
immutable read() responses.
"""

from __future__ import annotations

import copy
import dataclasses
from typing import TYPE_CHECKING, TypeVar

from haiv.helpers.tui._base import TuiModelSection

if TYPE_CHECKING:
    from haiv.helpers.tui.TuiModel import TuiModel


# ---------------------------------------------------------------------------
# Freezing
# ---------------------------------------------------------------------------

# Cache of dynamically-generated frozen dataclass variants, keyed by the
# original mutable class. Built once per section type, reused thereafter.
_frozen_variants: dict[type, type] = {}

_TSection = TypeVar("_TSection", bound=TuiModelSection)


def _freeze_section(section: _TSection) -> _TSection:
    """Create a frozen (immutable) copy of a section instance.

    Dynamically generates a frozen dataclass with the same fields as
    the original, deep-copies all values, and returns a frozen instance.
    """
    cls = type(section)
    values = {
        f.name: copy.deepcopy(getattr(section, f.name))
        for f in dataclasses.fields(cls)
    }

    frozen_cls = _frozen_variants.get(cls)
    if frozen_cls is None:
        fields_spec = [
            (f.name, f.type) for f in dataclasses.fields(cls)
        ]
        frozen_cls = dataclasses.make_dataclass(
            f"Frozen{cls.__name__}",
            fields_spec,
            frozen=True,
        )
        _frozen_variants[cls] = frozen_cls

    return frozen_cls(**values)


def freeze_model(model: TuiModel) -> TuiModel:
    """Return a deep-frozen copy suitable for read() responses.

    Each section is deep-copied and re-created as a frozen dataclass
    so that field assignment raises AttributeError.
    """
    frozen_sections = {}
    for f in dataclasses.fields(model):
        section = getattr(model, f.name)
        frozen_sections[f.name] = _freeze_section(section)
    return type(model)(**frozen_sections)
