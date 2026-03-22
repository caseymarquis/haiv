"""Tests for HUD widget assembly — raw data to DTOs."""

from haiv.helpers.tui.TuiModel import (
    ActiveMindRaw,
    SessionEntry,
    SessionsRaw,
)
from haiv_tui.widgets.hud import HudView, build_hud_view


def _entry(mind: str, *, task: str = "", branch: str = "",
           short_id: int = 0) -> SessionEntry:
    return SessionEntry(id="", mind=mind, task=task, branch=branch, short_id=short_id)


class TestBuildHudView:
    """build_hud_view assembles raw data into a HudView."""

    def test_no_active_mind(self):
        result = build_hud_view(None, None)
        assert result.worktree == "—"
        assert result.summary == "—"
        assert result.session_display == "—"

    def test_empty_active_mind(self):
        result = build_hud_view(ActiveMindRaw(mind=""), None)
        assert result.session_display == "—"

    def test_active_mind_with_session(self):
        active = ActiveMindRaw(mind="wren")
        sessions = SessionsRaw(entries=[
            _entry("wren", task="build the thing", branch="feature-x", short_id=3),
        ])
        result = build_hud_view(active, sessions)
        assert result.worktree == "feature-x"
        assert result.summary == "build the thing"
        assert result.session_display == "wren [3]"

    def test_active_mind_without_matching_session(self):
        active = ActiveMindRaw(mind="wren")
        sessions = SessionsRaw(entries=[
            _entry("sage", task="other work"),
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
            _entry("wren", task="no branch task", branch="", short_id=1),
        ])
        result = build_hud_view(active, sessions)
        assert result.worktree == "—"

    def test_empty_task_shows_dash(self):
        active = ActiveMindRaw(mind="wren")
        sessions = SessionsRaw(entries=[
            _entry("wren", task="", branch="main", short_id=1),
        ])
        result = build_hud_view(active, sessions)
        assert result.summary == "—"
