"""Research-report charts from the engine's JSON outputs.

Consumes the ``--json`` emitted by ``monte_carlo`` / ``breakeven`` / ``comps`` /
``dcf_valuation`` (plus small composed sheets for football-field & tornado) and
renders publication-style figures. It never recomputes a valuation -- it only
visualises numbers the engine already produced, so a chart can never disagree
with the report's arithmetic.

Clean-room implementation (no third-party chart code is vendored); the chart
*vocabulary* (football field, tornado, breakeven heatmap) follows standard
equity-research convention. Renders with the Agg backend so it runs headless/CI.

    python charts.py --kind montecarlo --in mc.json   --out figs/
    python charts.py --kind breakeven  --in be.json   --out figs/
    python charts.py --kind football   --in ff.json   --out figs/
    python charts.py --kind tornado    --in to.json   --out figs/
    python charts.py --kind terminal   --in dcf.json  --out figs/

JSON shapes:
  montecarlo : monte_carlo.py --json   (values, percentiles, price, mos_band)
  breakeven  : breakeven.py --json     (revenues, margins, grid, price)
  terminal   : dcf_valuation.py --json (terminal_pct_of_value)
  football   : {"price": P, "lenses": [{"label","low","high","mid"?}, ...]}
  tornado    : {"base": B, "drivers": [{"name","low","high"}, ...]}
"""

from __future__ import annotations

import argparse
import json
import os

import matplotlib
matplotlib.use("Agg")                       # headless: no display required
import matplotlib.pyplot as plt             # noqa: E402

# Restrained finance palette -- one accent, muted up/down, neutral surfaces.
PALETTE = {
    "ink": "#1f2a37",
    "muted": "#6b7280",
    "grid": "#e5e7eb",
    "accent": "#1d4ed8",      # value / base
    "up": "#15803d",          # cheap / undervalued
    "down": "#b91c1c",        # rich / overvalued
    "band": "#16a34a",        # margin-of-safety band fill
    "surface": "#f8fafc",
}
FIGSIZE = (9.0, 5.2)
DPI = 144


def _style(ax, title, xlabel=None, ylabel=None):
    ax.set_title(title, color=PALETTE["ink"], fontsize=13, fontweight="bold", loc="left", pad=12)
    if xlabel:
        ax.set_xlabel(xlabel, color=PALETTE["muted"], fontsize=10)
    if ylabel:
        ax.set_ylabel(ylabel, color=PALETTE["muted"], fontsize=10)
    ax.tick_params(colors=PALETTE["muted"], labelsize=9)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color(PALETTE["grid"])
    ax.grid(axis="both", color=PALETTE["grid"], linewidth=0.6, alpha=0.7)
    ax.set_axisbelow(True)


def _save(fig, out_dir, name):
    os.makedirs(out_dir, exist_ok=True)
    paths = []
    for ext in ("png", "svg"):
        p = os.path.join(out_dir, f"{name}.{ext}")
        fig.savefig(p, dpi=DPI, bbox_inches="tight", facecolor="white")
        paths.append(p)
    plt.close(fig)
    return paths


# --- chart kinds ---------------------------------------------------------------

def monte_carlo_hist(data, out_dir, name="montecarlo"):
    values = data["values"]
    band = data.get("mos_band", {})
    price = data.get("price")
    fig, ax = plt.subplots(figsize=FIGSIZE)
    ax.hist(values, bins=60, color=PALETTE["accent"], alpha=0.55, edgecolor="white", linewidth=0.3)

    if band:
        ax.axvspan(band["buy_below"], band["rich_above"], color=PALETTE["band"], alpha=0.10,
                   label=f"MoS buy-band ({band['mos']:.0%})")
        ax.axvline(band["buy_below"], color=PALETTE["up"], linewidth=1.4, linestyle="--",
                   label=f"Accumulate <= {band['buy_below']:.0f}")
        ax.axvline(band["median"], color=PALETTE["ink"], linewidth=1.6,
                   label=f"Fair (median) {band['median']:.0f}")
    if price is not None:
        pctl = data.get("price_percentile")
        lab = f"Price {price:.0f}" + (f"  ({pctl:.0%} pctile)" if pctl is not None else "")
        ax.axvline(price, color=PALETTE["down"], linewidth=2.0, label=lab)

    _style(ax, "Intrinsic value distribution (Monte Carlo)", "Value / share", "Trials")
    ax.legend(frameon=False, fontsize=8.5, loc="upper right")
    return _save(fig, out_dir, name)


def football_field(data, out_dir, name="football"):
    lenses = data["lenses"]
    price = data.get("price")
    labels = [l["label"] for l in lenses]
    ys = range(len(lenses))
    fig, ax = plt.subplots(figsize=FIGSIZE)
    for y, l in zip(ys, lenses):
        lo, hi = l["low"], l["high"]
        ax.plot([lo, hi], [y, y], color=PALETTE["accent"], linewidth=9, solid_capstyle="round", alpha=0.85)
        ax.text(lo, y, f"{lo:,.0f} ", va="center", ha="right", fontsize=8.5, color=PALETTE["muted"])
        ax.text(hi, y, f" {hi:,.0f}", va="center", ha="left", fontsize=8.5, color=PALETTE["muted"])
        if l.get("mid") is not None:
            ax.plot([l["mid"]], [y], marker="D", color=PALETTE["ink"], markersize=7, zorder=3)
    if price is not None:
        ax.axvline(price, color=PALETTE["down"], linewidth=2.0, label=f"Price {price:,.0f}")
        ax.legend(frameon=False, fontsize=9, loc="lower right")
    ax.set_yticks(list(ys))
    ax.set_yticklabels(labels, fontsize=9.5, color=PALETTE["ink"])
    ax.set_ylim(-0.6, len(lenses) - 0.4)
    _style(ax, "Valuation football field", "Value / share")
    ax.grid(axis="y", visible=False)
    return _save(fig, out_dir, name)


def breakeven_heatmap(data, out_dir, name="breakeven"):
    grid = data["grid"]
    revenues = data["revenues"]
    margins = data["margins"]
    price = data.get("price")
    fig, ax = plt.subplots(figsize=FIGSIZE)
    im = ax.imshow(grid, aspect="auto", origin="lower", cmap="RdYlGn")
    ax.set_xticks(range(len(margins)))
    ax.set_xticklabels([f"{m:.0%}" for m in margins])
    ax.set_yticks(range(len(revenues)))
    ax.set_yticklabels([f"{r/1000:,.0f}B" for r in revenues])
    for i, row in enumerate(grid):
        for j, v in enumerate(row):
            star = "*" if (price is not None and v >= price) else ""
            ax.text(j, i, f"{v:.0f}{star}", ha="center", va="center", fontsize=8,
                    color=PALETTE["ink"])
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.02)
    cbar.set_label("Value / share", color=PALETTE["muted"], fontsize=9)
    sub = f"  (* = reaches price {price:.0f})" if price is not None else ""
    _style(ax, "Breakeven: what has to be true" + sub, "Target operating margin", "Year-10 revenue")
    ax.grid(visible=False)
    return _save(fig, out_dir, name)


def sensitivity_tornado(data, out_dir, name="tornado"):
    base = data["base"]
    drivers = sorted(data["drivers"], key=lambda d: abs(d["high"] - d["low"]))
    names = [d["name"] for d in drivers]
    ys = range(len(drivers))
    fig, ax = plt.subplots(figsize=FIGSIZE)
    for y, d in zip(ys, drivers):
        lo, hi = sorted((d["low"], d["high"]))
        ax.barh(y, lo - base, left=base, color=PALETTE["down"], alpha=0.75)
        ax.barh(y, hi - base, left=base, color=PALETTE["up"], alpha=0.75)
    ax.axvline(base, color=PALETTE["ink"], linewidth=1.6, label=f"Base {base:,.0f}")
    ax.set_yticks(list(ys))
    ax.set_yticklabels(names, fontsize=9.5, color=PALETTE["ink"])
    ax.legend(frameon=False, fontsize=9, loc="lower right")
    _style(ax, "Sensitivity (tornado): value / share vs driver +/-1SD", "Value / share")
    ax.grid(axis="y", visible=False)
    return _save(fig, out_dir, name)


def terminal_share(data, out_dir, name="terminal"):
    term = data["terminal_pct_of_value"]
    explicit = max(0.0, 1.0 - term)
    fig, ax = plt.subplots(figsize=(5.6, 5.6))
    wedges, _ = ax.pie(
        [explicit, term],
        colors=[PALETTE["accent"], PALETTE["muted"]],
        startangle=90, counterclock=False,
        wedgeprops=dict(width=0.42, edgecolor="white"),
    )
    ax.text(0, 0, f"{term:.0%}\nin terminal", ha="center", va="center",
            fontsize=14, fontweight="bold", color=PALETTE["ink"])
    ax.legend(wedges, [f"Explicit FCFF  {explicit:.0%}", f"Terminal value  {term:.0%}"],
              frameon=False, fontsize=9.5, loc="lower center", bbox_to_anchor=(0.5, -0.08))
    ax.set_title("Where the value sits", color=PALETTE["ink"], fontsize=13,
                 fontweight="bold", loc="left", pad=12)
    return _save(fig, out_dir, name)


KINDS = {
    "montecarlo": monte_carlo_hist,
    "football": football_field,
    "breakeven": breakeven_heatmap,
    "tornado": sensitivity_tornado,
    "terminal": terminal_share,
}


def _main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Render research-report charts from engine JSON.")
    ap.add_argument("--kind", required=True, choices=sorted(KINDS))
    ap.add_argument("--in", dest="in_path", required=True, help="path to the source JSON")
    ap.add_argument("--out", default="figs", help="output directory (PNG + SVG)")
    ap.add_argument("--name", default=None, help="output file stem (defaults to --kind)")
    args = ap.parse_args(argv)
    with open(args.in_path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    fn = KINDS[args.kind]
    paths = fn(data, args.out, name=args.name or args.kind)
    print("wrote:")
    for p in paths:
        print(f"  {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
