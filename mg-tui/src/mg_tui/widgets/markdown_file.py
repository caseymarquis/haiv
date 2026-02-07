"""Markdown file viewer — renders a file and auto-refreshes on changes.

Uses MarkdownViewer which extends VerticalScroll for built-in scrolling.
The watcher thread reads the file on change and posts a Textual message
with the content. The widget receives the message on the UI thread and
updates via the inner Markdown document.
"""

from __future__ import annotations

from pathlib import Path

from textual.binding import Binding
from textual.message import Message
from textual.widgets import MarkdownViewer
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


class MarkdownFileWidget(MarkdownViewer):
    """Renders a markdown file and refreshes when it changes on disk.

    Extends MarkdownViewer for built-in scrolling (arrow keys, page up/down,
    home/end). Table of contents is hidden by default.
    """

    SCROLL_LINES = 3

    BINDINGS = [
        Binding("j,down", "scroll_down_lines", "Scroll Down", show=False, id="scroll.down"),
        Binding("k,up", "scroll_up_lines", "Scroll Up", show=False, id="scroll.up"),
        Binding("ctrl+d", "scroll_half_page_down", "Half Page Down", show=False, id="scroll.half_page_down"),
        Binding("ctrl+u", "scroll_half_page_up", "Half Page Up", show=False, id="scroll.half_page_up"),
    ]

    def action_scroll_down_lines(self) -> None:
        self.scroll_to(y=self.scroll_target_y + self.SCROLL_LINES, animate=False)

    def action_scroll_up_lines(self) -> None:
        self.scroll_to(y=self.scroll_target_y - self.SCROLL_LINES, animate=False)

    def action_scroll_half_page_down(self) -> None:
        self.scroll_to(y=self.scroll_target_y + self.scrollable_content_region.height // 2, animate=False)

    def action_scroll_half_page_up(self) -> None:
        self.scroll_to(y=self.scroll_target_y - self.scrollable_content_region.height // 2, animate=False)

    class FileChanged(Message):
        """Posted from the watcher thread with new file contents."""

        def __init__(self, content: str) -> None:
            super().__init__()
            self.content = content

    def __init__(self, file_path: Path, **kwargs) -> None:
        self.file_path = file_path.resolve()
        content = self._read_file()
        super().__init__(content, show_table_of_contents=False, **kwargs)
        self._observer: Observer | None = None

    def on_mount(self) -> None:
        handler = _FileChangeHandler(self)
        self._observer = Observer()
        self._observer.schedule(handler, str(self.file_path.parent), recursive=False)
        self._observer.start()

    def on_unmount(self) -> None:
        if self._observer is not None:
            self._observer.stop()
            self._observer.join(timeout=1)

    def _on_markdown_file_widget_file_changed(self, event: FileChanged) -> None:
        """Handle file change message on the UI thread."""
        self.document.update(event.content)

    def _read_file(self) -> str:
        """Read the file, returning error message on failure."""
        try:
            return self.file_path.read_text()
        except Exception as e:
            return f"*Error reading file: {e}*"


class _FileChangeHandler(FileSystemEventHandler):
    """Watchdog handler — reads file on watcher thread, posts message.

    Handles modified, created, and moved events to catch both direct
    writes and atomic writes (write-to-temp then rename).
    """

    def __init__(self, widget: MarkdownFileWidget) -> None:
        self._widget = widget

    def _handle_change(self, path: str) -> None:
        if Path(path).resolve() == self._widget.file_path:
            try:
                content = self._widget.file_path.read_text()
            except Exception as e:
                content = f"*{e}*"
            self._widget.post_message(MarkdownFileWidget.FileChanged(content))

    def on_modified(self, event) -> None:
        self._handle_change(event.src_path)

    def on_created(self, event) -> None:
        self._handle_change(event.src_path)

    def on_moved(self, event) -> None:
        self._handle_change(event.dest_path)
