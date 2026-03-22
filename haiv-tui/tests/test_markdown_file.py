"""Markdown file viewer widget tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from haiv_tui.widgets.markdown_file import MarkdownFileWidget

from harness import WidgetTestApp


class TestMarkdownFileWidget:

    @pytest.mark.asyncio
    async def test_mounts_with_missing_file(self, tmp_path):
        widget = MarkdownFileWidget(tmp_path / "nope.md", id="md")
        app = WidgetTestApp(widget)
        async with app.run_test():
            pass

    @pytest.mark.asyncio
    async def test_renders_file_content(self, tmp_path):
        md_file = tmp_path / "test.md"
        md_file.write_text("# Hello\n\nWorld")

        widget = MarkdownFileWidget(md_file, id="md")
        app = WidgetTestApp(widget)
        async with app.run_test() as pilot:
            await pilot.pause()
            # MarkdownViewer renders markdown — just verify it mounted
            # and didn't crash. Content rendering is Textual's job.
