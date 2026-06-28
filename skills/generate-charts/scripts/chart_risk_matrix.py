"""chart_risk_matrix.py -- Risk matrix scatter (probability vs value impact)."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from .chart_utils import style_ax, save_fig, get_palette


def render(data, out_dir, *, name="risk_matrix", theme=None, lang="en-US"):
    palette = get_palette(theme)
    risks = data["risks"]
    probs = [r["probability"] for r in risks]
    total_value = data.get("value") or data.get("intrinsic_value")
    impacts_abs = [r.get("impact_value_per_share",
                         r.get("impact_pct", 0)) for r in risks]
    if total_value and any(abs(v) > 1 for v in impacts_abs):
        impacts = [v / total_value for v in impacts_abs]
    else:
        impacts = impacts_abs

    categories = [r.get("category", "Other") for r in risks]
    names = [r.get("id", r.get("name", f"R{i}"))
             for i, r in enumerate(risks)]

    unique_cats = sorted(set(categories))
    cat_colors = {
        "Cycle": palette["down"],
        "Competition": "#D97706",
        "Technology": palette["accent"],
        "Demand": "#7C3AED",
        "Customer": palette["ink"],
        "Customer Concentration": palette["ink"],
        "Geopolitical": "#B45309",
        "Financial": palette["up"],
    }
    default_colors = [palette["accent"], palette["down"], palette["up"],
                      "#D97706", "#7C3AED", "#059669", palette["muted"]]
    for i, cat in enumerate(unique_cats):
        if cat not in cat_colors:
            cat_colors[cat] = default_colors[i % len(default_colors)]

    point_colors = [cat_colors.get(c, palette["muted"]) for c in categories]

    dpi = (theme or {}).get("figure", {}).get("dpi", 300)
    fig, ax = plt.subplots(figsize=(8.5, 7.0))

    med_prob = float(np.median(probs)) if probs else 0.5
    med_impact = float(np.median(impacts)) if impacts else 0.0

    ax.axhline(med_impact, color=palette["grid"], linewidth=1.0, linestyle="--")
    ax.axvline(med_prob, color=palette["grid"], linewidth=1.0, linestyle="--")

    ax.text(0.98, 0.98, "MITIGATE\n(high prob, high impact)",
            transform=ax.transAxes, ha="right", va="top", fontsize=8,
            color=palette["down"], fontweight="bold", alpha=0.7)
    ax.text(0.02, 0.98, "MONITOR\n(low prob, high impact)",
            transform=ax.transAxes, ha="left", va="top", fontsize=8,
            color=palette["ink"], fontweight="bold", alpha=0.7)
    ax.text(0.98, 0.02, "MANAGE\n(high prob, low impact)",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=8,
            color="#D97706", fontweight="bold", alpha=0.7)
    ax.text(0.02, 0.02, "ACCEPT\n(low prob, low impact)",
            transform=ax.transAxes, ha="left", va="bottom", fontsize=8,
            color=palette["muted"], fontweight="bold", alpha=0.7)

    impact_abs = [abs(imp) for imp in impacts]
    max_impact = max(impact_abs) if impact_abs else 1
    sizes = [max(60, abs(imp) / max(max_impact, 0.001) * 400) for imp in impacts]
    ax.scatter(probs, impacts, c=point_colors, s=sizes, alpha=0.75,
               edgecolors="white", linewidth=0.5, zorder=3)

    for i, risk_name in enumerate(names):
        y_offset = -12 if impacts[i] < med_impact else 10
        ax.annotate(risk_name, (probs[i], impacts[i]),
                    textcoords="offset points", xytext=(0, y_offset),
                    fontsize=7, ha="center", color=palette["ink"],
                    arrowprops=dict(arrowstyle="-", color=palette["grid"],
                                    lw=0.5))

    legend_handles = [plt.Line2D([0], [0], marker="o", color="w",
                                 markerfacecolor=cat_colors[cat],
                                 markersize=8, label=cat)
                      for cat in unique_cats]
    ax.legend(handles=legend_handles, frameon=False, fontsize=7.5,
              loc="lower right", title="Risk Category", title_fontsize=8)

    ax.set_xlabel("Estimated probability", color=palette["muted"], fontsize=10)
    if total_value:
        ax.set_ylabel("Value impact (% of intrinsic value)",
                      color=palette["muted"], fontsize=10)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{y:.0%}"))
    else:
        ax.set_ylabel("Value impact ($ / share)", color=palette["muted"],
                      fontsize=10)
    ax.set_xlim(-0.02, max(probs) * 1.08 if probs else 1.0)
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:.0%}"))
    ax.tick_params(colors=palette["muted"], labelsize=9)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color(palette["grid"])
    ax.grid(axis="both", color=palette["grid"], linewidth=0.6, alpha=0.5)
    ax.set_axisbelow(True)
    ax.set_title("Risk Matrix -- Probability vs. Value Impact",
                 color=palette["ink"], fontsize=13, fontweight="bold",
                 loc="left", pad=12)
    return save_fig(fig, out_dir, name, dpi=dpi)
