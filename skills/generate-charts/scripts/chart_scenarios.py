"""chart_scenarios.py -- Scenario comparison bar/waterfall."""

from __future__ import annotations

import matplotlib.pyplot as plt
from .chart_utils import style_ax, save_fig, get_palette


def render(data, out_dir, *, name="scenarios", theme=None, lang="en-US"):
    palette = get_palette(theme)
    scenarios = data["scenarios"]
    price = data.get("price")
    names = [s["name"] for s in scenarios]
    ys = list(range(len(scenarios)))

    dpi = (theme or {}).get("figure", {}).get("dpi", 300)
    fig_w = (theme or {}).get("figure", {}).get("default_width", 7.0)
    fig_h = (theme or {}).get("figure", {}).get("default_height", 4.2)

    fig, ax = plt.subplots(figsize=(fig_w, fig_h))

    for y, s in zip(ys, scenarios):
        v = s.get("value_per_share")
        if v is not None:
            lo = s.get("value_low", v)
            hi = s.get("value_high", v)
        else:
            lo = s.get("value_low", 0)
            hi = s.get("value_high", 0)

        color = palette["accent"]
        if "bear" in s["name"].lower():
            color = palette["down"]
        elif "bull" in s["name"].lower():
            color = palette["up"]

        if lo != hi:
            ax.plot([lo, hi], [y, y], color=color, linewidth=10,
                    solid_capstyle="round", alpha=0.80)
            ax.text(lo, y, f"{lo:,.0f} ", va="center", ha="right",
                    fontsize=8.5, color=palette["muted"])
            ax.text(hi, y, f" {hi:,.0f}", va="center", ha="left",
                    fontsize=8.5, color=palette["muted"])

        mid = s.get("value_mid")
        if mid is None:
            mid = (lo + hi) / 2 if lo != hi else v
        if mid:
            ax.plot([mid], [y], marker="D", color=palette["ink"],
                    markersize=8, zorder=3)
            ax.text(mid, y - 0.35, f"{mid:,.0f}", ha="center", va="top",
                    fontsize=8.5, color=palette["ink"])

        prob = s.get("probability")
        if prob is not None:
            right_edge = max(hi, ax.get_xlim()[1] if ax.get_xlim()[1] > 0 else 1)
            ax.text(right_edge, y + 0.15, f"p={prob:.0%}", va="bottom", ha="right",
                    fontsize=8, color=palette["muted"], fontstyle="italic")

    if price is not None:
        ax.axvline(price, color=palette["down"], linewidth=2.0, linestyle="--",
                   label=f"Price ${price:,.0f}")
        ax.legend(frameon=False, fontsize=9, loc="lower right")

    ax.set_yticks(ys)
    ax.set_yticklabels(names, fontsize=10, color=palette["ink"])
    ax.set_ylim(-0.6, len(scenarios) - 0.4)
    style_ax(ax, theme=theme,
             title="Scenario Analysis -- Value Ranges",
             xlabel="Value per share ($)")
    ax.grid(axis="y", visible=False)
    return save_fig(fig, out_dir, name, dpi=dpi)
