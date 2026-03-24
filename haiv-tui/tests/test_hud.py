"""HUD widget — assembly and widget-level tests."""

from __future__ import annotations

from collections import deque
from pathlib import Path

import pytest

from haiv.helpers.tui.TuiModel import (
    ActiveMindRaw,
    SessionsRaw,
    TuiModel,
)
from haiv.settings import HaivSettings
from haiv_tui.store import TuiStore
from haiv_tui.widgets.hud import HudWidget, build_hud_view

from harness import WidgetTestApp, make_entry


# ---------------------------------------------------------------------------
# Assembly
# ---------------------------------------------------------------------------


class TestBuildHudView:
    """build_hud_view assembles raw data into a HudView."""

    def test_no_active_mind(self):
        result = build_hud_view(None, None)
        assert result.worktree == "—"
        assert result.summary == "—"
        assert result.session_display == "—"
        assert result.worktree_path is None

    def test_empty_active_mind(self):
        result = build_hud_view(ActiveMindRaw(mind=""), None)
        assert result.session_display == "—"

    def test_active_mind_with_session(self):
        active = ActiveMindRaw(mind="wren")
        sessions = SessionsRaw(entries=[
            make_entry("wren", task="build the thing", branch="feature-x", short_id=3),
        ])
        result = build_hud_view(active, sessions)
        assert result.worktree == "feature-x"
        assert result.summary == "build the thing"
        assert result.session_display == "wren [3]"

    def test_worktree_path_assembled(self, tmp_path):
        active = ActiveMindRaw(mind="wren")
        sessions = SessionsRaw(entries=[
            make_entry("wren", branch="feature-x"),
        ])
        result = build_hud_view(active, sessions, tmp_path / "worktrees")
        assert result.worktree_path == tmp_path / "worktrees" / "feature-x"

    def test_worktree_path_none_without_branch(self):
        active = ActiveMindRaw(mind="wren")
        sessions = SessionsRaw(entries=[
            make_entry("wren", branch=""),
        ])
        result = build_hud_view(active, sessions, Path("/tmp/wt"))
        assert result.worktree_path is None

    def test_active_mind_without_matching_session(self):
        active = ActiveMindRaw(mind="wren")
        sessions = SessionsRaw(entries=[
            make_entry("sage", task="other work"),
        ])
        result = build_hud_view(active, sessions)
        assert result.worktree == "—"
        assert result.summary == "—"
        assert result.session_display == "wren"

    def test_active_mind_with_no_sessions(self):
        active = ActiveMindRaw(mind="wren")
        result = build_hud_view(active, None)
        assert result.session_display == "wren"

    def test_empty_branch_shows_dash(self):
        active = ActiveMindRaw(mind="wren")
        sessions = SessionsRaw(entries=[
            make_entry("wren", task="no branch task", branch="", short_id=1),
        ])
        result = build_hud_view(active, sessions)
        assert result.worktree == "—"

    def test_empty_task_shows_dash(self):
        active = ActiveMindRaw(mind="wren")
        sessions = SessionsRaw(entries=[
            make_entry("wren", task="", branch="main", short_id=1),
        ])
        result = build_hud_view(active, sessions)
        assert result.summary == "—"


# ---------------------------------------------------------------------------
# Widget
# ---------------------------------------------------------------------------


def _make_hud(store: TuiStore, **kwargs) -> HudWidget:
    return HudWidget(
        store=store,
        worktrees_dir=kwargs.get("worktrees_dir"),
        settings=kwargs.get("settings", HaivSettings()),
        errors=kwargs.get("errors", deque(maxlen=5)),
        id="hud",
    )


class TestHudWidget:
    """HudWidget mounted with injected store."""

    @pytest.mark.asyncio
    async def test_mounts_empty(self, store):
        app = WidgetTestApp(_make_hud(store))
        async with app.run_test():
            pass

    @pytest.mark.asyncio
    async def test_sets_app_title_on_active_mind(self, store):
        widget = _make_hud(store)
        app = WidgetTestApp(widget)

        async with app.run_test() as pilot:
            active = ActiveMindRaw(mind="wren")
            sessions = SessionsRaw(entries=[
                make_entry("wren", task="build thing", branch="feature-x", short_id=3),
            ])
            store.update(
                TuiModel(sessions=sessions, active_mind=active),
                frozenset({"active_mind", "sessions"}),
            )
            await pilot.pause()

            assert "wren" in app.title

    @pytest.mark.asyncio
    async def test_app_title_dashes_when_no_active_mind(self, store):
        widget = _make_hud(store)
        app = WidgetTestApp(widget)

        async with app.run_test() as pilot:
            store.update(TuiModel(), frozenset({"active_mind"}))
            await pilot.pause()

            assert "—" in app.title
