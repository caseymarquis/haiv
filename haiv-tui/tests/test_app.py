"""HaivApp tests — app mounted with injected deps, no real server."""

from __future__ import annotations

import pytest

from haiv_tui.app import HaivApp
from haiv_tui.widgets.errors import ErrorsWidget
from haiv_tui.widgets.hud import HudWidget
from haiv_tui.widgets.sessions import SessionsWidget

from harness import make_haiv_deps, make_mock_client, make_mock_server


def _make_app() -> HaivApp:
    return HaivApp(
        deps=make_haiv_deps(),
        server=make_mock_server(),
        client=make_mock_client(),
    )


class TestHaivApp:

    @pytest.mark.asyncio
    async def test_mounts(self):
        app = _make_app()
        async with app.run_test():
            pass

    @pytest.mark.asyncio
    async def test_has_sessions_widget(self):
        app = _make_app()
        async with app.run_test():
            app.query_one(SessionsWidget)

    @pytest.mark.asyncio
    async def test_has_hud_widget(self):
        app = _make_app()
        async with app.run_test():
            app.query_one(HudWidget)

    @pytest.mark.asyncio
    async def test_has_errors_widget(self):
        app = _make_app()
        async with app.run_test():
            app.query_one(ErrorsWidget)

    @pytest.mark.asyncio
    async def test_server_started_on_mount(self):
        server = make_mock_server()
        app = HaivApp(
            deps=make_haiv_deps(),
            server=server,
            client=make_mock_client(),
        )
        async with app.run_test():
            server.start.assert_called_once()

    @pytest.mark.asyncio
    async def test_poll_drains_dirty(self):
        server = make_mock_server()
        app = HaivApp(
            deps=make_haiv_deps(),
            server=server,
            client=make_mock_client(),
        )
        async with app.run_test() as pilot:
            await pilot.pause()
            assert server.drain_dirty.called
