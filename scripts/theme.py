"""Theme loader for chart generation.

Loads theme YAML files, merges with defaults, and applies rcParams globally.
Supports theme inheritance via the 'extends' key.

BUG FIX (2026-06-28):
    _deep_merge(base, override) gives override the final say.  The original
    load_theme built a chain [child, ..., parent] and merged in that order,
    so parent (default) was merged LAST and its values always won.

    Corrected: build the chain, then REVERSE it so root merges first.
    Leaf (most specific child) merges last and wins.
"""

import os
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

THEMES_DIR = Path(__file__).resolve().parent.parent / "themes"


def load_theme(name="default", themes_dir=None):
    """Load a named theme, resolving inheritance.

    Args:
        name: Theme name (matches filename without .yaml).
        themes_dir: Optional override for the themes directory.

    Returns:
        Dict with resolved theme configuration.

    Raises:
        ValueError: Theme not found or circular inheritance detected.
    """
    src = Path(themes_dir) if themes_dir else THEMES_DIR

    if yaml is None:
        raise ImportError("PyYAML is required: pip install pyyaml")

    # Load all theme files
    themes = {}
    for f in sorted(src.glob("*.yaml")):
        with open(f, "r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
            if data and "name" in data:
                themes[data["name"]] = data

    if name not in themes:
        raise ValueError(
            f"Theme '{name}' not found. Available: {sorted(themes.keys())}"
        )

    # Build inheritance chain from leaf to root
    chain = []        # [goldman, default]  for "goldman extends default"
    current = name
    while current:
        if current in chain:
            raise ValueError(f"Circular theme inheritance: {chain + [current]}")
        chain.append(current)
        t = themes.get(current)
        if not t:
            break
        current = t.get("extends")

    # Merge from ROOT to LEAF so child overrides parent.
    # chain is [child, ..., root] -> reverse to [root, ..., child].
    resolved = {}
    for theme_name in reversed(chain):
        t = themes[theme_name]
        resolved = _deep_merge(resolved, t)

    return resolved


def _deep_merge(base, override):
    """Recursively merge *override* into *base*.

    Immutable: returns a new dict.  Override scalars replace base scalars;
    nested dicts recurse.
    """
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
    """
    import matplotlib

    theme = load_theme(name)

    # Apply rcParams
    rc = theme.get("rcparams", {})
    for key, value in rc.items():
        matplotlib.rcParams[key] = value

    # Apply CJK fonts (optional)
    try:
        from .cjk_fonts import configure_cjk_fonts
        configure_cjk_fonts(lang)
    except ImportError:
        pass

    # Apply style base
    try:
        import matplotlib.style
        matplotlib.style.use("seaborn-v0_8-whitegrid")
    except Exception:
        pass

    return theme
