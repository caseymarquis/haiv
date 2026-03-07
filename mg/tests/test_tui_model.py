"""Tests for TuiModel, TuiModelSection, and related utilities."""

import dataclasses
import typing

import pytest

from haiv._infrastructure.TuiServer import TuiModelSection, freeze_model, pipe_address
from haiv.helpers.tui.TuiModel import HudSection, TuiModel


class TestTuiModelStructure:
    """Every field on TuiModel must be a TuiModelSection subclass."""

    def test_all_fields_are_sections(self):
        """Reflective check: prevents accidentally adding a raw field."""
        hints = typing.get_type_hints(TuiModel)
        for f in dataclasses.fields(TuiModel):
            assert issubclass(hints[f.name], TuiModelSection), (
                f"TuiModel.{f.name} has type {hints[f.name]}, "
                f"expected TuiModelSection subclass"
            )

    def test_model_is_frozen(self):
        """TuiModel is frozen — section slots can't be reassigned."""
        model = TuiModel()
        with pytest.raises(dataclasses.FrozenInstanceError):
            setattr(model, "hud", HudSection())


class TestTuiModelFreeze:
    """freeze_model() produces a deep-frozen snapshot."""

    def test_frozen_sections_reject_assignment(self):
        """Fields on frozen sections can't be modified."""
        model = TuiModel()
        frozen = freeze_model(model)
        with pytest.raises(AttributeError):
            frozen.hud.role = "COO"

    def test_frozen_preserves_values(self):
        """Frozen copy has the same field values as the original."""
        model = TuiModel(hud=HudSection(role="COO", worktree="main"))
        frozen = freeze_model(model)
        assert frozen.hud.role == "COO"
        assert frozen.hud.worktree == "main"

    def test_frozen_is_independent_copy(self):
        """Mutating the original after freeze doesn't affect the snapshot."""
        hud = HudSection(role="COO")
        model = TuiModel(hud=hud)
        frozen = freeze_model(model)
        hud.role = "CTO"
        assert frozen.hud.role == "COO"


class TestTuiModelSection:
    """Base section behavior."""

    def test_default_version_is_zero(self):
        """New sections start at version 0."""
        section = HudSection()
        assert section._version == 0

    def test_section_fields_default_to_none(self):
        """Concrete section fields default to None."""
        section = HudSection()
        assert section.role is None
        assert section.worktree is None
        assert section.summary is None
        assert section.session is None


class TestPipeAddress:
    """pipe_address() returns the correct IPC path per platform."""

    def test_unix_address(self, monkeypatch):
        """Unix returns a socket path in /tmp."""
        monkeypatch.setattr("haiv._infrastructure.TuiServer._TuiIpc.platform.system", lambda: "Linux")
        assert pipe_address("myproject") == "/tmp/haiv-myproject.sock"

    def test_windows_address(self, monkeypatch):
        """Windows returns a named pipe path."""
        monkeypatch.setattr("haiv._infrastructure.TuiServer._TuiIpc.platform.system", lambda: "Windows")
        assert pipe_address("myproject") == r"\\.\pipe\haiv-myproject"
