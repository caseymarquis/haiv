"""RecentFilesWidget — widget-level tests."""

from __future__ import annotations

from collections import deque
from pathlib import Path

import pytest

from textual.widgets import OptionList

from haiv.helpers.tui.TuiModel import RecentFilesRaw, RecentFileEntry, TuiModel
from haiv.settings import HaivSettings
from haiv_tui.store import TuiStore
from haiv_tui.widgets.recent_files import RecentFilesWidget

from harness import WidgetTestApp


def _make_widget(store=None, tmp_path=None):
    return RecentFilesWidget(
        store=store or TuiStore(),
        worktrees_dir=tmp_path or Path("/tmp/fake"),
        settings=HaivSettings(_editor_command=["echo"]),
        errors=deque(maxlen=5),
        id="recent-files",
    )


class TestRecentFilesWidget:

    @pytest.mark.asyncio
    async def test_mounts_empty(self):
        app = WidgetTestApp(_make_widget())
        async with app.run_test():
            pass

    @pytest.mark.asyncio
    async def test_populates_on_signal(self):
        store = TuiStore()
        widget = _make_widget(store=store)
        app = WidgetTestApp(widget)

        async with app.run_test() as pilot:
            files = RecentFilesRaw(files=[
                RecentFileEntry(path="src/app.py", worktree="main", mtime=1000.0),
                RecentFileEntry(path="src/store.py", worktree="main", mtime=999.0),
            ])
            store.update(TuiModel(recent_files=files), frozenset({"recent_files"}))
            await pilot.pause()

            option_list = widget.query_one(OptionList)
            assert option_list.option_count == 2

    @pytest.mark.asyncio
    async def test_enter_opens_file(self, tmp_path):
        """Enter on a highlighted file calls open_in_editor."""
        store = TuiStore()
        # Create a real file so is_file() passes
        wt = tmp_path / "worktrees" / "main" / "src"
        wt.mkdir(parents=True)
        (wt / "app.py").write_text("pass")

        widget = RecentFilesWidget(
            store=store,
            worktrees_dir=tmp_path / "worktrees",
            settings=HaivSettings(_editor_command=["echo"]),
            errors=deque(maxlen=5),
            id="recent-files",
        )
        app = WidgetTestApp(widget)

        async with app.run_test() as pilot:
            files = RecentFilesRaw(files=[
                RecentFileEntry(path="src/app.py", worktree="main", mtime=1000.0),
            ])
            store.update(TuiModel(recent_files=files), frozenset({"recent_files"}))
            await pilot.pause()

            option_list = widget.query_one(OptionList)
            option_list.focus()
            await pilot.pause()
            await pilot.press("enter")
            await pilot.pause()

            # No errors means open_in_editor succeeded
            errors = widget._errors
            assert len(errors) == 0
