"""chart_tornado.py -- Sensitivity tornado."""

from __future__ import annotations

import matplotlib.pyplot as plt
from .chart_utils import style_ax, save_fig, get_palette


def render(data: dict, out_dir: str, *, name: str = "tornado",
           theme: dict | None = None, lang: str = "en-US") -> list[str]:
    """Render a sensitivity tornado chart from engine JSON data.

    Input schema:
        base: float
        drivers: list[{name, low, high}]

    Returns:
        List of output file paths [svg_path, png_path].
    """
    palette = get_palette(theme)
    cd = (theme or {}).get("chart_defaults", {})

    base = data["base"]
    drivers = sorted(data["drivers"], key=lambda d: abs(d["high"] - d["low"]))
    names = [d["name"] for d in drivers]
    ys = range(len(drivers))

    dpi = (theme or {}).get("figure", {}).get("dpi", 300)
    fig_w = (theme or {}).get("figure", {}).get("default_width", 7.0)
    fig_h = (theme or {}).get("figure", {}).get("default_height", 4.2)

    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    for y, d in zip(ys, drivers):
        lo, hi = sorted((d["low"], d["high"]))
        ax.barh(y, lo - base, left=base, color=palette["down"], alpha=0.75)
        ax.barh(y, hi - base, left=base, color=palette["up"], alpha=0.75)

    ax.axvline(base, color=palette["ink"], linewidth=1.6,
               label=f"Base ${base:,.0f}")
    ax.set_yticks(list(ys))
    ax.set_yticklabels(names, fontsize=9.5, color=palette["ink"])
    ax.legend(frameon=False, fontsize=9, loc="lower right")

    style_ax(ax, theme=theme,
             title="Sensitivity (tornado): value per share vs driver +/-1SD",
             xlabel="Value per share ($)")
    ax.grid(axis="y", visible=False)
    return save_fig(fig, out_dir, name, dpi=dpi)
