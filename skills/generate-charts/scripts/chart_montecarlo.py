"""chart_montecarlo.py -- Monte Carlo histogram."""

from __future__ import annotations

import matplotlib.pyplot as plt
from .chart_utils import style_ax, save_fig, get_palette


def render(data, out_dir, *, name="montecarlo", theme=None, lang="en-US"):
    palette = get_palette(theme)

    values = data["values"]
    band = data.get("mos_band", {})
    price = data.get("price")

    dpi = (theme or {}).get("figure", {}).get("dpi", 300)
    fig_w = (theme or {}).get("figure", {}).get("default_width", 7.0)
    fig_h = (theme or {}).get("figure", {}).get("default_height", 4.2)

    fig, ax = plt.subplots(figsize=(fig_w, fig_h))

    ax.hist(values, bins=60, color=palette["accent"], alpha=0.55,
            edgecolor="white", linewidth=0.3)

    if band:
        label_text = (
            f'MoS buy-band ({band["mos"]:.0%})'
        )
        ax.axvspan(band["buy_below"], band["rich_above"],
                   color=palette["band"], alpha=0.10,
                   label=label_text)
        ax.axvline(band["buy_below"], color=palette["up"],
                   linewidth=1.4, linestyle="--",
                   label=f'Accumulate <= ${band["buy_below"]:,.0f}')
        ax.axvline(band["median"], color=palette["ink"],
                   linewidth=1.6,
                   label=f'Fair (median) ${band["median"]:,.0f}')

    if price is not None:
        pctl = data.get("price_percentile")
        lab = f"Price ${price:,.0f}"
        if pctl is not None:
            lab += f"  ({pctl:.0%} pctile)"
        ax.axvline(price, color=palette["down"], linewidth=2.0, label=lab)

    style_ax(ax, theme=theme,
             title="Intrinsic value distribution -- Monte Carlo",
             xlabel="Intrinsic value per share ($)",
             ylabel="Frequency (trials)")

    ax.legend(frameon=False, fontsize=8.5, loc="upper right")
    return save_fig(fig, out_dir, name, dpi=dpi)
