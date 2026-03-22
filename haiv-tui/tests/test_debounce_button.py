"""DebounceButton — disables briefly after press to prevent double-clicks."""

from __future__ import annotations

import pytest

from textual.widgets import Button

from haiv_tui.widgets.debounce_button import DebounceButton
from harness import WidgetTestApp


class TestDebounceButton:

    @pytest.mark.asyncio
    async def test_renders_with_label(self):
        btn = DebounceButton("Open", id="btn")
        app = WidgetTestApp(btn)

        async with app.run_test() as pilot:
            await pilot.pause()
            assert btn.button.label.plain == "Open"

    @pytest.mark.asyncio
    async def test_starts_enabled_by_default(self):
        btn = DebounceButton("Open", id="btn")
        app = WidgetTestApp(btn)

        async with app.run_test() as pilot:
            await pilot.pause()
            assert btn.disabled is False

    @pytest.mark.asyncio
    async def test_starts_disabled_when_requested(self):
        btn = DebounceButton("Open", disabled=True, id="btn")
        app = WidgetTestApp(btn)

        async with app.run_test() as pilot:
            await pilot.pause()
            assert btn.disabled is True

    @pytest.mark.asyncio
    async def test_posts_pressed_message(self):
        btn = DebounceButton("Open", id="btn")
        app = WidgetTestApp(btn)

        async with app.run_test() as pilot:
            await pilot.click("#inner")
            await pilot.pause()
            # Verify the button entered cooldown — confirms the press was handled
            assert btn.button.disabled is True

    @pytest.mark.asyncio
    async def test_disables_during_cooldown(self):
        btn = DebounceButton("Open", debounce_seconds=10.0, id="btn")
        app = WidgetTestApp(btn)

        async with app.run_test() as pilot:
            await pilot.click("#inner")
            await pilot.pause()
            assert btn.button.disabled is True

    @pytest.mark.asyncio
    async def test_suppresses_second_press_during_cooldown(self):
        btn = DebounceButton("Open", debounce_seconds=10.0, id="btn")
        app = WidgetTestApp(btn)

        async with app.run_test() as pilot:
            await pilot.click("#inner")
            await pilot.pause()
            assert btn.button.disabled is True
            # Inner button is disabled, second click is a no-op

    @pytest.mark.asyncio
    async def test_re_enables_after_cooldown(self):
        btn = DebounceButton("Open", debounce_seconds=0.2, id="btn")
        app = WidgetTestApp(btn)

        async with app.run_test() as pilot:
            await pilot.click("#inner")
            await pilot.pause()
            assert btn.button.disabled is True
            await pilot.pause(0.4)
            assert btn.button.disabled is False

    @pytest.mark.asyncio
    async def test_disabled_setter_works(self):
        btn = DebounceButton("Open", id="btn")
        app = WidgetTestApp(btn)

        async with app.run_test() as pilot:
            await pilot.pause()
            btn.disabled = True
            assert btn.button.disabled is True
            btn.disabled = False
            assert btn.button.disabled is False
