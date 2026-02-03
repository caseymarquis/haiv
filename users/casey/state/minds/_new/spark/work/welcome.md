# Task Assignment

**Build WezTerm CLI Wrapper**

Create a Python wrapper for WezTerm's CLI in mg-core, similar to existing wrappers for git and tmux.

---

## Context

We're building a TUI for mind-games that will run inside WezTerm. We need programmatic control over WezTerm panes, tabs, and windows. WezTerm has a CLI (`wezterm cli ...`) that provides this.

On this system, WezTerm is installed via Flatpak: `flatpak run org.wezfurlong.wezterm cli ...`

The WezTerm command should be read from `mg.toml` configuration, not hardcoded. This allows different systems (Flatpak, native, custom path) to configure their own command.

---

## Deliverable

**Location:** `worktrees/main/mg-core/src/mg_core/helpers/wezterm.py`

### Dataclass for Pane

The `wezterm cli list --format json` command returns detailed pane info. Create a dataclass:

```python
@dataclass
class Pane:
    window_id: int
    tab_id: int
    pane_id: int
    workspace: str
    rows: int
    cols: int
    pixel_width: int
    pixel_height: int
    title: str
    cwd: str
    tab_title: str
    is_active: bool
    is_zoomed: bool
    # ... other fields from JSON
```

### WezTerm Class

Wrap the CLI commands:

```python
class WezTerm:
    def __init__(self, command: list[str] | None = None):
        # Read from mg.toml if not provided
        # Config key: [tools.wezterm] command = ["flatpak", "run", "org.wezfurlong.wezterm"]

    def list_panes(self) -> list[Pane]
    def spawn(self, cwd: str = None, command: list[str] = None,
              window_id: int = None, new_window: bool = False) -> int  # returns pane_id
    def split_pane(self, pane_id: int, direction: str = "right",
                   percent: int = 50, move_pane_id: int = None) -> int
    def move_pane_to_new_tab(self, pane_id: int, window_id: int = None)
    def send_text(self, pane_id: int, text: str)
    def get_text(self, pane_id: int) -> str
    def set_tab_title(self, pane_id: int, title: str)
    def activate_pane(self, pane_id: int)
    def kill_pane(self, pane_id: int)
    def zoom_pane(self, pane_id: int, toggle: bool = True)
```

---

## Reference

Look at existing wrappers for patterns:
- `worktrees/main/mg-core/src/mg_core/helpers/git.py`
- `worktrees/main/mg-core/src/mg_core/helpers/tmux.py`

WezTerm CLI help:
```bash
flatpak run org.wezfurlong.wezterm cli --help
flatpak run org.wezfurlong.wezterm cli list --help
flatpak run org.wezfurlong.wezterm cli spawn --help
# etc.
```

---

## Tests

Write tests in `worktrees/main/mg-core/tests/helpers/test_wezterm.py`

Focus on:
- Dataclass parsing from JSON
- Command construction (don't need to actually call WezTerm in unit tests)

---

## Success Criteria

- Clean wrapper that matches the style of git.py and tmux.py
- All WezTerm CLI commands wrapped
- Pane dataclass with all relevant fields
- Basic test coverage
