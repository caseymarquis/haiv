"""Tests for sessions widget assembly — raw data to DTOs."""

from haiv.helpers.tui.TuiModel import (
    ActiveMindRaw,
    GitRaw,
    SessionEntry,
    SessionsRaw,
)
from haiv.wrappers.git import BranchStats
from haiv_tui.widgets.sessions import SessionNodeView, build_session_tree


def _entry(mind: str, *, id: str = "", task: str = "", branch: str = "",
           short_id: int = 0, parent_id: str = "", status: str = "started",
           description: str = "") -> SessionEntry:
    return SessionEntry(
        id=id, mind=mind, task=task, branch=branch,
        short_id=short_id, parent_id=parent_id,
        status=status, description=description,
    )


class TestBuildSessionTree:
    """build_session_tree assembles raw data into SessionNodeViews."""

    def test_empty_when_no_sessions(self):
        result = build_session_tree(None, None, None)
        assert result == []

    def test_empty_when_sessions_empty(self):
        result = build_session_tree(SessionsRaw(entries=[]), None, None)
        assert result == []

    def test_single_session(self):
        sessions = SessionsRaw(entries=[_entry("wren", id="1", task="test task", short_id=1)])
        result = build_session_tree(sessions, None, None)
        assert len(result) == 1
        assert result[0].mind == "wren"
        assert result[0].task == "test task"
        assert result[0].short_id == 1
        assert result[0].is_active is False
        assert result[0].children == []

    def test_active_mind_highlighted(self):
        sessions = SessionsRaw(entries=[
            _entry("wren", id="1"),
            _entry("sage", id="2"),
        ])
        active = ActiveMindRaw(mind="wren")
        result = build_session_tree(sessions, None, active)
        by_mind = {v.mind: v for v in result}
        assert by_mind["wren"].is_active is True
        assert by_mind["sage"].is_active is False

    def test_git_stats_merged_by_branch(self):
        sessions = SessionsRaw(entries=[
            _entry("wren", id="1", branch="feature-x"),
        ])
        git = GitRaw(branches={
            "feature-x": BranchStats(ahead=2, behind=1, changed_files=3),
        })
        result = build_session_tree(sessions, git, None)
        assert result[0].git_stats == "↑2 ↓1 ~3"

    def test_git_stats_default_when_branch_missing(self):
        sessions = SessionsRaw(entries=[
            _entry("wren", id="1", branch="unknown"),
        ])
        git = GitRaw(branches={})
        result = build_session_tree(sessions, git, None)
        assert result[0].git_stats == "(no branch)"

    def test_git_stats_default_when_no_git(self):
        sessions = SessionsRaw(entries=[
            _entry("wren", id="1", branch="feature"),
        ])
        result = build_session_tree(sessions, None, None)
        assert result[0].git_stats == "(no branch)"

    def test_parent_child_hierarchy(self):
        sessions = SessionsRaw(entries=[
            _entry("wren", id="parent-1", short_id=1),
            _entry("sage", id="child-1", short_id=2, parent_id="parent-1"),
        ])
        result = build_session_tree(sessions, None, None)
        assert len(result) == 1
        assert result[0].mind == "wren"
        assert len(result[0].children) == 1
        assert result[0].children[0].mind == "sage"

    def test_description_passed_through(self):
        sessions = SessionsRaw(entries=[
            _entry("wren", id="1", description="detailed work"),
        ])
        result = build_session_tree(sessions, None, None)
        assert result[0].description == "detailed work"

    def test_status_passed_through(self):
        sessions = SessionsRaw(entries=[
            _entry("wren", id="1", status="staged"),
        ])
        result = build_session_tree(sessions, None, None)
        assert result[0].status == "staged"
