"""Tests for theme loading and application."""

import sys
import os

# Ensure we can import from the scripts directory
_scripts_dir = os.path.join(os.path.dirname(__file__), "..", "scripts")
sys.path.insert(0, _scripts_dir)

import pytest


class TestLoadTheme:
    """Tests for theme.load_theme()."""

    def test_load_default_theme(self):
        """Default theme should load without error."""
        from theme import load_theme
        theme = load_theme("default")
        assert theme is not None
        assert "name" in theme
        assert theme["name"] == "default"
        assert "palette" in theme
        assert "ink" in theme["palette"]
        assert "accent" in theme["palette"]

    def test_load_goldman_theme(self):
        """Goldman theme should extend default."""
        from theme import load_theme
        theme = load_theme("goldman")
        assert theme is not None
        assert "name" in theme
        assert theme["name"] == "goldman"
        # Should inherit palette from default but override accent
        assert "palette" in theme
        assert theme["palette"]["accent"] == "#003A70"

    def test_load_ms_theme(self):
        """Morgan Stanley theme should extend default."""
        from theme import load_theme
        theme = load_theme("ms")
        assert theme is not None
        assert theme["name"] == "ms"
        assert theme["palette"]["accent"] == "#1C4587"

    def test_load_cjk_theme(self):
        """CJK theme should extend default with larger fonts."""
        from theme import load_theme
        theme = load_theme("cjk")
        assert theme is not None
        assert theme["name"] == "cjk"
        assert theme["chart_defaults"]["title_fontsize"] == 11

    def test_unknown_theme_raises(self):
        """Loading a nonexistent theme should raise ValueError."""
        from theme import load_theme
        with pytest.raises(ValueError, match="Theme 'nonexistent' not found"):
            load_theme("nonexistent")

    def test_all_themes_have_palette(self):
        """Every theme should have a palette with ink and accent."""
        from theme import load_theme
        for name in ("default", "goldman", "ms", "cjk"):
            theme = load_theme(name)
            assert "ink" in theme["palette"], f"{name} missing ink"
            assert "accent" in theme["palette"], f"{name} missing accent"


class TestDeepMerge:
    """Tests for theme._deep_merge()."""

    def test_simple_override(self):
        from theme import _deep_merge
        base = {"a": 1, "b": 2}
        override = {"b": 3}
        result = _deep_merge(base, override)
        assert result["a"] == 1
        assert result["b"] == 3

    def test_nested_merge(self):
        from theme import _deep_merge
        base = {"palette": {"ink": "#000", "accent": "#001"}}
        override = {"palette": {"accent": "#002"}}
        result = _deep_merge(base, override)
        assert result["palette"]["ink"] == "#000"
        assert result["palette"]["accent"] == "#002"

    def test_original_unmodified(self):
        """Deep merge should not mutate the original dict."""
        from theme import _deep_merge
        base = {"palette": {"ink": "#000"}}
        original_base = {"palette": {"ink": "#000"}}
        override = {"palette": {"accent": "#001"}}
        _deep_merge(base, override)
        assert base == original_base


class TestCjkFonts:
    """Tests for cjk_fonts module."""

    def test_configure_returns_value(self):
        """configure_cjk_fonts should return a font name or None."""
        from cjk_fonts import configure_cjk_fonts
        result = configure_cjk_fonts("zh-CN")
        # result may be None if no CJK font installed, which is fine
        assert result is None or isinstance(result, str)

    def test_detect_best_cjk_returns_optional(self):
        """_detect_best_cjk should return a string or None."""
        from cjk_fonts import _detect_best_cjk
        result = _detect_best_cjk("zh-CN")
        assert result is None or isinstance(result, str)

    def test_available_fonts_is_set(self):
        """_available_fonts should return a set."""
        from cjk_fonts import _available_fonts
        fonts = _available_fonts()
        assert isinstance(fonts, set)
