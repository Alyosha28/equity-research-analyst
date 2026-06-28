"""chart_waterfall.py -- Driver waterfall bridge."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from .chart_utils import style_ax, save_fig, get_palette


def render(data, out_dir, *, name="waterfall", theme=None, lang="en-US"):
    palette = get_palette(theme)
    steps = data["steps"]
    price = data.get("price")
    base_value = data.get("base_value") or data.get("intrinsic_value")

    n = len(steps)
    bar_width = 0.6
    x = np.arange(n)
    dpi = (theme or {}).get("figure", {}).get("dpi", 300)
    fig_width = max(9, n * 1.15)
    fig_h = (theme or {}).get("figure", {}).get("default_height", 4.2)

    fig, ax = plt.subplots(figsize=(fig_width, fig_h))

    bottoms = []
    heights = []
    colors = []
    labels_text = []

    running = 0.0
    for i, s in enumerate(steps):
        val = s.get("value")
        delta = s.get("delta", 0)
        is_pos = s.get("is_positive", s.get("direction", "up") in ("up", "positive"))

        if i == 0:
            bottom = 0
            height = val if val else 0
            color = palette["accent"]
            running = height
        elif i == n - 1:
            bottom = 0
            height = val if val else running
            color = palette["accent"]
            running = height
        else:
            if is_pos:
                bottom = running
                height = abs(delta)
                running += height
                color = palette["up"]
            else:
                running += delta
                bottom = running
                height = abs(delta)
                color = palette["down"]

        bottoms.append(bottom)
        heights.append(height)
        colors.append(color)
        labels_text.append(s.get("label", ""))

    ax.bar(x, heights, bar_width, bottom=bottoms, color=colors,
           edgecolor="white", linewidth=0.5)

    for i in range(n):
        label_val = steps[i].get("value", running)
        max_h = max(heights) if heights else 1
        offset = max_h * 0.02
        ax.text(i, bottoms[i] + heights[i] + offset, f"{label_val:,.0f}",
                ha="center", va="bottom", fontsize=8.5, color=palette["ink"],
                fontweight="bold")

    for i in range(n - 1):
        top_i = bottoms[i] + heights[i]
        top_j = bottoms[i + 1] + heights[i + 1]
        ax.plot([i + bar_width / 2, i + 1 - bar_width / 2], [top_i, top_j],
                color=palette["grid"], linewidth=0.8, linestyle="-", zorder=0)

    ax.set_xticks(x)
    wrapped_labels = [l.replace(" ", "\n") if len(l) > 20 else l for l in labels_text]
    ax.set_xticklabels(wrapped_labels, fontsize=7.5, color=palette["ink"],
                       rotation=0, ha="center")

    if price is not None:
        ax.axhline(price, color=palette["down"], linewidth=1.2, linestyle="--",
                   alpha=0.6, label=f"Market price ${price:,.0f}")
        ax.legend(frameon=False, fontsize=8.5, loc="upper right")

    if base_value and price:
        gap = price - base_value
        chart_title = (f"Value Bridge: from ${base_value:,.0f} to "
                       f"${price:,.0f} (gap: ${gap:+,.0f})")
        ax.set_title(chart_title, color=palette["ink"], fontsize=13,
                     fontweight="bold", loc="left", pad=12)
    else:
        style_ax(ax, theme=theme,
                 title="Value Bridge: Driver Contributions",
                 ylabel="Value per share ($)")
        return save_fig(fig, out_dir, name, dpi=dpi)

    ax.set_ylabel("Value per share ($)", color=palette["muted"], fontsize=10)
    ax.tick_params(colors=palette["muted"], labelsize=9)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color(palette["grid"])
    ax.grid(axis="y", color=palette["grid"], linewidth=0.6, alpha=0.7)
    ax.set_axisbelow(True)
    return save_fig(fig, out_dir, name, dpi=dpi)
