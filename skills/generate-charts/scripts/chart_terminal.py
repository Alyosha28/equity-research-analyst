"""chart_terminal.py -- Terminal value donut."""

from __future__ import annotations

import matplotlib.pyplot as plt
from .chart_utils import save_fig, get_palette


def render(data: dict, out_dir: str, *, name: str = "terminal",
           theme: dict | None = None, lang: str = "en-US") -> list[str]:
    """Render a terminal value donut chart from engine JSON data.

    Input schema:
        terminal_pct_of_value: float
        explicit_pct: float
        dcf_value: float
        terminal_value: float
        explicit_value: float
        growth_rate: float
        risk_free_rate: float

    Returns:
        List of output file paths [svg_path, png_path].
    """
    palette = get_palette(theme)
    cd = (theme or {}).get("chart_defaults", {})

    term = data["terminal_pct_of_value"]
    explicit = max(0.0, 1.0 - term)

    dpi = (theme or {}).get("figure", {}).get("dpi", 300)
    ink = palette["ink"]

    fig, ax = plt.subplots(figsize=(5.6, 5.6))
    wedges, _ = ax.pie(
        [explicit, term],
        colors=[palette["accent"], palette["muted"]],
        startangle=90, counterclock=False,
        wedgeprops=dict(width=0.42, edgecolor="white"),
    )
    ax.text(0, 0, f"{term:.0%}\nin terminal", ha="center", va="center",
            fontsize=14, fontweight="bold", color=ink)

    ax.legend(wedges,
              [f"Explicit FCFF  {explicit:.0%}",
               f"Terminal value  {term:.0%}"],
              frameon=False, fontsize=9.5, loc="lower center",
              bbox_to_anchor=(0.5, -0.08))

    title_fs = cd.get("title_fontsize", 10)
    ax.set_title("Where the value sits -- terminal value dependency",
                 color=ink, fontsize=title_fs, fontweight="bold",
                 loc="left", pad=12)

    return save_fig(fig, out_dir, name, dpi=dpi)
