"""Tests for mg.helpers.utils.trees module."""

import pytest

from mg.helpers.utils.trees import TreeNode, build_tree, render_tree


class TestBuildTree:
    """Tests for build_tree()."""

    def test_empty_input(self):
        """Returns empty list for empty input."""
        assert build_tree([]) == []

    def test_single_root(self):
        """Single item with no parent becomes a root."""
        a = "a"
        [root] = build_tree([(a, None)])

        assert root.item is a
        assert root.parent is None
        assert root.parent_node is None
        assert root.children == []
        assert root.child_nodes == []

    def test_multiple_roots(self):
        """Items with no parent all become roots."""
        a, b, c = "a", "b", "c"
        roots = build_tree([(a, None), (b, None), (c, None)])

        assert [r.item for r in roots] == [a, b, c]

    def test_single_child(self):
        """Child is linked to its parent."""
        parent = "parent"
        child = "child"
        roots = build_tree([(parent, None), (child, parent)])

        assert len(roots) == 1
        root = roots[0]
        assert root.item is parent
        assert root.children == [child]
        assert len(root.child_nodes) == 1

        child_node = root.child_nodes[0]
        assert child_node.item is child
        assert child_node.parent is parent
        assert child_node.parent_node is root

    def test_multiple_children(self):
        """Multiple children under one parent."""
        p = "parent"
        c1, c2, c3 = "c1", "c2", "c3"
        roots = build_tree([(p, None), (c1, p), (c2, p), (c3, p)])

        [root] = roots
        assert root.children == [c1, c2, c3]
        assert all(cn.parent is p for cn in root.child_nodes)

    def test_three_levels(self):
        """Grandchild linked through child to root."""
        gp = "grandparent"
        p = "parent"
        c = "child"
        roots = build_tree([(gp, None), (p, gp), (c, p)])

        [root] = roots
        assert root.item is gp
        [mid] = root.child_nodes
        assert mid.item is p
        [leaf] = mid.child_nodes
        assert leaf.item is c
        assert leaf.parent is p
        assert leaf.parent_node is mid

    def test_orphan_becomes_root(self):
        """Item whose parent is not in the list becomes a root."""
        missing_parent = "ghost"
        orphan = "orphan"
        roots = build_tree([(orphan, missing_parent)])

        assert len(roots) == 1
        assert roots[0].item is orphan
        assert roots[0].parent is missing_parent
        assert roots[0].parent_node is None

    def test_mixed_roots_and_children(self):
        """Mix of root sessions and delegated children."""
        r1 = "root1"
        r2 = "root2"
        c1 = "child_of_r1"
        roots = build_tree([(r1, None), (r2, None), (c1, r1)])

        assert len(roots) == 2
        assert roots[0].item is r1
        assert roots[1].item is r2
        assert roots[0].children == [c1]
        assert roots[1].children == []

    def test_identity_not_equality(self):
        """Matching uses identity (is), not equality (==)."""
        a = "same"
        b = "same"  # equal but not identical (though CPython may intern these)
        # Use lists to guarantee distinct identity
        a = ["same"]
        b = ["same"]
        assert a == b and a is not b

        roots = build_tree([(a, None), (b, a)])
        # b's parent is a, so b is a child of a
        assert len(roots) == 1
        assert roots[0].item is a
        assert roots[0].child_nodes[0].item is b

    def test_preserves_input_order(self):
        """Roots appear in the same order as the input."""
        items = ["d", "b", "a", "c"]
        roots = build_tree([(i, None) for i in items])

        assert [r.item for r in roots] == items

    def test_self_reference_raises(self):
        """Item that is its own parent raises ValueError."""
        a = "self-ref"
        with pytest.raises(ValueError, match="Cycle detected"):
            build_tree([(a, a)])

    def test_two_node_cycle_raises(self):
        """A→B→A cycle raises ValueError."""
        a, b = ["a"], ["b"]
        with pytest.raises(ValueError, match="Cycle detected"):
            build_tree([(a, b), (b, a)])

    def test_three_node_cycle_raises(self):
        """A→B→C→A cycle raises ValueError."""
        a, b, c = ["a"], ["b"], ["c"]
        with pytest.raises(ValueError, match="Cycle detected"):
            build_tree([(a, c), (b, a), (c, b)])

    def test_cycle_mixed_with_normal_raises(self):
        """Cycle raises even when mixed with valid items."""
        r = "root"
        child = "child"
        a, b = ["a"], ["b"]
        with pytest.raises(ValueError, match="Cycle detected"):
            build_tree([(r, None), (child, r), (a, b), (b, a)])

    def test_duplicate_item_raises(self):
        """Same item appearing twice raises ValueError."""
        a = ["a"]
        b = ["b"]
        with pytest.raises(ValueError, match="Duplicate item"):
            build_tree([(a, None), (a, b)])


class TestRenderTree:
    """Tests for render_tree()."""

    def _build(self, items):
        """Helper: build tree from (item, parent_ref) pairs."""
        return build_tree(items)

    def test_empty(self):
        """Empty roots produce no lines."""
        assert render_tree([], str) == []

    def test_single_root(self):
        """Single root, no children."""
        a = "alpha"
        roots = self._build([(a, None)])
        assert render_tree(roots, str) == ["alpha"]

    def test_multiple_roots(self):
        """Multiple roots separated by blank lines."""
        a, b = "alpha", "beta"
        roots = self._build([(a, None), (b, None)])
        assert render_tree(roots, str) == ["alpha", "", "beta"]

    def test_single_child(self):
        """One child uses └─ connector."""
        p, c = "parent", "child"
        roots = self._build([(p, None), (c, p)])
        assert render_tree(roots, str) == [
            "parent",
            "└─ child",
        ]

    def test_multiple_children(self):
        """Non-last children use ├─, last uses └─."""
        p = "parent"
        c1, c2, c3 = "first", "second", "third"
        roots = self._build([(p, None), (c1, p), (c2, p), (c3, p)])
        assert render_tree(roots, str) == [
            "parent",
            "├─ first",
            "├─ second",
            "└─ third",
        ]

    def test_nested_children(self):
        """Deeper nesting indents with │ continuation."""
        gp, p, c = "gp", "p", "c"
        roots = self._build([(gp, None), (p, gp), (c, p)])
        assert render_tree(roots, str) == [
            "gp",
            "└─ p",
            "   └─ c",
        ]

    def test_sibling_continuation_lines(self):
        """│ continues for non-last branches at each level."""
        r = "root"
        a, b = "a", "b"
        a1 = "a1"
        roots = self._build([(r, None), (a, r), (b, r), (a1, a)])
        assert render_tree(roots, str) == [
            "root",
            "├─ a",
            "│  └─ a1",
            "└─ b",
        ]

    def test_custom_formatter(self):
        """format_item callback controls the display string."""
        a = 42
        roots = self._build([(a, None)])
        assert render_tree(roots, lambda n: f"item={n}") == ["item=42"]

    def test_multiple_roots_with_children(self):
        """Multiple root trees separated by blank lines."""
        r1, r2 = "r1", "r2"
        c1 = "c1"
        roots = self._build([(r1, None), (r2, None), (c1, r1)])
        assert render_tree(roots, str) == [
            "r1",
            "└─ c1",
            "",
            "r2",
        ]
