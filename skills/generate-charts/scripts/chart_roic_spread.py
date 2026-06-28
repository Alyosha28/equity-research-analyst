"""chart_roic_spread.py -- ROIC-WACC spread over time (durability assessment)."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from .chart_utils import style_ax, save_fig, get_palette


def render(data, out_dir, *, name="roic_spread", theme=None, lang="en-US"):
    palette = get_palette(theme)
    years = data.get("years", list(range(1, 11)))
    roic = data["roic"] if isinstance(data["roic"], list) else [data["roic"]] * len(years)
    wacc = data["wacc"] if isinstance(data["wacc"], list) else [data["wacc"]] * len(years)
    spread = data.get("spread")
    if spread is None:
        spread = [r - w for r, w in zip(roic, wacc)]
    elif not isinstance(spread, list):
        spread = [spread] * len(years)
    cap = data.get("competitive_advantage_period", len(years))

    n = min(len(years), len(roic), len(wacc), len(spread))
    years = years[:n]
    roic = roic[:n]
    wacc = wacc[:n]
    spread = spread[:n]

    dpi = (theme or {}).get("figure", {}).get("dpi", 300)
    fig_w = (theme or {}).get("figure", {}).get("default_width", 7.0)
    fig_h = (theme or {}).get("figure", {}).get("default_height", 4.2)

    x = np.arange(n)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))

    ax.plot(x, roic, color=palette["accent"], linewidth=2.0, marker="o", markersize=4,
            label="ROIC")
    ax.plot(x, wacc, color=palette["muted"], linewidth=1.6, linestyle="--",
            label="WACC")

    for i in range(n - 1):
        if roic[i] >= wacc[i] and roic[i + 1] >= wacc[i + 1]:
            fill_color = palette["up"]
            fill_alpha = 0.10
        elif roic[i] < wacc[i] and roic[i + 1] < wacc[i + 1]:
            fill_color = palette["down"]
            fill_alpha = 0.10
        else:
            fill_color = palette["grid"]
            fill_alpha = 0.15
        ax.fill_between(x[i:i + 2], roic[i:i + 2], wacc[i:i + 2],
                        color=fill_color, alpha=fill_alpha)

    cap_idx = min(cap, n - 1)
    if cap_idx > 0 and cap_idx < n:
        y_max = max(max(roic), max(wacc))
        ax.axvline(cap_idx - 0.5, color=palette["muted"], linewidth=1.2, linestyle=":")
        ax.text(cap_idx - 0.5, y_max * 0.95, f"CAP = {cap}y",
                ha="center", fontsize=8.5, color=palette["muted"], va="top")

    hist_roic = data.get("historical_roic")
    hist_years = data.get("historical_years")
    all_labels = [str(y) for y in years]
    all_positions = list(x)
    if hist_roic and hist_years:
        hx = np.arange(-len(hist_roic), 0)
        ax.plot(hx, hist_roic, color=palette["accent"], linewidth=1.5, linestyle=":",
                marker="s", markersize=3, alpha=0.6, label="Historical ROIC")
        ax.axvline(-0.5, color=palette["grid"], linewidth=1.0, linestyle="--")
        all_labels = [str(y) for y in hist_years] + all_labels
        all_positions = list(hx) + list(x)

    ax.set_xticks(all_positions)
    rotation = 45 if len(all_labels) > 8 else 0
    ax.set_xticklabels(all_labels, fontsize=8, rotation=rotation, color=palette["muted"])
    ax.legend(frameon=False, fontsize=9, loc="upper right")
    style_ax(ax, theme=theme,
             title="ROIC-WACC Spread -- Durability Assessment",
             xlabel="Year", ylabel="Return / Cost of capital")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{y:.0%}"))
    return save_fig(fig, out_dir, name, dpi=dpi)
