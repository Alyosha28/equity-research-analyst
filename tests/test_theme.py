"""Tests for theme loading and inheritance merge order.

Covers:
  - _deep_merge: scalar override, nested merge, immutability
  - load_theme: child-overrides-parent inheritance order (the bug fix)
  - Circular inheritance detection
"""

import sys
import os
import tempfile
from pathlib import Path

import pytest

# Make scripts/ importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import theme
from theme import _deep_merge, load_theme


# ---------------------------------------------------------------------------
# _deep_merge unit tests
# ---------------------------------------------------------------------------

class TestDeepMerge:
    def test_scalar_override(self):
        base = {"a": 1, "b": 2}
        override = {"b": 99}
        result = _deep_merge(base, override)
        assert result == {"a": 1, "b": 99}

    def test_nested_merge(self):
        base = {"palette": {"accent": "#002D72", "ink": "#1A1A1A"}}
        override = {"palette": {"accent": "#003A70"}}
        result = _deep_merge(base, override)
        assert result["palette"]["accent"] == "#003A70"
        assert result["palette"]["ink"] == "#1A1A1A"  # unchanged

    def test_new_key_added(self):
        base = {"a": 1}
        override = {"b": 2}
        result = _deep_merge(base, override)
        assert result == {"a": 1, "b": 2}

    def test_override_wins_on_scalar(self):
        base = {"a": "base_value"}
        override = {"a": "override_value"}
        result = _deep_merge(base, override)
        assert result["a"] == "override_value"

    def test_immutable_does_not_mutate_base(self):
        base = {"x": {"y": 1}}
        original = dict(base)
        _deep_merge(base, {"x": {"z": 2}})
        assert base == original  # base untouched

    def test_empty_override_returns_copy(self):
        base = {"a": 1}
        result = _deep_merge(base, {})
        assert result == base
        assert result is not base


# ---------------------------------------------------------------------------
# Theme loading + inheritance merge-order tests
# ---------------------------------------------------------------------------

def _write_theme(dir_, name, extends=None, **extra):
    """Write a minimal theme YAML file to *dir_*."""
    content = {"name": name}
    if extends:
        content["extends"] = extends
    content.update(extra)
    path = dir_ / f"{name}.yaml"
    # Simple YAML output (avoids dependency for test)
    lines = [f"name: {name}"]
    if extends:
        lines.append(f"extends: {extends}")
    for k, v in extra.items():
        lines.append(f"{k}:")
        if isinstance(v, dict):
            for sk, sv in v.items():
                if isinstance(sv, bool):
                    sv = str(sv).lower()
                elif isinstance(sv, str):
                    sv = f'"{sv}"'
                lines.append(f"  {sk}: {sv}")
        else:
            if isinstance(v, str):
                v = f'"{v}"'
            lines.append(f"  {k}: {v}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


class TestLoadTheme:
    """Theme loading with real YAML files in a temp directory."""

    def test_child_overrides_parent_accent(self):
        """The core bug: goldman accent=#003A70 extends default accent=#002D72.

        Before the fix, default was merged LAST and its accent=#002D72 won.
        After the fix, goldman (child) merges LAST and #003A70 wins.
        """
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            _write_theme(d, "default", palette={"accent": "#002D72", "ink": "#1A1A1A"})
            _write_theme(d, "goldman", extends="default", palette={"accent": "#003A70"})

            result = load_theme("goldman", themes_dir=d)

        assert result["name"] == "goldman"
        assert result["palette"]["accent"] == "#003A70", (
            f"Expected child (goldman) accent #003A70 to win, "
            f"got {result['palette']['accent']}"
        )
        # Default's ink should still be inherited
        assert result["palette"]["ink"] == "#1A1A1A"

    def test_default_loaded_directly(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            _write_theme(d, "default", palette={"accent": "#002D72"})

            result = load_theme("default", themes_dir=d)

        assert result["palette"]["accent"] == "#002D72"

    def test_deep_merge_preserves_sibling_keys(self):
        """child adds one key, parent's sibling keys survive."""
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            _write_theme(d, "default", palette={"accent": "#002D72", "ink": "#111"})
            _write_theme(d, "child", extends="default", palette={"up": "#0F0"})

            result = load_theme("child", themes_dir=d)

        assert result["palette"]["accent"] == "#002D72"
        assert result["palette"]["ink"] == "#111"
        assert result["palette"]["up"] == "#0F0"

    def test_three_level_chain(self):
        """grandchild > child > default — grandchild wins."""
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            _write_theme(d, "default", palette={"accent": "#000", "ink": "#111"})
            _write_theme(d, "mid", extends="default", palette={"accent": "#333"})
            _write_theme(d, "leaf", extends="mid", palette={"accent": "#666"})

            result = load_theme("leaf", themes_dir=d)

        assert result["palette"]["accent"] == "#666"
        assert result["palette"]["ink"] == "#111"

    def test_circular_detection(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            _write_theme(d, "a", extends="b", palette={})
            _write_theme(d, "b", extends="a", palette={})

            with pytest.raises(ValueError, match="Circular"):
                load_theme("a", themes_dir=d)

    def test_missing_theme_raises(self):
        with tempfile.TemporaryDirectory() as td:
            with pytest.raises(ValueError, match="not found"):
                load_theme("nope", themes_dir=Path(td))
