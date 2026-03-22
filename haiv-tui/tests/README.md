# haiv-tui Tests

## Textual Widget Testing

Textual provides `app.run_test()` — an async context manager that runs the app headless and returns a `Pilot` for driving it.

```python
async with app.run_test() as pilot:
    await pilot.press("r")
    assert app.screen.styles.background == Color.parse("red")
```

### Accessing Static widget content

`Static` exposes a `.content` property (read/write) that returns the original content set via `update()` or the constructor:

```python
widget = pilot.app.query_one(MyStaticWidget)
assert "expected text" in str(widget.content)
```

There's also `.visual` (read-only) which returns the rendered visual — may differ from what was passed to `update()`.

### Timing

If you send a signal or post a message and immediately assert, it may fail because the message hasn't been processed yet. Call `await pilot.pause()` to flush pending messages first.

### Clicking by selector

```python
await pilot.click("#red")
await pilot.click(".my-class")
```

### Snapshot testing

For visual regression, Textual provides `pytest-textual-snapshot` as a separate package. We don't use it currently — our tests assert on data, not pixels.

## Our conventions

- **One file per widget** — `test_sessions.py`, `test_hud.py`, etc.
- **Assembly + widget tests together** — pure DTO assembly tests and mounted widget tests live in the same file.
- **`harness.py`** — shared `WidgetTestApp` and helpers. Imported via `conftest.py` fixtures.
- **Constructor injection** — widgets receive deps as keyword args. Tests provide fakes/mocks directly. No `self.app` fishing.

## Sources

- [Textual Testing Guide](https://textual.textualize.io/guide/testing/)
- [Static Widget API](https://textual.textualize.io/widgets/static/)
- [pytest-textual-snapshot](https://github.com/Textualize/pytest-textual-snapshot)
