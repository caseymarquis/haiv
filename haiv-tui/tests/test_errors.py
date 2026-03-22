"""Errors widget tests."""

from __future__ import annotations

import pytest

from haiv_tui.widgets.errors import ErrorsWidget

from harness import WidgetTestApp


class TestErrorsWidget:

    @pytest.mark.asyncio
    async def test_mounts_empty(self):
        app = WidgetTestApp(ErrorsWidget(id="errors"))
        async with app.run_test():
            pass

    @pytest.mark.asyncio
    async def test_renders_errors(self):
        widget = ErrorsWidget(id="errors")
        app = WidgetTestApp(widget)

        async with app.run_test() as pilot:
            widget.render_errors(["oops", "bang"])
            await pilot.pause()

            content = str(widget.content)
            assert "oops" in content
            assert "bang" in content

    @pytest.mark.asyncio
    async def test_clears_on_empty_list(self):
        widget = ErrorsWidget(id="errors")
        app = WidgetTestApp(widget)

        async with app.run_test() as pilot:
            widget.render_errors(["oops"])
            await pilot.pause()
            widget.render_errors([])
            await pilot.pause()

            content = str(widget.content)
            assert "oops" not in content
