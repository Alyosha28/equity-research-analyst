"""chart_capex_cycle.py -- CAPEX cycle chart (industry capacity vs demand)."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from .chart_utils import style_ax, save_fig, get_palette


def render(data, out_dir, *, name="capex_cycle", theme=None, lang="en-US"):
    palette = get_palette(theme)
    years = data["years"]
    demand = data.get("demand_growth_pct") or data.get("demand_growth", [])
    capacity = data.get("capacity_additions_pct") or data.get("capacity_additions", [])
    util = data.get("utilization_pct") or data.get("utilization_rate", [])
    industry = data.get("industry", "Industry")
    current_phase = data.get("current_cycle_phase", "")

    dpi = (theme or {}).get("figure", {}).get("dpi", 300)
    fig_w = (theme or {}).get("figure", {}).get("default_width", 7.0)
    fig_h = (theme or {}).get("figure", {}).get("default_height", 4.2)

    x = np.arange(len(years))
    fig, ax1 = plt.subplots(figsize=(fig_w, fig_h))

    ax1.plot(x, demand, color=palette["accent"], linewidth=2.0, marker="o",
             markersize=4, label="Demand growth (YoY %)")
    ax1.plot(x, capacity, color="#D97706", linewidth=1.8, marker="s", markersize=4,
             linestyle="--", label="Capacity additions (YoY %)")
    ax1.axhline(0, color=palette["grid"], linewidth=0.8, linestyle="-")
    ax1.set_ylabel("Growth rate (YoY %)", color=palette["muted"], fontsize=10)
    ax1.tick_params(colors=palette["muted"], labelsize=9)
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{y:.0f}%"))

    ax2 = ax1.twinx()
    ax2.fill_between(x, util, alpha=0.15, color=palette["accent"])
    ax2.plot(x, util, color=palette["accent"], linewidth=2.2, marker="D",
             markersize=4, label="Utilization rate")
    ax2.axhline(100, color=palette["ink"], linewidth=0.8, linestyle="--", alpha=0.4)
    ax2.axhline(85, color=palette["grid"], linewidth=0.6, linestyle=":", alpha=0.5)
    ax2.set_ylabel("Utilization rate (%)", color=palette["muted"], fontsize=10)
    ax2.tick_params(colors=palette["muted"], labelsize=9)
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{y:.0f}%"))

    phases = data.get("cycle_phase", [])
    phase_map = {p["year"]: p["phase"] for p in phases} if phases else {}
    demand_range = max(demand) - min(demand) if demand else 1
    for i, yr in enumerate(years):
        phase = phase_map.get(yr, "")
        if phase:
            ax1.annotate(phase, xy=(i, demand[i]),
                         xytext=(i, demand[i] + demand_range * 0.12),
                         fontsize=6.5, color=palette["muted"], ha="center",
                         va="bottom", fontstyle="italic",
                         arrowprops=dict(arrowstyle="->", color=palette["grid"],
                                         lw=0.5))

    if current_phase:
        phase_text = f"Current: {current_phase}"
        ax1.text(0.98, 0.95, phase_text, transform=ax1.transAxes, fontsize=9,
                 color=palette["ink"], ha="right", va="top",
                 bbox=dict(boxstyle="round,pad=0.3", facecolor=palette["surface"],
                           edgecolor=palette["grid"], alpha=0.9))

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, frameon=False, fontsize=8,
               loc="upper left")

    ax1.set_xticks(x)
    step = max(1, len(years) // 12)
    visible = [str(y) if i % step == 0 else "" for i, y in enumerate(years)]
    ax1.set_xticklabels(visible, fontsize=8, rotation=45, color=palette["muted"],
                        ha="right")
    ax1.set_title(f"Industry Capacity Cycle -- {industry}",
                  color=palette["ink"], fontsize=13, fontweight="bold",
                  loc="left", pad=12)
    for spine in ("top", "right"):
        ax1.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax1.spines[spine].set_color(palette["grid"])
    ax1.grid(axis="both", color=palette["grid"], linewidth=0.6, alpha=0.5)
    ax1.set_axisbelow(True)
    return save_fig(fig, out_dir, name, dpi=dpi)
