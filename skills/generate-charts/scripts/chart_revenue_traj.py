"""chart_revenue_traj.py -- Revenue and margin trajectory (NEW).

Dual-panel chart showing revenue bars + growth rate line (top panel) and
operating margin / FCFF margin over time (bottom panel), with historical
period shading and forecast start marker.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from .chart_utils import style_ax, save_fig, get_palette


def render(data, out_dir, *, name="revenue_traj", theme=None, lang="en-US"):
    palette = get_palette(theme)

    years = data["years"]
    revenue = data["revenue"]
    revenue_growth = data.get("revenue_growth", [])
    op_margin = data.get("op_margin", [])
    fcff_margin = data.get("fcff_margin", [])
    historical_revenue = data.get("historical_revenue", [])
    historical_margin = data.get("historical_margin", [])
    historical_years = data.get("historical_years", [])

    dpi = (theme or {}).get("figure", {}).get("dpi", 300)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7.0, 5.5), sharex=True)

    # Top panel: Revenue bars + growth rate line
    n_hist = len(historical_years)
    n_forecast = len(years)
    all_rev = list(historical_revenue) + list(revenue)
    all_years = list(historical_years) + list(years)
    x_all = np.arange(len(all_years))

    # Revenue bars (in billions)
    rev_billions = [r / 1000 for r in all_rev]
    bar_colors = [palette["accent"]] * n_hist + [palette["accent"]] * n_forecast
    bar_alphas = [0.5] * n_hist + [0.85] * n_forecast
    for i, (rv, c, a) in enumerate(zip(rev_billions, bar_colors, bar_alphas)):
        ax1.bar(i, rv, color=c, alpha=a, width=0.65)

    # Revenue growth rate line (right axis)
    if revenue_growth:
        # Historical growth (computed from revenue if not provided)
        hist_growth = []
        for i in range(1, n_hist):
            if historical_revenue[i - 1]:
                hist_growth.append((historical_revenue[i] / historical_revenue[i - 1]) - 1)
        if n_hist > 0:
            hist_growth.append(0)  # placeholder for first year
        growth_all = hist_growth + list(revenue_growth)
        growth_x = np.arange(len(growth_all))
        ax1r = ax1.twinx()
        ax1r.plot(growth_x, [g * 100 for g in growth_all],
                  color=palette["muted"], linewidth=1.2, linestyle="--",
                  marker=".", markersize=3, alpha=0.7,
                  label="Revenue growth (%, right axis)")
        ax1r.set_ylabel("Revenue growth (%)", color=palette["muted"], fontsize=8)
        ax1r.tick_params(colors=palette["muted"], labelsize=7)

    # Forecast start divider
    if n_hist > 0 and n_forecast > 0:
        ax1.axvline(n_hist - 0.5, color=palette["grid"], linewidth=1.0, linestyle="--")
        ax1.text(n_hist - 0.5, ax1.get_ylim()[1] * 0.98,
                 "Forecast start", ha="center", fontsize=7, color=palette["muted"],
                 va="top", rotation=90)

    ax1.set_ylabel("Revenue ($B)", color=palette["muted"], fontsize=9)
    ax1.tick_params(colors=palette["muted"], labelsize=8)

    # Bottom panel: Margin lines
    if historical_margin and historical_years:
        hx = np.arange(n_hist)
        ax2.plot(hx, historical_margin, color=palette["accent"], linewidth=1.4,
                 marker="o", markersize=3, alpha=0.6, label="Op. margin (historical)")
    fx = np.arange(n_hist, n_hist + n_forecast)
    if op_margin:
        ax2.plot(fx, op_margin, color=palette["accent"], linewidth=2.0,
                 marker="o", markersize=4, label="Operating margin")
    if fcff_margin:
        ax2.plot(fx, fcff_margin, color=palette["accent"], linewidth=1.6,
                 linestyle="--", marker="s", markersize=3,
                 label="FCFF margin")

    # Forecast start divider on bottom panel
    if n_hist > 0 and n_forecast > 0:
        ax2.axvline(n_hist - 0.5, color=palette["grid"], linewidth=1.0, linestyle="--")

    ax2.set_ylabel("Margin (%)", color=palette["muted"], fontsize=9)
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{y:.0%}"))
    ax2.legend(frameon=False, fontsize=7.5, loc="best")
    ax2.tick_params(colors=palette["muted"], labelsize=8)

    # X-axis labels
    all_labels = [str(y) for y in all_years]
    ax2.set_xticks(x_all)
    rotation = 45 if len(all_labels) > 8 else 0
    ax2.set_xticklabels(all_labels, fontsize=7, rotation=rotation,
                        color=palette["muted"], ha="right")

    # Dual-axis warning annotation
    if revenue_growth:
        ax1.text(0.01, 0.95,
                 "Note: Revenue ($B, left axis) and growth rate (%, right axis) use different scales.",
                 transform=ax1.transAxes, fontsize=6, color=palette["muted"],
                 va="top", ha="left", fontstyle="italic")

    # Style both axes
    for ax in (ax1, ax2):
        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)
        for spine in ("left", "bottom"):
            ax.spines[spine].set_color(palette["grid"])
            ax.spines[spine].set_linewidth(0.8)
        ax.grid(axis="both", color=palette["grid"], linewidth=0.6, alpha=0.5)
        ax.set_axisbelow(True)

    # Title on top panel
    cd = (theme or {}).get("chart_defaults", {})
    title_fs = cd.get("title_fontsize", 10)
    ax1.set_title("Revenue & Margin Trajectory",
                  color=palette["ink"], fontsize=title_fs,
                  fontweight="bold", loc="left", pad=10)

    fig.tight_layout()
    return save_fig(fig, out_dir, name, dpi=dpi)
