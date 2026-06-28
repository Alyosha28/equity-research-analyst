"""chart_football.py -- Football field (valuation range comparison)."""

from __future__ import annotations

import matplotlib.pyplot as plt
from .chart_utils import style_ax, save_fig, get_palette


def render(data: dict, out_dir: str, *, name: str = "football",
           theme: dict | None = None, lang: str = "en-US") -> list[str]:
    """Render a football field chart from engine JSON data.

    Input schema:
        price: float
        lenses: list[{label, low, high, mid?}]

    Returns:
        List of output file paths [svg_path, png_path].
    """
    palette = get_palette(theme)
    cd = (theme or {}).get("chart_defaults", {})

    lenses = data["lenses"]
    price = data.get("price")
    labels = [l["label"] for l in lenses]
    ys = range(len(lenses))

    dpi = (theme or {}).get("figure", {}).get("dpi", 300)
    fig_w = (theme or {}).get("figure", {}).get("default_width", 7.0)
    fig_h = (theme or {}).get("figure", {}).get("default_height", 4.2)

    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    for y, l in zip(ys, lenses):
        lo, hi = l["low"], l["high"]
        ax.plot([lo, hi], [y, y], color=palette["accent"],
                linewidth=9, solid_capstyle="round", alpha=0.85)
        ax.text(lo, y, f"{lo:,.0f} ", va="center", ha="right",
                fontsize=8.5, color=palette["muted"])
        ax.text(hi, y, f" {hi:,.0f}", va="center", ha="left",
                fontsize=8.5, color=palette["muted"])
        if l.get("mid") is not None:
            ax.plot([l["mid"]], [y], marker="D", color=palette["ink"],
                    markersize=7, zorder=3)

    if price is not None:
        ax.axvline(price, color=palette["down"], linewidth=2.0,
                   label=f"Price ${price:,.0f}")
        ax.legend(frameon=False, fontsize=9, loc="lower right")

    ax.set_yticks(list(ys))
    ax.set_yticklabels(labels, fontsize=9.5, color=palette["ink"])
    ax.set_ylim(-0.6, len(lenses) - 0.4)

    style_ax(ax, theme=theme,
             title="Valuation football field",
             xlabel="Value per share ($)")
    ax.grid(axis="y", visible=False)
    return save_fig(fig, out_dir, name, dpi=dpi)
