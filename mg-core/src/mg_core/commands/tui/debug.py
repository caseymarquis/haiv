"""mg tui debug - Print WezTerm pane layout for debugging."""

from mg import cmd


def define() -> cmd.Def:
    return cmd.Def(
        description="Print WezTerm pane layout for debugging",
    )


def execute(ctx: cmd.Ctx) -> None:
    from mg.wrappers.wezterm import WezTerm

    wezterm = WezTerm(ctx.settings.wezterm_command, quiet=True)

    try:
        panes = wezterm.list_panes()
    except Exception as e:
        ctx.print(f"Failed to list panes: {e}")
        return

    if not panes:
        ctx.print("No panes found.")
        return

    # Group by window, then tab
    from collections import defaultdict

    windows: dict[int, dict[int, list]] = defaultdict(lambda: defaultdict(list))
    for p in panes:
        windows[p.window_id][p.tab_id].append(p)

    for window_id in sorted(windows):
        ctx.print(f"Window {window_id}")
        for tab_id in sorted(windows[window_id]):
            tab_panes = windows[window_id][tab_id]
            tab_title = tab_panes[0].tab_title or "(untitled)"
            ctx.print(f"  Tab {tab_id}: {tab_title}")
            for p in sorted(tab_panes, key=lambda p: (p.top_row, p.left_col)):
                active = " *" if p.is_active else ""
                pos = f"col={p.left_col} row={p.top_row}"
                size = f"{p.size.cols}x{p.size.rows}"
                ctx.print(f"    Pane {p.pane_id}: {size} {pos} title={p.title!r}{active}")
