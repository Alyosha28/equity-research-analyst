"""Theme loader for chart generation.

Loads theme YAML files, merges with defaults, and applies rcParams globally.
Supports theme inheritance via the 'extends' key.
"""

import yaml
import os
from pathlib import Path

THEMES_DIR = Path(__file__).resolve().parent.parent / "themes"


def load_theme(name="default"):
    """Load a named theme, resolving inheritance.

    Args:
        name: Theme name (matches filename without .yaml). E.g., 'default',
              'goldman', 'ms', 'cjk'.

    Returns:
        Dict with resolved theme configuration.
    """
    themes = {}
    for f in sorted(THEMES_DIR.glob("*.yaml")):
        with open(f, "r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
            if data and "name" in data:
                themes[data["name"]] = data

    if name not in themes:
        raise ValueError(
            f"Theme '{name}' not found. Available: {sorted(themes.keys())}"
        )

    # Resolve inheritance chain from parent to child so child values win.
    chain = []
    current = name
    while current:
        if current in chain:
            raise ValueError(f"Circular theme inheritance: {chain}")
        chain.append(current)
        t = themes.get(current)
        if not t:
            break
        current = t.get("extends")

    resolved = {}
    for theme_name in reversed(chain):
        resolved = _deep_merge(resolved, themes[theme_name])

    return resolved


def _deep_merge(base, override):
    """Recursively merge override into base dict. Immutable -- returns new dict."""
    result = dict(base)
    for k, v in override.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = _deep_merge(result[k], v)
        else:
            result[k] = v
    return result


def apply_theme(name="default", lang="zh-CN"):
    """Load theme and apply rcParams + CJK fonts.

    Call once before any figure creation.

    Args:
        name: Theme name.
        lang: Language code for CJK font selection.

    Returns:
        Theme dict.
    """
    import matplotlib
    from .cjk_fonts import configure_cjk_fonts

    theme = load_theme(name)

    # Apply rcParams
    rc = theme.get("rcparams", {})
    for key, value in rc.items():
        matplotlib.rcParams[key] = value

    # Apply CJK fonts
    configure_cjk_fonts(lang)

    # Apply style base
    try:
        import matplotlib.style
        matplotlib.style.use("seaborn-v0_8-whitegrid")
    except Exception:
        pass  # style not critical

    return theme
