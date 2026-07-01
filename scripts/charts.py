"""Research-report charts from the engine's JSON outputs.

Consumes the ``--json`` emitted by ``monte_carlo`` / ``breakeven`` / ``comps`` /
``dcf_valuation`` (plus small composed sheets for football-field & tornado) and
renders publication-style figures. It never recomputes a valuation -- it only
visualises numbers the engine already produced, so a chart can never disagree
with the report's arithmetic.

Clean-room implementation (no third-party chart code is vendored); the chart
*vocabulary* (football field, tornado, breakeven heatmap) follows standard
equity-research convention. Renders with the Agg backend so it runs headless/CI.

    python charts.py --kind montecarlo --in mc.json   --out figs/ --ticker NVDA
    python charts.py --kind breakeven  --in be.json   --out figs/ --ticker NVDA
    python charts.py --kind football   --in ff.json   --out figs/ --ticker NVDA
    python charts.py --kind tornado    --in to.json   --out figs/ --ticker NVDA
    python charts.py --kind terminal   --in dcf.json  --out figs/ --ticker NVDA

Output files: figs/NVDA_montecarlo.png, figs/NVDA_montecarlo.svg, etc.
Canonical chart reference format: figs/{TICKER}_{kind}.{ext}

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
from statistics import mean

import matplotlib
matplotlib.use("Agg")                       # headless: no display required

# CJK font configuration - detect and prepend CJK-capable font
import matplotlib as _mpl
import matplotlib.font_manager as _fm
import matplotlib.text as _mtext
_cjk_font_files = [
    r"C:\Windows\Fonts\NotoSansSC-VF.ttf",
    r"C:\Windows\Fonts\Noto Sans SC (TrueType).otf",
    r"C:\Windows\Fonts\msyh.ttc",
    r"C:\Windows\Fonts\simhei.ttf",
    r"C:\Windows\Fonts\simsun.ttc",
]
_cjk_font_prop = None
for _font_path in _cjk_font_files:
    if os.path.exists(_font_path):
        _fm.fontManager.addfont(_font_path)
        _cjk_font_prop = _fm.FontProperties(fname=_font_path)
        _mpl.rcParams['font.family'] = 'sans-serif'
        _mpl.rcParams['font.sans-serif'] = [_cjk_font_prop.get_name()] + _mpl.rcParams['font.sans-serif']
        break
_cjk_opts = ['Noto Sans SC', 'Microsoft YaHei', 'SimHei', 'PingFang SC', 'Noto Sans CJK SC', 'WenQuanYi Micro Hei']
_avail = {f.name for f in _fm.fontManager.ttflist}
_cjk_found = next((f for f in _cjk_opts if f in _avail), None)
if _cjk_font_prop is None and _cjk_found:
    _mpl.rcParams['font.sans-serif'] = [_cjk_found] + _mpl.rcParams['font.sans-serif']
    _mpl.rcParams['font.family'] = 'sans-serif'

import matplotlib.pyplot as plt             # noqa: E402
import numpy as np                           # noqa: E402

# ── Palette: sourced from design_tokens.json (single source of truth) ──
# This replaces the previously hardcoded PALETTE. The design_tokens.json file
# is the shared visual-identity authority consumed by both charts (Python) and
# PDF (CSS via build_css_vars.py). Keep this block self-contained so charts.py
# remains runnable even if theme.py is unavailable.
def _load_palette():
    """Load colour palette from design_tokens.json; fall back to hardcoded defaults."""
    _tokens_path = os.path.join(os.path.dirname(__file__), "design_tokens.json")
    _defaults = {
        "ink": "#1A1A1A", "muted": "#6B7280", "grid": "#D1D5DB",
        "accent": "#002D72", "up": "#0E6E4D", "down": "#CC0000",
        "band": "#F3F4F6", "surface": "#FFFFFF",
    }
    try:
        with open(_tokens_path, "r", encoding="utf-8") as _fh:
            _tokens = json.load(_fh)
        _colors = _tokens.get("colors", {})
        return {k: _colors.get(k, _defaults[k]) for k in _defaults}
    except Exception:
        return dict(_defaults)

PALETTE = _load_palette()
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
    if _cjk_font_prop is not None:
        for text in fig.findobj(match=_mtext.Text):
            size = text.get_fontsize()
            weight = text.get_fontweight()
            style = text.get_fontstyle()
            text.set_fontproperties(_cjk_font_prop)
            text.set_fontsize(size)
            text.set_fontweight(weight)
            text.set_fontstyle(style)
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
                   label=f"安全边际买入带（{band['mos']:.0%}）")
        ax.axvline(band["buy_below"], color=PALETTE["up"], linewidth=1.4, linestyle="--",
                   label=f"加仓 <= {band['buy_below']:.0f}")
        ax.axvline(band["median"], color=PALETTE["ink"], linewidth=1.6,
                   label=f"公允中位数 {band['median']:.0f}")
    if price is not None:
        pctl = data.get("price_percentile")
        lab = f"当前价格 {price:.0f}" + (f"（{pctl:.0%} 分位）" if pctl is not None else "")
        ax.axvline(price, color=PALETTE["down"], linewidth=2.0, label=lab)

    _style(ax, "内在价值分布（蒙特卡洛）", "每股价值", "模拟次数")
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
        ax.axvline(price, color=PALETTE["down"], linewidth=2.0, label=f"当前价格 {price:,.0f}")
        ax.legend(frameon=False, fontsize=9, loc="lower right")
    ax.set_yticks(list(ys))
    ax.set_yticklabels(labels, fontsize=9.5, color=PALETTE["ink"])
    ax.set_ylim(-0.6, len(lenses) - 0.4)
    _style(ax, "估值区间图", "每股价值")
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
    ax.set_yticklabels([f"{r/100:,.0f}亿" for r in revenues])
    for i, row in enumerate(grid):
        for j, v in enumerate(row):
            star = "*" if (price is not None and v >= price) else ""
            ax.text(j, i, f"{v:.0f}{star}", ha="center", va="center", fontsize=8,
                    color=PALETTE["ink"])
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.02)
    cbar.set_label("每股价值", color=PALETTE["muted"], fontsize=9)
    sub = f"（* 表示达到当前价格 {price:.0f}）" if price is not None else ""
    _style(ax, "盈亏平衡：需要兑现什么" + sub, "目标经营利润率", "第 10 年收入（亿元）")
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
    ax.axvline(base, color=PALETTE["ink"], linewidth=1.6, label=f"基准 {base:,.0f}")
    ax.set_yticks(list(ys))
    ax.set_yticklabels(names, fontsize=9.5, color=PALETTE["ink"])
    ax.legend(frameon=False, fontsize=9, loc="lower right")
    _style(ax, "敏感性分析（龙卷风）：每股价值对关键驱动的 +/-1SD 变化", "每股价值")
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
    ax.text(0, 0, f"{term:.0%}\n来自终值", ha="center", va="center",
            fontsize=14, fontweight="bold", color=PALETTE["ink"])
    ax.legend(wedges, [f"显性期 FCFF  {explicit:.0%}", f"终值  {term:.0%}"],
              frameon=False, fontsize=9.5, loc="lower center", bbox_to_anchor=(0.5, -0.08))
    ax.set_title("价值构成", color=PALETTE["ink"], fontsize=13,
                 fontweight="bold", loc="left", pad=12)
    return _save(fig, out_dir, name)


# --- NEW chart kinds (7 additions; 12 total matching SKILL.md catalog) ------------


def revenue_traj_chart(data, out_dir, name="revenue_traj"):
    """Revenue & margin trajectory — dual-panel with bars, lines, and historical context.

    Input shape (from dcf_valuation.py or OUTPUT_SLOTS):
        years, revenue, revenue_growth, op_margin, fcff_margin,
        historical_revenue, historical_margin, historical_years

    Renders per SKILL.md chart #6 spec:
        Top panel:  Revenue bars ($B) + growth rate line (%, right axis)
        Bottom panel: Operating margin (solid) + FCFF margin (dashed)
        Historical period shaded with lighter alpha; vertical divider at forecast start.
    """
    years = data["years"]
    revenue = data["revenue"]
    rev_growth = data.get("revenue_growth", [])
    op_margin = data.get("op_margin", [])
    fcff_margin = data.get("fcff_margin", [])
    hist_rev = data.get("historical_revenue", [])
    hist_margin = data.get("historical_margin", [])
    hist_years = data.get("historical_years", [])

    n_fcst = len(years)
    n_hist = len(hist_years)

    # Combined x-axis positions: historical first, then forecast
    hist_x = list(range(n_hist))
    fcst_x = list(range(n_hist, n_hist + n_fcst))
    all_labels = [str(y) for y in (hist_years + years)]
    all_ticks = hist_x + fcst_x

    # accent_light for secondary series — PALETTE may lack it; fall back to SKILL.md value
    accent_lite = PALETTE.get("accent_light", "#4A7AB5")

    # Dual-panel figure per spec: 2 rows × 1 col, shared x-axis, figsize=(7, 5.5)
    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(7.0, 5.5), sharex=True,
        gridspec_kw={'height_ratios': [1.1, 1], 'hspace': 0.06},
    )

    # ── TOP PANEL: Revenue bars + growth rate line ──
    # Forecast revenue bars ($B)
    rev_billions = [r / 1000 for r in revenue]
    ax1.bar(fcst_x, rev_billions, color=PALETTE["accent"], alpha=0.85,
            label="收入（预测）", zorder=2)

    # Historical revenue bars (shaded / lower alpha)
    if n_hist and hist_rev:
        hist_billions = [r / 1000 for r in hist_rev]
        ax1.bar(hist_x, hist_billions, color=PALETTE["band"], alpha=0.70,
                edgecolor=PALETTE["grid"], linewidth=0.5,
                label="收入（历史）", zorder=2)

    # Revenue growth rate line on right y-axis
    ax1b = ax1.twinx()
    if rev_growth:
        growth_pct = [g * 100 for g in rev_growth]
        ax1b.plot(fcst_x, growth_pct, color=PALETTE["muted"], linewidth=1.5,
                  linestyle="--", marker="s", markersize=3,
                  label="收入增速（同比 %）", zorder=3)
        ax1b.set_ylabel("增速（%）", color=PALETTE["muted"], fontsize=8)
        ax1b.tick_params(colors=PALETTE["muted"], labelsize=7)

    # Forecast-start vertical divider + zone labels
    if n_hist:
        ax1.axvline(n_hist - 0.5, color=PALETTE["grid"], linewidth=1.2,
                    linestyle="--", alpha=0.8, zorder=1)
        # Compute label positions at 60% of the way up whichever range is taller
        all_rev_vals = ([r / 1000 for r in hist_rev] if n_hist else []) + rev_billions
        y_ref = max(all_rev_vals) * 1.08 if all_rev_vals else 1
        mid_hist = (n_hist - 1) / 2 if n_hist > 1 else 0
        mid_fcst = n_hist + (n_fcst - 1) / 2 if n_fcst > 1 else n_hist
        ax1.text(mid_hist, y_ref, "历史区间", ha="center",
                 fontsize=6.5, color=PALETTE["muted"], fontstyle="italic", va="bottom")
        ax1.text(mid_fcst, y_ref, "预测区间", ha="center",
                 fontsize=6.5, color=PALETTE["muted"], fontstyle="italic", va="bottom")

    ax1.set_ylabel("收入（十亿）", color=PALETTE["muted"], fontsize=9)
    ax1.tick_params(colors=PALETTE["muted"], labelsize=7)

    # Dual-axis warning (per spec)
    ax1.text(0.01, 0.96,
             "注：收入（左轴）与增速（右轴）使用不同刻度。",
             transform=ax1.transAxes, fontsize=5.5, color=PALETTE["muted"],
             fontstyle="italic", va="top")

    # Combine legends from both left and right axes
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines1b, labels1b = ax1b.get_legend_handles_labels() if rev_growth else ([], [])
    ax1.legend(lines1 + lines1b, labels1 + labels1b, frameon=False,
               fontsize=7.5, loc="upper left")

    # ── BOTTOM PANEL: Margin lines ──
    # Historical operating margin
    if n_hist and hist_margin:
        ax2.plot(hist_x, [m * 100 for m in hist_margin], color=PALETTE["accent"],
                 linewidth=1.5, linestyle=":", marker="o", markersize=4,
                  alpha=0.6, label="经营利润率（历史）")

    # Forecast operating margin (solid)
    if op_margin:
        ax2.plot(fcst_x, [m * 100 for m in op_margin], color=PALETTE["accent"],
                 linewidth=2.0, marker="o", markersize=4,
                  label="经营利润率")

    # Forecast FCFF margin (dashed, lighter navy)
    if fcff_margin:
        ax2.plot(fcst_x, [m * 100 for m in fcff_margin], color=accent_lite,
                 linewidth=1.8, linestyle="--", marker="s", markersize=3,
                  label="FCFF 利润率")

    # Forecast-start divider
    if n_hist:
        ax2.axvline(n_hist - 0.5, color=PALETTE["grid"], linewidth=1.2,
                    linestyle="--", alpha=0.8, zorder=1)

    ax2.set_ylabel("利润率（%）", color=PALETTE["muted"], fontsize=9)
    ax2.tick_params(colors=PALETTE["muted"], labelsize=7)
    ax2.legend(frameon=False, fontsize=7.5, loc="upper right")

    # Combined x-axis tick labels on the bottom panel
    ax2.set_xticks(all_ticks)
    rotation = 45 if len(all_labels) > 8 else 0
    ax2.set_xticklabels(all_labels, fontsize=7, rotation=rotation,
                        color=PALETTE["muted"],
                        ha="right" if rotation else "center")

    # Shared styling for both panels
    for ax in (ax1, ax2):
        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)
        for spine in ("left", "bottom"):
            ax.spines[spine].set_color(PALETTE["grid"])
        ax.grid(axis="both", color=PALETTE["grid"], linewidth=0.6, alpha=0.5)
        ax.set_axisbelow(True)

    # Overall figure title (left-aligned per chart catalog discipline)
    fig.suptitle("收入与利润率路径",
                 color=PALETTE["ink"], fontsize=13, fontweight="bold",
                 x=0.02, ha="left", y=0.97)

    return _save(fig, out_dir, name)


def roic_spread_chart(data, out_dir, name="roic_spread"):
    """ROIC-WACC spread over time -- durability assessment.

    Input shape (from durability-check or OUTPUT_SLOTS):
        years, roic (list or scalar), wacc (list or scalar),
        spread (list or scalar), competitive_advantage_period (int),
        optional: historical_roic, historical_years
    """
    years = data.get("years", list(range(1, 11)))
    roic = data["roic"] if isinstance(data["roic"], list) else [data["roic"]] * len(years)
    wacc = data["wacc"] if isinstance(data["wacc"], list) else [data["wacc"]] * len(years)
    spread = data.get("spread")
    if spread is None:
        spread = [r - w for r, w in zip(roic, wacc)]
    elif not isinstance(spread, list):
        spread = [spread] * len(years)
    cap = data.get("competitive_advantage_period", len(years))

    # Truncate lists to shortest common length
    n = min(len(years), len(roic), len(wacc), len(spread))
    years = years[:n]
    roic = roic[:n]
    wacc = wacc[:n]
    spread = spread[:n]

    x = np.arange(n)
    fig, ax = plt.subplots(figsize=FIGSIZE)

    ax.plot(x, roic, color=PALETTE["accent"], linewidth=2.0, marker="o", markersize=4,
            label="ROIC")
    ax.plot(x, wacc, color=PALETTE["muted"], linewidth=1.6, linestyle="--",
            label="WACC")

    # Fill spread area: green when ROIC > WACC, red when ROIC < WACC
    for i in range(n - 1):
        if roic[i] >= wacc[i] and roic[i + 1] >= wacc[i + 1]:
            fill_color = PALETTE["up"]
            fill_alpha = 0.10
        elif roic[i] < wacc[i] and roic[i + 1] < wacc[i + 1]:
            fill_color = PALETTE["down"]
            fill_alpha = 0.10
        else:
            fill_color = PALETTE["grid"]
            fill_alpha = 0.15
        ax.fill_between(x[i:i + 2], roic[i:i + 2], wacc[i:i + 2],
                        color=fill_color, alpha=fill_alpha)

    # Competitive advantage period marker
    cap_idx = min(cap, n - 1)
    if cap_idx > 0 and cap_idx < n:
        y_max = max(max(roic), max(wacc))
        ax.axvline(cap_idx - 0.5, color=PALETTE["muted"], linewidth=1.2, linestyle=":")
        ax.text(cap_idx - 0.5, y_max * 0.95, f"竞争优势期 = {cap}年",
                ha="center", fontsize=8.5, color=PALETTE["muted"], va="top")

    # Historical data if present
    hist_roic = data.get("historical_roic")
    hist_years = data.get("historical_years")
    all_labels = [str(y) for y in years]
    all_positions = list(x)
    if hist_roic and hist_years:
        hx = np.arange(-len(hist_roic), 0)
        ax.plot(hx, hist_roic, color=PALETTE["accent"], linewidth=1.5, linestyle=":",
                marker="s", markersize=3, alpha=0.6, label="历史 ROIC")
        ax.axvline(-0.5, color=PALETTE["grid"], linewidth=1.0, linestyle="--")
        all_labels = [str(y) for y in hist_years] + all_labels
        all_positions = list(hx) + list(x)

    ax.set_xticks(all_positions)
    rotation = 45 if len(all_labels) > 8 else 0
    ax.set_xticklabels(all_labels, fontsize=8, rotation=rotation,
                       color=PALETTE["muted"])
    ax.legend(frameon=False, fontsize=9, loc="upper right")
    _style(ax, "ROIC-WACC 利差：耐久性评估",
           "年份", "回报率 / 资本成本")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{y:.0%}"))
    return _save(fig, out_dir, name)


def scenarios_chart(data, out_dir, name="scenarios"):
    """Scenario comparison -- bull / base / bear value ranges.

    Input shape (from build_scenarios.py or /build-assumptions):
        scenarios: list of {name, probability, value_per_share, key_drivers, ...}
        Optional: price, value_low, value_high (for range bars)
    """
    scenarios = data["scenarios"]
    price = data.get("price")
    names = [s["name"] for s in scenarios]
    ys = list(range(len(scenarios)))
    fig, ax = plt.subplots(figsize=FIGSIZE)

    for y, s in zip(ys, scenarios):
        v = s.get("value_per_share")
        if v is not None:
            lo = s.get("value_low", v)
            hi = s.get("value_high", v)
        else:
            lo = s.get("value_low", 0)
            hi = s.get("value_high", 0)

        color = PALETTE["accent"]
        if "bear" in s["name"].lower():
            color = PALETTE["down"]
        elif "bull" in s["name"].lower():
            color = PALETTE["up"]

        if lo != hi:
            ax.plot([lo, hi], [y, y], color=color, linewidth=10,
                    solid_capstyle="round", alpha=0.80)
            ax.text(lo, y, f"{lo:,.0f} ", va="center", ha="right", fontsize=8.5,
                    color=PALETTE["muted"])
            ax.text(hi, y, f" {hi:,.0f}", va="center", ha="left", fontsize=8.5,
                    color=PALETTE["muted"])

        # Midpoint diamond
        mid = s.get("value_mid")
        if mid is None:
            mid = (lo + hi) / 2 if lo != hi else v
        if mid:
            ax.plot([mid], [y], marker="D", color=PALETTE["ink"], markersize=8,
                    zorder=3)
            ax.text(mid, y - 0.35, f"{mid:,.0f}", ha="center", va="top",
                    fontsize=8.5, color=PALETTE["ink"])

        # Probability badge
        prob = s.get("probability")
        if prob is not None:
            right_edge = max(hi, ax.get_xlim()[1] if ax.get_xlim()[1] > 0 else 1)
            ax.text(right_edge, y + 0.15, f"p={prob:.0%}", va="bottom", ha="right",
                    fontsize=8, color=PALETTE["muted"], fontstyle="italic")

    if price is not None:
        ax.axvline(price, color=PALETTE["down"], linewidth=2.0, linestyle="--",
                   label=f"当前价格 {price:,.0f}")
        ax.legend(frameon=False, fontsize=9, loc="lower right")

    ax.set_yticks(ys)
    ax.set_yticklabels(names, fontsize=10, color=PALETTE["ink"])
    ax.set_ylim(-0.6, len(scenarios) - 0.4)
    _style(ax, "情景分析：每股价值区间", "每股价值")
    ax.grid(axis="y", visible=False)
    return _save(fig, out_dir, name)


def price_vs_value_chart(data, out_dir, name="price_vs_value"):
    """Price vs intrinsic value over time -- historical gap analysis.

    Input shape (from build_history.py or /analyze-company):
        dates, price, value_low, value_mid, value_high (all lists)
        Optional: events list of {date, label, impact}
    """
    dates = data["dates"]
    price = data["price"]
    v_low = data["value_low"]
    v_mid = data["value_mid"]
    v_high = data["value_high"]
    events = data.get("events", [])

    x = np.arange(len(dates))
    fig, ax = plt.subplots(figsize=FIGSIZE)

    # Value band (shaded area)
    ax.fill_between(x, v_low, v_high, color=PALETTE["band"], alpha=0.35,
                    label="内在价值区间")
    # Value mid line
    ax.plot(x, v_mid, color=PALETTE["accent"], linewidth=1.8, linestyle="--",
            marker="o", markersize=4, label="内在价值（中枢）")
    # Price line
    ax.plot(x, price, color=PALETTE["down"], linewidth=2.2, marker="s", markersize=4,
            label="市场价格")

    # Event markers
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
            ev_color = (PALETTE["up"] if impact == "positive"
                        else PALETTE["down"] if impact == "negative"
                        else PALETTE["muted"])
            ax.axvline(idx, color=ev_color, linewidth=0.8, linestyle=":", alpha=0.7)
            y_top = max(max(price), max(v_high))
            ax.text(idx, y_top * 0.92, ev.get("label", ""), ha="center",
                    fontsize=6.5, color=PALETTE["muted"], rotation=45, va="top")

    # Gap annotation at rightmost point
    last_price = price[-1]
    last_mid = v_mid[-1]
    gap_pct = (last_mid - last_price) / last_price if last_price else 0
    direction = "折价" if gap_pct > 0 else "溢价"
    gap_label = (f"价格 {last_price:,.0f} / "
                 f"价值 {last_mid:,.0f} = {gap_pct:+.0%} {direction}")
    ax.annotate(gap_label, xy=(x[-1], last_price),
                xytext=(x[-1] + 0.3, last_price),
                fontsize=7.5, color=PALETTE["muted"], va="center",
                arrowprops=dict(arrowstyle="->", color=PALETTE["muted"], lw=0.8))

    ax.set_xticks(x)
    step = max(1, len(dates) // 12)
    visible = [d if i % step == 0 else "" for i, d in enumerate(dates)]
    ax.set_xticklabels(visible, fontsize=8, rotation=45, color=PALETTE["muted"],
                       ha="right")
    ax.legend(frameon=False, fontsize=8.5, loc="upper left")
    _style(ax, "价格与内在价值：历史差距分析",
           "日期", "每股价值 / 价格")
    return _save(fig, out_dir, name)


def waterfall_chart(data, out_dir, name="waterfall"):
    """Driver waterfall bridge -- from intrinsic base value to market price.

    Input shape (from build_waterfall.py or /triangulate):
        base_value or intrinsic_value (float),
        price (float),
        steps: list of {label, value (cumulative), delta, is_positive/direction}
    """
    steps = data["steps"]
    price = data.get("price")
    base_value = data.get("base_value") or data.get("intrinsic_value")

    n = len(steps)
    bar_width = 0.6
    x = np.arange(n)
    fig_width = max(9, n * 1.15)
    fig, ax = plt.subplots(figsize=(fig_width, 5.2))

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
            color = PALETTE["accent"]
            running = height
        elif i == n - 1:
            bottom = 0
            height = val if val else running
            color = PALETTE["accent"]
            running = height
        else:
            if is_pos:
                bottom = running
                height = abs(delta)
                running += height
                color = PALETTE["up"]
            else:
                running += delta
                bottom = running
                height = abs(delta)
                color = PALETTE["down"]

        bottoms.append(bottom)
        heights.append(height)
        colors.append(color)
        labels_text.append(s.get("label", ""))

    bars = ax.bar(x, heights, bar_width, bottom=bottoms, color=colors,
                  edgecolor="white", linewidth=0.5)

    # Value labels above each bar
    for i in range(n):
        label_val = steps[i].get("value", running)
        max_h = max(heights) if heights else 1
        offset = max_h * 0.02
        ax.text(i, bottoms[i] + heights[i] + offset, f"{label_val:,.0f}",
                ha="center", va="bottom", fontsize=8.5, color=PALETTE["ink"],
                fontweight="bold")

    # Connector lines between bar tops
    for i in range(n - 1):
        top_i = bottoms[i] + heights[i]
        top_j = bottoms[i + 1] + heights[i + 1]
        ax.plot([i + bar_width / 2, i + 1 - bar_width / 2], [top_i, top_j],
                color=PALETTE["grid"], linewidth=0.8, linestyle="-", zorder=0)

    ax.set_xticks(x)
    wrapped_labels = [l.replace(" ", "\n") if len(l) > 20 else l for l in labels_text]
    ax.set_xticklabels(wrapped_labels, fontsize=7.5, color=PALETTE["ink"],
                       rotation=0, ha="center")

    if price is not None:
        ax.axhline(price, color=PALETTE["down"], linewidth=1.2, linestyle="--",
                   alpha=0.6, label=f"市场价格 {price:,.0f}")
        ax.legend(frameon=False, fontsize=8.5, loc="upper right")

    if base_value and price:
        gap = price - base_value
        chart_title = (f"价值桥：从 {base_value:,.0f} 到 "
                       f"{price:,.0f}（差距：{gap:+,.0f}）")
        ax.set_title(chart_title, color=PALETTE["ink"], fontsize=13,
                     fontweight="bold", loc="left", pad=12)
    else:
        _style(ax, "价值桥：驱动因素贡献", ylabel="每股价值")
        return _save(fig, out_dir, name)

    ax.set_ylabel("每股价值", color=PALETTE["muted"], fontsize=10)
    ax.tick_params(colors=PALETTE["muted"], labelsize=9)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color(PALETTE["grid"])
    ax.grid(axis="y", color=PALETTE["grid"], linewidth=0.6, alpha=0.7)
    ax.set_axisbelow(True)
    return _save(fig, out_dir, name)


def capex_cycle_chart(data, out_dir, name="capex_cycle"):
    """Industry capacity cycle -- demand growth vs capacity additions with utilization.

    Input shape (from build_capex.py or /analyze-industry):
        years, demand_growth_pct (or demand_growth),
        capacity_additions_pct (or capacity_additions),
        utilization_pct (or utilization_rate),
        cycle_phase list, current_cycle_phase, industry, producers list
    """
    years = data["years"]
    demand = data.get("demand_growth_pct") or data.get("demand_growth", [])
    capacity = data.get("capacity_additions_pct") or data.get("capacity_additions", [])
    util = data.get("utilization_pct") or data.get("utilization_rate", [])
    industry = data.get("industry", "Industry")
    current_phase = data.get("current_cycle_phase", "")

    x = np.arange(len(years))
    fig, ax1 = plt.subplots(figsize=FIGSIZE)

    # Left axis: demand growth and capacity additions
    ax1.plot(x, demand, color=PALETTE["accent"], linewidth=2.0, marker="o",
             markersize=4, label="需求增长（同比 %）")
    ax1.plot(x, capacity, color="#D97706", linewidth=1.8, marker="s", markersize=4,
             linestyle="--", label="产能新增（同比 %）")
    ax1.axhline(0, color=PALETTE["grid"], linewidth=0.8, linestyle="-")
    ax1.set_ylabel("同比增速（%）", color=PALETTE["muted"], fontsize=10)
    ax1.tick_params(colors=PALETTE["muted"], labelsize=9)
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{y:.0f}%"))

    # Right axis: utilization rate
    ax2 = ax1.twinx()
    ax2.fill_between(x, util, alpha=0.15, color=PALETTE["accent"])
    ax2.plot(x, util, color=PALETTE["accent"], linewidth=2.2, marker="D",
             markersize=4, label="产能利用率")
    ax2.axhline(100, color=PALETTE["ink"], linewidth=0.8, linestyle="--", alpha=0.4)
    ax2.axhline(85, color=PALETTE["grid"], linewidth=0.6, linestyle=":", alpha=0.5)
    ax2.set_ylabel("产能利用率（%）", color=PALETTE["muted"], fontsize=10)
    ax2.tick_params(colors=PALETTE["muted"], labelsize=9)
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{y:.0f}%"))

    # Cycle phase annotations
    phases = data.get("cycle_phase", [])
    phase_map = {p["year"]: p["phase"] for p in phases} if phases else {}
    demand_range = max(demand) - min(demand) if demand else 1
    for i, yr in enumerate(years):
        phase = phase_map.get(yr, "")
        if phase:
            ax1.annotate(phase, xy=(i, demand[i]),
                         xytext=(i, demand[i] + demand_range * 0.12),
                         fontsize=6.5, color=PALETTE["muted"], ha="center",
                         va="bottom", fontstyle="italic",
                         arrowprops=dict(arrowstyle="->", color=PALETTE["grid"],
                                         lw=0.5))

    # Current phase text box
    if current_phase:
        phase_text = f"当前阶段：{current_phase}"
        ax1.text(0.98, 0.95, phase_text, transform=ax1.transAxes, fontsize=9,
                 color=PALETTE["ink"], ha="right", va="top",
                 bbox=dict(boxstyle="round,pad=0.3", facecolor=PALETTE["surface"],
                           edgecolor=PALETTE["grid"], alpha=0.9))

    # Combine legends
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, frameon=False, fontsize=8,
               loc="upper left")

    ax1.set_xticks(x)
    step = max(1, len(years) // 12)
    visible = [str(y) if i % step == 0 else "" for i, y in enumerate(years)]
    ax1.set_xticklabels(visible, fontsize=8, rotation=45, color=PALETTE["muted"],
                        ha="right")
    ax1.set_title(f"行业产能周期：{industry}",
                  color=PALETTE["ink"], fontsize=13, fontweight="bold",
                  loc="left", pad=12)
    for spine in ("top", "right"):
        ax1.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax1.spines[spine].set_color(PALETTE["grid"])
    ax1.grid(axis="both", color=PALETTE["grid"], linewidth=0.6, alpha=0.5)
    ax1.set_axisbelow(True)
    return _save(fig, out_dir, name)


def risk_matrix_chart(data, out_dir, name="risk_matrix"):
    """Risk matrix -- probability vs. value impact scatter with quadrant labels.

    Input shape (from build_risks.py or /durability-check):
        risks: list of {id, category, description, probability,
                        impact_value_per_share, ...}
        Optional: price, value (total intrinsic value for pct conversion)
    """
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
    category_labels = {
        "Cycle": "周期",
        "Competition": "竞争",
        "Technology": "技术",
        "Demand": "需求",
        "Customer": "客户",
        "Customer Concentration": "客户集中度",
        "Geopolitical": "地缘政治",
        "Financial": "财务",
        "Other": "其他",
    }

    # Category color mapping
    unique_cats = sorted(set(categories))
    cat_colors = {
        "Cycle": PALETTE["down"],
        "Competition": "#D97706",
        "Technology": PALETTE["accent"],
        "Demand": "#7C3AED",
        "Customer": PALETTE["ink"],
        "Customer Concentration": PALETTE["ink"],
        "Geopolitical": "#B45309",
        "Financial": PALETTE["up"],
    }
    default_colors = [PALETTE["accent"], PALETTE["down"], PALETTE["up"],
                      "#D97706", "#7C3AED", "#059669", PALETTE["muted"]]
    for i, cat in enumerate(unique_cats):
        if cat not in cat_colors:
            cat_colors[cat] = default_colors[i % len(default_colors)]

    point_colors = [cat_colors.get(c, PALETTE["muted"]) for c in categories]

    fig, ax = plt.subplots(figsize=(8.5, 7.0))

    # Quadrant dividing lines
    med_prob = float(np.median(probs)) if probs else 0.5
    med_impact = float(np.median(impacts)) if impacts else 0.0

    ax.axhline(med_impact, color=PALETTE["grid"], linewidth=1.0, linestyle="--")
    ax.axvline(med_prob, color=PALETTE["grid"], linewidth=1.0, linestyle="--")

    # Quadrant labels
    ax.text(0.98, 0.98, "重点缓释\n（高概率，高影响）",
            transform=ax.transAxes, ha="right", va="top", fontsize=8,
            color=PALETTE["down"], fontweight="bold", alpha=0.7)
    ax.text(0.02, 0.98, "持续监测\n（低概率，高影响）",
            transform=ax.transAxes, ha="left", va="top", fontsize=8,
            color=PALETTE["ink"], fontweight="bold", alpha=0.7)
    ax.text(0.98, 0.02, "主动管理\n（高概率，低影响）",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=8,
            color="#D97706", fontweight="bold", alpha=0.7)
    ax.text(0.02, 0.02, "接受\n（低概率，低影响）",
            transform=ax.transAxes, ha="left", va="bottom", fontsize=8,
            color=PALETTE["muted"], fontweight="bold", alpha=0.7)

    # Scatter points with impact-based sizing
    impact_abs = [abs(imp) for imp in impacts]
    max_impact = max(impact_abs) if impact_abs else 1
    sizes = [max(60, abs(imp) / max(max_impact, 0.001) * 400) for imp in impacts]
    ax.scatter(probs, impacts, c=point_colors, s=sizes, alpha=0.75,
               edgecolors="white", linewidth=0.5, zorder=3)

    # Labels
    for i, risk_name in enumerate(names):
        y_offset = -12 if impacts[i] < med_impact else 10
        ax.annotate(risk_name, (probs[i], impacts[i]),
                    textcoords="offset points", xytext=(0, y_offset),
                    fontsize=7, ha="center", color=PALETTE["ink"],
                    arrowprops=dict(arrowstyle="-", color=PALETTE["grid"],
                                    lw=0.5))

    # Legend for categories
    legend_handles = [plt.Line2D([0], [0], marker="o", color="w",
                                 markerfacecolor=cat_colors[cat],
                                 markersize=8, label=category_labels.get(cat, cat))
                      for cat in unique_cats]
    ax.legend(handles=legend_handles, frameon=False, fontsize=7.5,
              loc="lower right", title="风险类别", title_fontsize=8)

    ax.set_xlabel("估计概率", color=PALETTE["muted"], fontsize=10)
    if total_value:
        ax.set_ylabel("价值影响（占内在价值比例）",
                      color=PALETTE["muted"], fontsize=10)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{y:.0%}"))
    else:
        ax.set_ylabel("价值影响（每股）", color=PALETTE["muted"],
                      fontsize=10)
    ax.set_xlim(-0.02, max(probs) * 1.08 if probs else 1.0)
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:.0%}"))
    ax.tick_params(colors=PALETTE["muted"], labelsize=9)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color(PALETTE["grid"])
    ax.grid(axis="both", color=PALETTE["grid"], linewidth=0.6, alpha=0.5)
    ax.set_axisbelow(True)
    ax.set_title("风险矩阵：概率与价值影响",
                 color=PALETTE["ink"], fontsize=13, fontweight="bold",
                 loc="left", pad=12)
    return _save(fig, out_dir, name)


def commodity_price_deck_chart(data, out_dir, name="commodity_price_deck"):
    rows = data["rows"]
    years = [r["year"] for r in rows]
    prices = [r["commodity_price"] for r in rows]
    costs = [r.get("cash_cost") for r in rows]
    norm = data.get("normalization", {})
    commodity = data.get("commodity", {})
    unit = commodity.get("price_unit", "")

    fig, ax = plt.subplots(figsize=FIGSIZE)
    ax.plot(years, prices, marker="o", linewidth=2.2, color=PALETTE["accent"],
            label="预测价格表")
    if any(c is not None for c in costs):
        cost_vals = [np.nan if c is None else c for c in costs]
        ax.plot(years, cost_vals, marker="s", linewidth=1.8, color=PALETTE["down"],
                label="现金成本表")
        ax.fill_between(years, prices, cost_vals, where=np.array(prices) >= np.array(cost_vals),
                        color=PALETTE["up"], alpha=0.08)
    if norm.get("normalized_price") is not None:
        ax.axhline(norm["normalized_price"], color=PALETTE["ink"], linewidth=1.3,
                   linestyle="--", label="正常化价格")
    if norm.get("current_price") is not None:
        ax.axhline(norm["current_price"], color=PALETTE["muted"], linewidth=1.1,
                   linestyle=":", label="当前现货/参考价")

    ylabel = f"价格（{unit}）" if unit else "价格"
    _style(ax, "商品价格表与正常化价格", "年份", ylabel)
    ax.legend(frameon=False, fontsize=8.5, loc="best")
    return _save(fig, out_dir, name)


def cost_curve_position_chart(data, out_dir, name="cost_curve_position"):
    curve = data.get("cost_curve") or []
    norm = data.get("normalization", {})
    commodity = data.get("commodity", {})
    unit = commodity.get("price_unit", "")

    fig, ax = plt.subplots(figsize=FIGSIZE)
    if curve:
        labels = [str(x.get("label", f"Point {i + 1}")) for i, x in enumerate(curve)]
        costs = [float(x["cash_cost"]) for x in curve]
        colors = [PALETTE["accent"] if x.get("company") else PALETTE["grid"] for x in curve]
        xs = np.arange(len(curve))
        ax.bar(xs, costs, color=colors, width=0.64)
        ax.set_xticks(xs)
        ax.set_xticklabels(labels, rotation=25, ha="right", fontsize=8.5)
    else:
        rows = data["rows"]
        labels = ["当前成本", "平均预测成本", "正常化价格"]
        row_costs = [r.get("cash_cost") for r in rows if r.get("cash_cost") is not None]
        current_cost = row_costs[0] if row_costs else 0.0
        avg_cost = mean(row_costs) if row_costs else current_cost
        costs = [current_cost, avg_cost, norm.get("normalized_price", 0.0)]
        ax.bar(np.arange(3), costs, color=[PALETTE["accent"], PALETTE["grid"], PALETTE["up"]])
        ax.set_xticks(np.arange(3))
        ax.set_xticklabels(labels, rotation=0, fontsize=8.5)

    if norm.get("current_price") is not None:
        ax.axhline(norm["current_price"], color=PALETTE["down"], linewidth=1.6,
                   label="当前现货/参考价")
    if norm.get("normalized_price") is not None:
        ax.axhline(norm["normalized_price"], color=PALETTE["ink"], linewidth=1.3,
                   linestyle="--", label="正常化价格")

    ylabel = f"成本 / 价格（{unit}）" if unit else "成本 / 价格"
    _style(ax, "成本曲线位置", None, ylabel)
    ax.legend(frameon=False, fontsize=8.5, loc="best")
    return _save(fig, out_dir, name)


def cycle_position_dashboard_chart(data, out_dir, name="cycle_position_dashboard"):
    norm = data.get("normalization", {})
    rows = data.get("rows", [])
    utilization = [r.get("utilization") for r in rows if r.get("utilization") is not None]
    margins = [r.get("ebitda_margin") for r in rows if r.get("ebitda_margin") is not None]
    capex_to_ebitda = [
        r["capex_m"] / r["ebitda_m"]
        for r in rows
        if r.get("ebitda_m") and r.get("capex_m") is not None
    ]

    metrics = [
        ("价格分位", norm.get("cycle_price_percentile", 0.5)),
        ("产能利用率", mean(utilization) if utilization else 0.5),
        ("EBITDA 利润率", mean(margins) if margins else 0.0),
        ("资本开支 / EBITDA", mean(capex_to_ebitda) if capex_to_ebitda else 0.0),
    ]
    labels = [m[0] for m in metrics]
    values = [max(0.0, min(1.5, float(m[1]))) for m in metrics]
    colors = [PALETTE["accent"], PALETTE["up"], PALETTE["ink"], PALETTE["down"]]

    fig, ax = plt.subplots(figsize=FIGSIZE)
    ys = np.arange(len(metrics))
    ax.barh(ys, values, color=colors, alpha=0.85)
    ax.axvline(1.0, color=PALETTE["grid"], linewidth=1.2, linestyle="--")
    ax.set_yticks(ys)
    ax.set_yticklabels(labels, fontsize=9.5, color=PALETTE["ink"])
    ax.invert_yaxis()
    for y, v in zip(ys, values):
        ax.text(v + 0.02, y, f"{v:.0%}", va="center", fontsize=8.5,
                color=PALETTE["muted"])
    ax.set_xlim(0, max(1.25, max(values) * 1.18 if values else 1.25))
    _style(ax, "周期位置仪表盘", "比例 / 分位")
    ax.grid(axis="y", visible=False)
    return _save(fig, out_dir, name)


def midcycle_multiple_bridge_chart(data, out_dir, name="midcycle_multiple_bridge"):
    methods = data.get("methods", [])
    weighted = data.get("weighted", {})
    label_map = {
        "Price-deck DCF": "价格表 DCF",
        "Mid-cycle EV/EBITDA": "中周期 EV/EBITDA",
        "Asset NPV": "资产 NPV",
    }
    labels = [label_map.get(m.get("label", m["method"]), m.get("label", m["method"])) for m in methods] + ["加权值"]
    values = [m["value_per_share"] for m in methods] + [weighted.get("value_per_share", 0.0)]
    colors = [PALETTE["grid"]] * len(methods) + [PALETTE["accent"]]

    fig, ax = plt.subplots(figsize=FIGSIZE)
    xs = np.arange(len(values))
    ax.bar(xs, values, color=colors, width=0.62)
    ax.set_xticks(xs)
    ax.set_xticklabels(labels, rotation=18, ha="right", fontsize=8.5)
    for x, v in zip(xs, values):
        ax.text(x, v, f"{v:,.1f}", ha="center", va="bottom", fontsize=8.5,
                color=PALETTE["muted"])
    _style(ax, "中周期估值桥", None, "每股价值")
    ax.grid(axis="x", visible=False)
    return _save(fig, out_dir, name)


KINDS = {
    "montecarlo": monte_carlo_hist,
    "football": football_field,
    "breakeven": breakeven_heatmap,
    "tornado": sensitivity_tornado,
    "terminal": terminal_share,
    "revenue_traj": revenue_traj_chart,
    "roic_spread": roic_spread_chart,
    "scenarios": scenarios_chart,
    "price_vs_value": price_vs_value_chart,
    "waterfall": waterfall_chart,
    "capex_cycle": capex_cycle_chart,
    "risk_matrix": risk_matrix_chart,
    "commodity_price_deck": commodity_price_deck_chart,
    "cost_curve_position": cost_curve_position_chart,
    "cycle_position_dashboard": cycle_position_dashboard_chart,
    "midcycle_multiple_bridge": midcycle_multiple_bridge_chart,
}


def _main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Render research-report charts from engine JSON.")
    ap.add_argument("--kind", required=True, choices=sorted(KINDS))
    ap.add_argument("--in", dest="in_path", required=True, help="path to the source JSON")
    ap.add_argument("--out", default="figs", help="output directory (PNG + SVG)")
    ap.add_argument("--ticker", default=None, help="ticker symbol; output stem becomes {TICKER}_{kind}")
    ap.add_argument("--name", default=None, help="output file stem (overrides --ticker + --kind combination)")
    args = ap.parse_args(argv)
    with open(args.in_path, "r", encoding="utf-8-sig") as fh:
        data = json.load(fh)
    fn = KINDS[args.kind]
    _default_name = f"{args.ticker}_{args.kind}" if args.ticker else args.kind
    paths = fn(data, args.out, name=args.name or _default_name)
    print("wrote:")
    for p in paths:
        print(f"  {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
