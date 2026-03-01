"""Tests for FileWatcher — OS file events with debounced batch delivery."""

from __future__ import annotations

import threading
from pathlib import Path

from mg.helpers.utils.file_watcher import FileWatcher

# Fast timing for tests.
_DEBOUNCE = 0.05
_TICK = 0.02


def _watcher(handler, **kwargs):
    return FileWatcher(handler, debounce_seconds=_DEBOUNCE, tick_seconds=_TICK, **kwargs)


class TestWatchFile:
    """Watch a single file for changes."""

    def test_detects_file_modification(self, tmp_path: Path):
        """Modifying a watched file delivers its path."""
        target = tmp_path / "sessions.toml"
        target.write_text("original")

        received: list[list[Path]] = []
        event = threading.Event()

        def handler(batch: list[Path]) -> None:
            received.append(batch)
            event.set()

        w = _watcher(handler)
        w.watch_file(target)
        w.start()
        try:
            target.write_text("modified")
            event.wait(timeout=3.0)
            assert len(received) == 1
            assert target in received[0]
        finally:
            w.stop()

    def test_ignores_other_files_in_same_directory(self, tmp_path: Path):
        """Only the watched file triggers events, not siblings."""
        target = tmp_path / "watched.toml"
        other = tmp_path / "other.toml"
        target.write_text("original")
        other.write_text("original")

        received: list[list[Path]] = []
        event = threading.Event()

        def handler(batch: list[Path]) -> None:
            received.append(batch)
            event.set()

        w = _watcher(handler)
        w.watch_file(target)
        w.start()
        try:
            other.write_text("changed")
            assert not event.wait(timeout=0.2)
            assert received == []
        finally:
            w.stop()


class TestWatchDirectory:
    """Watch a directory recursively for changes."""

    def test_detects_file_creation(self, tmp_path: Path):
        """Creating a file in a watched directory delivers its path."""
        watched_dir = tmp_path / "minds"
        watched_dir.mkdir()

        received: list[list[Path]] = []
        event = threading.Event()

        def handler(batch: list[Path]) -> None:
            received.append(batch)
            event.set()

        w = _watcher(handler)
        w.watch_directory(watched_dir)
        w.start()
        try:
            new_file = watched_dir / "plan.md"
            new_file.write_text("hello")
            event.wait(timeout=3.0)
            all_paths = [p for batch in received for p in batch]
            assert any(p == new_file for p in all_paths)
        finally:
            w.stop()

    def test_detects_nested_changes(self, tmp_path: Path):
        """Changes in subdirectories are detected."""
        watched_dir = tmp_path / "minds"
        sub = watched_dir / "wren" / "work"
        sub.mkdir(parents=True)

        received: list[list[Path]] = []
        event = threading.Event()

        def handler(batch: list[Path]) -> None:
            received.append(batch)
            event.set()

        w = _watcher(handler)
        w.watch_directory(watched_dir)
        w.start()
        try:
            nested_file = sub / "scratchpad.md"
            nested_file.write_text("thinking")
            event.wait(timeout=3.0)
            all_paths = [p for batch in received for p in batch]
            assert any(p == nested_file for p in all_paths)
        finally:
            w.stop()


class TestLifecycle:
    """Start/stop behavior."""

    def test_stop_is_idempotent(self, tmp_path: Path):
        """Calling stop() twice does not raise."""
        w = _watcher(lambda b: None)
        w.watch_file(tmp_path / "f.txt")
        w.start()
        w.stop()
        w.stop()

    def test_multiple_watches(self, tmp_path: Path):
        """Can watch a file and a directory on the same watcher."""
        file_target = tmp_path / "sessions.toml"
        file_target.write_text("original")
        dir_target = tmp_path / "minds"
        dir_target.mkdir()

        received: list[list[Path]] = []
        both_done = threading.Event()

        def handler(batch: list[Path]) -> None:
            received.append(batch)
            all_paths = [p for b in received for p in b]
            has_file = any(p == file_target for p in all_paths)
            has_dir_file = any("new.md" in str(p) for p in all_paths)
            if has_file and has_dir_file:
                both_done.set()

        w = _watcher(handler)
        w.watch_file(file_target)
        w.watch_directory(dir_target)
        w.start()
        try:
            file_target.write_text("changed")
            (dir_target / "new.md").write_text("hello")
            both_done.wait(timeout=3.0)
            all_paths = [p for b in received for p in b]
            assert any(p == file_target for p in all_paths)
            assert any("new.md" in str(p) for p in all_paths)
        finally:
            w.stop()
