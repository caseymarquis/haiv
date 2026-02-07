"""Markdown file viewer — renders a file and auto-refreshes on changes.

Uses MarkdownViewer which extends VerticalScroll for built-in scrolling.
The watcher thread reads the file on change and posts a Textual message
with the content. The widget receives the message on the UI thread and
updates via the inner Markdown document.
"""

from __future__ import annotations

from pathlib import Path

from textual.message import Message
from textual.widgets import MarkdownViewer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent
from watchdog.observers import Observer


class MarkdownFileWidget(MarkdownViewer):
    """Renders a markdown file and refreshes when it changes on disk.

    Extends MarkdownViewer for built-in scrolling (arrow keys, page up/down,
    home/end). Table of contents is hidden by default.
    """

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
    """Watchdog handler — reads file on watcher thread, posts message."""

    def __init__(self, widget: MarkdownFileWidget) -> None:
        self._widget = widget

    def on_modified(self, event: FileModifiedEvent) -> None:
        if Path(event.src_path).resolve() == self._widget.file_path:
            try:
                content = self._widget.file_path.read_text()
            except Exception as e:
                content = f"*{e}*"
            self._widget.post_message(MarkdownFileWidget.FileChanged(content))
