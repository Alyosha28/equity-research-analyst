"""chart_breakeven.py -- Breakeven heatmap."""

from __future__ import annotations

import matplotlib.pyplot as plt
from .chart_utils import style_ax, save_fig, get_palette


def render(data: dict, out_dir: str, *, name: str = "breakeven",
           theme: dict | None = None, lang: str = "en-US") -> list[str]:
    """Render a breakeven heatmap from engine JSON data.

    Input schema:
        revenues: list[float] -- Y10 revenue levels
        margins: list[float]  -- target operating margins
        grid: list[list[float]] -- 2D value grid
        price: float
        base_revenue: float
        base_margin: float

    Returns:
        List of output file paths [svg_path, png_path].
    """
    palette = get_palette(theme)
    cd = (theme or {}).get("chart_defaults", {})

    grid = data["grid"]
    revenues = data["revenues"]
    margins = data["margins"]
    price = data.get("price")

    dpi = (theme or {}).get("figure", {}).get("dpi", 300)
    fig_w = (theme or {}).get("figure", {}).get("default_width", 7.0)
    fig_h = (theme or {}).get("figure", {}).get("default_height", 4.2)

    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    im = ax.imshow(grid, aspect="auto", origin="lower", cmap="RdYlGn")
    ax.set_xticks(range(len(margins)))
    ax.set_xticklabels([f"{m:.0%}" for m in margins])
    ax.set_yticks(range(len(revenues)))
    ax.set_yticklabels([f"{r/1000:,.0f}B" for r in revenues])

    for i, row in enumerate(grid):
        for j, v in enumerate(row):
            star = "*" if (price is not None and v >= price) else ""
            ax.text(j, i, f"{v:.0f}{star}", ha="center", va="center",
                    fontsize=8, color=palette["ink"])

    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.02)
    cbar.set_label("Value per share ($)", color=palette["muted"], fontsize=9)

    sub = f"  (star = reaches price ${price:,.0f})" if price is not None else ""
    style_ax(ax, theme=theme,
             title="Breakeven: what must be true for the price to be right" + sub,
             xlabel="Target operating margin",
             ylabel="Year-10 revenue")
    ax.grid(visible=False)
    return save_fig(fig, out_dir, name, dpi=dpi)
