"""chart_price_vs_value.py -- Price vs intrinsic value history."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from .chart_utils import style_ax, save_fig, get_palette


def render(data, out_dir, *, name="price_vs_value", theme=None, lang="en-US"):
    palette = get_palette(theme)
    dates = data["dates"]
    price = data["price"]
    v_low = data["value_low"]
    v_mid = data["value_mid"]
    v_high = data["value_high"]
    events = data.get("events", [])

    dpi = (theme or {}).get("figure", {}).get("dpi", 300)
    fig_w = (theme or {}).get("figure", {}).get("default_width", 7.0)
    fig_h = (theme or {}).get("figure", {}).get("default_height", 4.2)

    x = np.arange(len(dates))
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))

    ax.fill_between(x, v_low, v_high, color=palette["band"], alpha=0.35,
                    label="Intrinsic value range")
    ax.plot(x, v_mid, color=palette["accent"], linewidth=1.8, linestyle="--",
            marker="o", markersize=4, label="Intrinsic value (mid)")
    ax.plot(x, price, color=palette["down"], linewidth=2.2, marker="s",
            markersize=4, label="Market price")

    date_to_idx = {d: i for i, d in enumerate(dates)}
    for ev in events:
        ev_date = ev.get("date", "")
        idx = date_to_idx.get(ev_date)
        if idx is None:
            for d in dates:
                if d.startswith(ev_date):
                    idx = date_to_idx[d]
                    break
        if idx is not None:
            impact = ev.get("impact", "neutral")
            ev_color = (palette["up"] if impact == "positive"
                        else palette["down"] if impact == "negative"
                        else palette["muted"])
            ax.axvline(idx, color=ev_color, linewidth=0.8, linestyle=":", alpha=0.7)
            y_top = max(max(price), max(v_high))
            ax.text(idx, y_top * 0.92, ev.get("label", ""), ha="center",
                    fontsize=6.5, color=palette["muted"], rotation=45, va="top")

    last_price = price[-1]
    last_mid = v_mid[-1]
    gap_pct = (last_mid - last_price) / last_price if last_price else 0
    direction = "discount" if gap_pct > 0 else "premium"
    gap_label = (f"Price ${last_price:,.0f} / "
                 f"Value ${last_mid:,.0f} = {gap_pct:+.0%} {direction}")
    ax.annotate(gap_label, xy=(x[-1], last_price),
                xytext=(x[-1] + 0.3, last_price),
                fontsize=7.5, color=palette["muted"], va="center",
                arrowprops=dict(arrowstyle="->", color=palette["muted"], lw=0.8))

    ax.set_xticks(x)
    step = max(1, len(dates) // 12)
    visible = [d if i % step == 0 else "" for i, d in enumerate(dates)]
    ax.set_xticklabels(visible, fontsize=8, rotation=45, color=palette["muted"],
                       ha="right")
    ax.legend(frameon=False, fontsize=8.5, loc="upper left")
    style_ax(ax, theme=theme,
             title="Price vs. Intrinsic Value -- Historical Gap Analysis",
             xlabel="Date", ylabel="Value / Price per share ($)")
    return save_fig(fig, out_dir, name, dpi=dpi)
