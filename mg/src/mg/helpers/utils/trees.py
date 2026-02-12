"""Generic tree building and rendering.

Builds a tree from a flat sequence of (item, parent_ref) pairs.
Uses object identity to match children to parents.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass
class TreeNode(Generic[T]):
    """A node in a tree."""

    item: T
    parent: T | None = None
    parent_node: TreeNode[T] | None = None
    children: list[T] = field(default_factory=list)
    child_nodes: list[TreeNode[T]] = field(default_factory=list)


def build_tree(items: Sequence[tuple[T, T | None]]) -> list[TreeNode[T]]:
    """Build a tree from (item, parent_ref_or_None) pairs.

    Uses object identity to match parents. Items whose parent is None
    or not present in the list become roots.

    Raises ValueError if a cycle is detected.
    """
    nodes: dict[int, TreeNode[T]] = {}
    for item, parent in items:
        if id(item) in nodes:
            raise ValueError("Duplicate item in tree input")
        nodes[id(item)] = TreeNode(item=item, parent=parent)

    # Link children to parents
    roots: list[TreeNode[T]] = []
    for item, parent in items:
        node = nodes[id(item)]
        if parent is not None and id(parent) in nodes:
            parent_node = nodes[id(parent)]
            node.parent_node = parent_node
            parent_node.children.append(item)
            parent_node.child_nodes.append(node)
        else:
            roots.append(node)

    # Detect cycles: every node must be reachable from a root
    reachable: set[int] = set()

    def _walk(node: TreeNode[T]) -> None:
        reachable.add(id(node.item))
        for child in node.child_nodes:
            _walk(child)

    for root in roots:
        _walk(root)

    for item, _ in items:
        if id(item) not in reachable:
            raise ValueError("Cycle detected in tree input")

    return roots


def render_tree(
    roots: list[TreeNode[T]],
    format_item: Callable[[T], str],
) -> list[str]:
    """Render a tree as lines with connectors.

    Args:
        roots: Root nodes to render.
        format_item: Callback to format each item into a display string.

    Returns:
        Lines ready to print, using ├─/└─/│ connectors.
        Blank lines separate root-level trees.
    """
    lines: list[str] = []

    def _render_node(node: TreeNode[T], prefix: str, connector: str) -> None:
        lines.append(f"{prefix}{connector}{format_item(node.item)}")
        for i, child in enumerate(node.child_nodes):
            is_last = i == len(node.child_nodes) - 1
            if connector == "":
                child_prefix = prefix
            elif connector == "├─ ":
                child_prefix = prefix + "│  "
            else:  # └─
                child_prefix = prefix + "   "
            _render_node(child, child_prefix, "└─ " if is_last else "├─ ")

    for i, root in enumerate(roots):
        if i > 0:
            lines.append("")
        _render_node(root, "", "")

    return lines
