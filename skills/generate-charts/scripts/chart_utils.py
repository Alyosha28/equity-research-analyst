"""Shared utilities for chart rendering.

Provides style_ax(), save_fig(), format_currency(), add_source_footnote(),
and palette access functions used by all per-chart modules.
"""

from __future__ import annotations

import os
import matplotlib.pyplot as plt
import matplotlib

# Default palette (used when theme is not loaded)
_DEFAULT_PALETTE = {
    "ink": "#1A1A1A",
    "muted": "#6B7280",
    "grid": "#D1D5DB",
    "accent": "#002D72",
    "accent_light": "#4A7AB5",
    "up": "#0E6E4D",
    "down": "#CC0000",
    "band": "#F3F4F6",
    "surface": "#FFFFFF",
}


def get_palette(theme=None):
    """Return the active palette from theme, or defaults.

    Args:
        theme: Resolved theme dict. If None, uses built-in defaults.

    Returns:
        Dict with palette colour keys.
    """
    if theme is None:
        return dict(_DEFAULT_PALETTE)
    return theme.get("palette", _DEFAULT_PALETTE)


def _resolve_color(palette, key, fallback=None):
    """Resolve a named colour from the palette dict."""
    if isinstance(key, str) and key in palette:
        return palette[key]
    return key if fallback is None else fallback


def style_ax(ax, theme=None, title=None, xlabel=None, ylabel=None,
             subtitle=None, source=None):
    """Apply consistent styling to an axes.

    Args:
        ax: matplotlib Axes object.
        theme: Resolved theme dict (or None for defaults).
        title: Bold title text (10pt, left-aligned).
        xlabel: X-axis label text.
        ylabel: Y-axis label text.
        subtitle: Subtitle text (7.5pt, below title).
        source: Source footnote text (6.5pt, bottom-left).
    """
    palette = get_palette(theme)
    cd = (theme or {}).get("chart_defaults", {})

    title_fs = cd.get("title_fontsize", 10)
    title_fw = cd.get("title_fontweight", "bold")
    title_loc = cd.get("title_loc", "left")
    title_pad = cd.get("title_pad", 10)
    subtitle_fs = cd.get("subtitle_fontsize", 7.5)
    subtitle_c = _resolve_color(palette, cd.get("subtitle_color", palette["muted"]))
    source_fs = cd.get("source_fontsize", 6.5)

    ink = palette["ink"]
    muted = palette["muted"]
    grid = palette["grid"]

    ax.set_title(title, color=ink, fontsize=title_fs, fontweight=title_fw,
                 loc=title_loc, pad=title_pad)
    if xlabel:
        ax.set_xlabel(xlabel, color=muted, fontsize=9)
    if ylabel:
        ax.set_ylabel(ylabel, color=muted, fontsize=9)

    # Subtitle as a text annotation below the title
    if subtitle:
        ax.text(0, 1.01, subtitle, transform=ax.transAxes,
                fontsize=subtitle_fs, color=subtitle_c, va="bottom", ha="left")

    # Source footnote at bottom-left
    if source:
        ax.text(0, -0.10, source, transform=ax.transAxes,
                fontsize=source_fs, color=muted, va="top", ha="left")

    ax.tick_params(colors=muted, labelsize=8)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color(grid)
        ax.spines[spine].set_linewidth(0.8)
    ax.grid(axis="both", color=grid, linewidth=0.6, alpha=0.7)
    ax.set_axisbelow(True)


def save_fig(fig, out_dir, name, dpi=None):
    """Save figure as SVG and PNG, then close.

    Args:
        fig: matplotlib Figure.
        out_dir: Output directory (created if needed).
        name: File stem (no extension).
        dpi: DPI for raster output (default 300).

    Returns:
        List of output file paths [svg_path, png_path].
    """
    if dpi is None:
        dpi = 300
    os.makedirs(out_dir, exist_ok=True)
    paths = []
    svg_path = os.path.join(out_dir, f"{name}.svg")
    png_path = os.path.join(out_dir, f"{name}.png")
    fig.savefig(svg_path, bbox_inches="tight", facecolor="white")
    fig.savefig(png_path, dpi=dpi, bbox_inches="tight", facecolor="white")
    paths.extend([svg_path, png_path])
    plt.close(fig)
    return paths


def add_source_footnote(fig, theme=None, text="Source: DCF valuation engine"):
    """Add a source footnote to the figure (not axis-specific).

    Args:
        fig: matplotlib Figure.
        theme: Resolved theme dict.
        text: Source text.
    """
    palette = get_palette(theme)
    cd = (theme or {}).get("chart_defaults", {})
    fs = cd.get("source_fontsize", 6.5)
    fig.text(0.01, 0.005, text, fontsize=fs, color=palette["muted"],
             ha="left", va="bottom")


def format_currency(value, decimals=0):
    """Format a number as a human-readable currency string.

    Args:
        value: Numeric value.
        decimals: Decimal places.

    Returns:
        String like '$1,450' or '$12.5B'.
    """
    if abs(value) >= 1e12:
        return f"${value / 1e12:,.{decimals}f}T"
    if abs(value) >= 1e9:
        return f"${value / 1e9:,.{decimals}f}B"
    if abs(value) >= 1e6:
        return f"${value / 1e6:,.{decimals}f}M"
    return f"${value:,.{decimals}f}"
