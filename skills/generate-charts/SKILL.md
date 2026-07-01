---
name: equity-research-analyst/generate-charts
description: >
  Render publication-grade equity research charts from the valuation engine's JSON
  outputs. Produces 12 chart types with consistent theming, full CJK font support,
  and SVG-primary/PNG-fallback output. Called after run-valuation, before write-report
  if charts are referenced inline, or after write-report for final rendering.
  Supports per-report theme customization via YAML config.
license: MIT
---

# Generate Charts

**Pipeline position:** Called after `/run-valuation` (STEP 6) and typically before
`/write-report` (STEP 8). Charts may also be regenerated during `/generate-pdf`
(STEP 9) if layout or resolution adjustments are needed.

This sub-skill consumes the engine's JSON outputs and produces every chart in the
report. It never recomputes a valuation -- it only visualises numbers the engine
already produced, so a chart can never disagree with the report's arithmetic.

## Shared publishing contract

Read `references/publishing-contract.md` when a report is being produced or
refreshed. The chart `lang` must equal the report `report_lang`.

For Chinese reports:

- render chart titles, subtitles, axes, legends, annotations, and source notes in
  Chinese;
- use CJK-capable fonts and fail fast if none are available;
- format natural units locally where appropriate (`亿元`, `%`, `倍`);
- avoid English broker-template words in SVG text unless they are tickers,
  company legal names, formulas, or source titles.

## Architecture

```
/generate-charts
├── SKILL.md                    ← THIS FILE
├── scripts/
│   ├── charts.py               ← Main chart factory (rewrite of current charts.py)
│   ├── theme.py                ← Theme loader, rcParams config, font detection
│   ├── cjk_fonts.py            ← Cross-platform CJK font auto-detection
│   ├── chart_utils.py          ← Shared: _style(), _save(), label formatting
│   ├── chart_montecarlo.py     ← Monte Carlo histogram
│   ├── chart_breakeven.py      ← Breakeven heatmap
│   ├── chart_terminal.py       ← Terminal value donut
│   ├── chart_football.py       ← Football field (valuation range comparison)
│   ├── chart_tornado.py        ← Sensitivity tornado
│   ├── chart_revenue_traj.py   ← Revenue & margin trajectory (NEW)
│   ├── chart_roic_spread.py    ← ROIC-WACC spread over time (NEW)
│   ├── chart_scenarios.py      ← Scenario comparison bar/waterfall (NEW)
│   ├── chart_price_vs_value.py ← Price vs intrinsic value history (NEW)
│   ├── chart_waterfall.py      ← Driver waterfall bridge (NEW)
│   ├── chart_capex_cycle.py    ← CAPEX cycle chart (NEW)
│   └── chart_risk_matrix.py    ← Risk matrix scatter (NEW)
├── themes/
│   ├── default.yaml            ← Default finance theme
│   ├── goldman.yaml            ← Goldman Sachs aesthetic
│   ├── ms.yaml                 ← Morgan Stanley aesthetic
│   └── cjk.yaml                ← CJK-optimized overrides
├── fonts/
│   └── README.md               ← Font installation instructions per OS
└── tests/
    ├── test_charts.py
    └── test_theme.py
```

### Mode A pipeline integration

```
/run-valuation  →  engine JSON outputs (mc.json, be.json, ff.json, dcf.json, ...)
                        ↓
/generate-charts →  reads JSON → renders SVG+PNG → writes figs/
                        ↓
/write-report    →  Markdown with ![](figs/...) references
                        ↓
/self-audit      →  verifies chart existence in report
                        ↓
/generate-pdf    →  SVG chart embeds for vector-quality PDF; re-renders if needed
```

**Invocation contract:**
```
/generate-charts reads an output-manifest.json produced by /run-valuation:
  {
    "ticker": "0700.HK",
    "output_dir": "figs/0700",
    "charts": [
      {"kind": "montecarlo",   "in": "engine/mc.json",    "name": "montecarlo"},
      {"kind": "breakeven",    "in": "engine/be.json",    "name": "breakeven"},
      {"kind": "terminal",     "in": "engine/dcf.json",   "name": "terminal"},
      {"kind": "football",     "in": "engine/ff.json",    "name": "football"},
      {"kind": "tornado",      "in": "engine/to.json",    "name": "tornado"},
      {"kind": "revenue_traj", "in": "engine/dcf.json",   "name": "revenue_traj"},
      {"kind": "roic_spread",  "in": "engine/durability.json", "name": "roic_spread"},
      {"kind": "scenarios",    "in": "engine/scenarios.json",  "name": "scenarios"},
      {"kind": "price_vs_value","in": "engine/history.json",   "name": "price_vs_value"},
      {"kind": "waterfall",    "in": "engine/waterfall.json",  "name": "waterfall"},
      {"kind": "capex_cycle",  "in": "engine/capex.json",      "name": "capex_cycle"},
      {"kind": "risk_matrix",  "in": "engine/risks.json",      "name": "risk_matrix"}
    ],
    "theme": "default",
    "lang": "zh-CN"
  }
```

All 12 chart kinds are supported; the manifest specifies which subset to render.
At minimum, the 5 existing kinds (montecarlo, football, breakeven, tornado, terminal)
are always produced. The 7 new kinds are rendered when their input JSON is available.

### CLI interface

```bash
# Single chart (backward-compatible with current charts.py API)
python scripts/charts.py --kind montecarlo --in engine/mc.json --out figs/ --lang zh-CN

# Batch from manifest (primary mode)
python scripts/charts.py --manifest output-manifest.json

# With explicit theme override
python scripts/charts.py --manifest output-manifest.json --theme goldman
```

---

## Chart Catalog (12 types)

Every chart adheres to the **single-takeaway discipline**:
- A bold 10pt title stating the **conclusion** (not just the topic)
- A 7.5pt subtitle with context (date, assumptions, source)
- Properly labeled axes with units and zero-baseline (for bars)
- A 6.5–7pt source footnote
- No 3D effects, no shadows, no rotated labels, no dual axes without explicit warning markers

### 1. Monte Carlo Histogram
**Purpose:** Show the full distribution of intrinsic value, the price's position in it, and the margin-of-safety buy-band.

**Input JSON schema:**
```json
{
  "values": [120.5, 131.2, ...],
  "percentiles": {"p5": 80, "p25": 110, "p50": 145, "p75": 180, "p95": 220},
  "price": 95.0,
  "price_percentile": 0.12,
  "mos_band": {
    "buy_below": 101.5,
    "median": 145.0,
    "rich_above": 217.5,
    "mos": 0.30
  }
}
```

**Rendering spec:**
- 60-bin histogram, accent-blue fill at 0.55 alpha, white edge line
- MoS buy-band as a subtle gray vertical span (`band` color at 0.10 alpha)
- Vertical dashed line at `buy_below` (green, "Accumulate <= $X")
- Vertical solid line at `median` (ink, "Fair $X")
- Vertical solid thick line at `price` (red, "Price $X (Yth pctile)")
- Legend: upper-right, no frame, 8pt
- Title: "Intrinsic value distribution — Monte Carlo (N=20,000 trials)"
- Subtitle: "As of [date]. Current price at [X]th percentile of value distribution."
- X-axis: "Intrinsic value per share ($)"
- Y-axis: "Frequency (trials)"

### 2. Breakeven Heatmap
**Purpose:** Show what Year-10 revenue and operating margin combinations justify the current price.

**Input JSON schema:**
```json
{
  "revenues": [50000, 75000, 100000, 125000, 150000, 175000, 200000],
  "margins": [0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40],
  "grid": [[45, 67, 89, 111, 133, 155, 177], ...],
  "price": 95.0,
  "base_revenue": 120000,
  "base_margin": 0.28
}
```

**Rendering spec:**
- `pcolormesh` with RdYlGn colormap (green = undervalued, red = overvalued)
- Cells that reach price marked with a white ★ star character
- Base case cell outlined with a bold ink rectangle
- X-axis: "Target operating margin" (percentage labels)
- Y-axis: "Year-10 revenue" (formatted as $XB)
- Value annotations in each cell (6.5pt, ink)
- Colorbar: "Value per share ($)"
- Title: "Breakeven: what must be true for the price to be right"
- Subtitle: "★ = cell value >= current price of $X. Base case: Y10 rev $XB, margin Y%."
- Gridlines hidden (grid is the data)

### 3. Terminal Value Donut
**Purpose:** Show the split between explicit forecast value and terminal value, highlighting terminal dependency.

**Input JSON schema:**
```json
{
  "terminal_pct_of_value": 0.72,
  "explicit_pct": 0.28,
  "dcf_value": 145.0,
  "terminal_value": 104.4,
  "explicit_value": 40.6,
  "growth_rate": 0.03,
  "risk_free_rate": 0.04
}
```

**Rendering spec:**
- Donut chart (pie with `wedgeprops=dict(width=0.42)`) not a full pie
- Two segments: Explicit FCFF (accent blue), Terminal value (muted gray)
- Center annotation: "72%\nin terminal" (14pt bold, ink)
- Legend below chart: "Explicit FCFF (Y1–10): 28% ($X/share)" / "Terminal value: 72% ($X/share)"
- An additional annotation if terminal growth >= risk-free rate: ⚠ warning symbol + "Terminal growth (3%) approaches risk-free rate (4%)"
- Title: "Where the value sits — terminal value dependency"
- Subtitle: "Higher terminal % = more sensitive to long-run assumptions."
- Note: always a donut, never a full pie. The hole carries the key message.

### 4. Football Field (Valuation Range Comparison)
**Purpose:** Compare the intrinsic value range across 5–7 valuation lenses on one horizontal axis.

**Input JSON schema:**
```json
{
  "price": 95.0,
  "lenses": [
    {"label": "DCF (base)",        "low": 120, "high": 170, "mid": 145},
    {"label": "Monte Carlo (P25–P75)", "low": 110, "high": 180, "mid": 145},
    {"label": "Reverse DCF",       "low": 90,  "high": 140, "mid": 115},
    {"label": "Peer P/E",          "low": 100, "high": 155, "mid": 128},
    {"label": "Peer EV/EBITDA",    "low": 105, "high": 160, "mid": 133},
    {"label": "DCF (bear)",        "low": 75,  "high": 110, "mid": 92},
    {"label": "DCF (bull)",        "low": 160, "high": 230, "mid": 195}
  ]
}
```

**Rendering spec:**
- Horizontal bars (linewidth 9, round caps, alpha 0.85) for each lens range
- Diamond marker at midpoint
- Low/high values printed as edge labels (8.5pt, muted gray)
- Price as a vertical red dashed line across the full height
- Y-axis: lens labels, no gridlines
- X-axis: "Value per share ($)"
- Title: "Valuation football field — [TICKER]"
- Subtitle: "Range across [N] valuation lenses. Diamond = midpoint estimate."
- Bar color: accent blue for primary (DCF-based), lighter blue for supporting, gray for sensitivity cases

### 5. Sensitivity Tornado
**Purpose:** Show which drivers have the largest impact on value per share when varied by +/-1 standard deviation.

**Input JSON schema:**
```json
{
  "base": 145.0,
  "drivers": [
    {"name": "Revenue growth (Y1–5)",  "low": 105, "high": 195},
    {"name": "Terminal op. margin",    "low": 118, "high": 168},
    {"name": "WACC",                   "low": 125, "high": 160},
    {"name": "Revenue growth (Y6–10)", "low": 130, "high": 158},
    {"name": "Terminal growth rate",   "low": 135, "high": 153},
    {"name": "Tax rate",               "low": 140, "high": 150}
  ]
}
```

**Rendering spec:**
- Horizontal stacked bar chart: left side = downside (red, alpha 0.75), right side = upside (green, alpha 0.75)
- Drivers sorted by impact magnitude (|high - low|), smallest at top
- Base case as a vertical ink line across the full height
- Y-axis: driver names (9.5pt, ink)
- X-axis: "Value per share ($)"
- Title: "Sensitivity: value per share vs driver +/-1SD"
- Subtitle: "Sorted by impact. Bar length = range of value outcomes."
- Legend: "Base case $X" (ink line), down arrow for downside, up arrow for upside

### 6. Revenue & Margin Trajectory (NEW)
**Purpose:** Show the projection path -- how revenue and margins evolve over the explicit forecast period.

**Input JSON schema:**
```json
{
  "years": [2025, 2026, 2027, 2028, 2029, 2030, 2031, 2032, 2033, 2034],
  "revenue": [8500, 9350, 10285, 11314, 12445, 13690, 14374, 15093, 15847, 16640],
  "revenue_growth": [0.12, 0.10, 0.10, 0.10, 0.10, 0.10, 0.05, 0.05, 0.05, 0.05],
  "op_margin": [0.22, 0.23, 0.24, 0.25, 0.26, 0.27, 0.28, 0.285, 0.29, 0.30],
  "fcff_margin": [0.14, 0.15, 0.16, 0.17, 0.18, 0.18, 0.19, 0.19, 0.19, 0.20],
  "historical_revenue": [5000, 5800, 6700, 7600],
  "historical_margin": [0.18, 0.19, 0.20, 0.21],
  "historical_years": [2021, 2022, 2023, 2024]
}
```

**Rendering spec:**
- Dual-panel figure (2 rows, 1 column, shared x-axis, figsize=(7, 5.5))
- **Top panel:** Revenue bars + revenue growth line (right y-axis)
  - Blue bars for revenue ($B), gray dashed line for growth rate (%, right axis)
  - Historical period shaded with lighter alpha
  - Vertical dashed line at "forecast start"
- **Bottom panel:** Margin lines
  - Operating margin (solid navy line), FCFF margin (dashed navy line)
  - Historical margins shown with markers
- Title: "Revenue & margin trajectory — [TICKER]"
- Subtitle: "Historical (2021–2024) + projected (2025–2034). Growth decelerates from 12% to 5%."
- Dual-axis warning annotation: "Note: Revenue ($B, left axis) and growth rate (%, right axis) use different scales."

### 7. ROIC-WACC Spread Over Time (NEW)
**Purpose:** Visualize durability -- how long the company earns excess returns, and the fade pattern.

**Input JSON schema:**
```json
{
  "years": [2025, 2026, 2027, 2028, 2029, 2030, 2031, 2032, 2033, 2034],
  "roic": [0.18, 0.19, 0.20, 0.21, 0.20, 0.19, 0.17, 0.15, 0.13, 0.12],
  "wacc": [0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09],
  "spread": [0.09, 0.10, 0.11, 0.12, 0.11, 0.10, 0.08, 0.06, 0.04, 0.03],
  "competitive_advantage_period": 8,
  "historical_roic": [0.16, 0.17, 0.18, 0.18],
  "historical_years": [2021, 2022, 2023, 2024]
}
```

**Rendering spec:**
- ROIC line (solid navy) and WACC line (dashed flat gray at constant level)
- Spread area fill between ROIC and WACC:
  - Green (0.10 alpha) when ROIC > WACC
  - Red (0.10 alpha) when ROIC < WACC
- Vertical dashed line at Competitive Advantage Period (CAP) end
- Annotation: "CAP = Y years" at the CAP line
- Title: "ROIC-WACC spread — durability assessment"
- Subtitle: "Excess returns persist for ~[Y] years before fading to cost of capital. CAP = [Y] years."
- Y-axis: "Return / Cost of capital (%)"
- X-axis: "Year"

### 8. Scenario Comparison (NEW)
**Purpose:** Show bull/base/bear value ranges side-by-side with key driver differences.

**Input JSON schema:**
```json
{
  "scenarios": [
    {
      "name": "Bear",
      "value_low": 75,
      "value_high": 105,
      "value_mid": 90,
      "key_drivers": {
        "Revenue CAGR (Y1–10)": "4%",
        "Terminal op. margin": "22%",
        "WACC": "10.5%"
      },
      "probability": 0.25
    },
    {
      "name": "Base",
      "value_low": 120,
      "value_high": 170,
      "value_mid": 145,
      "key_drivers": {
        "Revenue CAGR (Y1–10)": "8%",
        "Terminal op. margin": "28%",
        "WACC": "9.0%"
      },
      "probability": 0.50
    },
    {
      "name": "Bull",
      "value_low": 175,
      "value_high": 240,
      "value_mid": 208,
      "key_drivers": {
        "Revenue CAGR (Y1–10)": "12%",
        "Terminal op. margin": "34%",
        "WACC": "8.0%"
      },
      "probability": 0.25
    }
  ],
  "price": 95.0
}
```

**Rendering spec:**
- Horizontal "floating bar" chart: one row per scenario, bar from value_low to value_high
- Midpoint diamond marker on each bar
- Price vertical dashed red line across all rows
- Scenario probability annotated as a small badge (e.g., "p=25%") next to each bar
- Driver table below the chart: key driver values in small text per scenario (3 columns)
- Title: "Scenario analysis — [TICKER] value ranges"
- Subtitle: "Probability-weighted value: $[weighted avg]. Current price $[X] at [Y]th percentile of bear case."
- Color: Bear = muted gray, Base = accent blue, Bull = lighter blue

### 9. Price vs Intrinsic Value History (NEW)
**Purpose:** Show how the price-value gap has evolved over time, if historical valuations are available.

**Input JSON schema:**
```json
{
  "dates": ["2021-12-31", "2022-06-30", "2022-12-31", "2023-06-30", "2023-12-31", "2024-06-30", "2024-12-31"],
  "price": [60, 55, 48, 72, 85, 78, 95],
  "value_low": [80, 78, 75, 90, 105, 110, 120],
  "value_mid": [105, 100, 98, 115, 135, 140, 145],
  "value_high": [130, 125, 120, 140, 165, 170, 170],
  "events": [
    {"date": "2022-12-31", "label": "COVID reopening", "y_offset": 0.85}
  ]
}
```

**Rendering spec:**
- Price line (solid red, 2pt)
- Value band: `fill_between` value_low to value_high (band gray, 0.12 alpha)
- Value mid line (dashed navy, 1.5pt)
- Event markers: vertical dashed gray lines with text annotations at top
- Gap annotation at rightmost point: "Price $X / Value $Y = [Z]% discount"
- Title: "Price vs. intrinsic value — [TICKER] (2021–present)"
- Subtitle: "Shaded band = intrinsic value range (low–high). Current discount to midpoint: [X]%."
- Y-axis: "Value / Price per share ($)"
- X-axis: "Date"

### 10. Driver Waterfall (NEW)
**Purpose:** Bridge from the current stock price to intrinsic value, showing how each driver contributes to the gap.

**Input JSON schema:**
```json
{
  "price": 95.0,
  "intrinsic_value": 145.0,
  "steps": [
    {"label": "Current price", "value": 95.0},
    {"label": "+ Revenue growth\n(higher than priced)", "delta": 18.0, "direction": "up"},
    {"label": "+ Margin expansion\n(operating leverage)", "delta": 14.0, "direction": "up"},
    {"label": "+ Lower WACC\n(less leverage)", "delta": 8.0, "direction": "up"},
    {"label": "+ Terminal value\n(long-run economics)", "delta": 12.0, "direction": "up"},
    {"label": "− Competitive fade\n(ROIC → WACC)", "delta": -2.0, "direction": "down"},
    {"label": "Intrinsic value", "value": 145.0}
  ]
}
```

**Rendering spec:**
- Waterfall chart: starting bar (price), then incremental floating bars (green for up, red for down), ending bar (intrinsic value)
- Connector lines between bars
- Bar value labels above/below each bar
- Total gap annotation: "Value-Price gap: +$50 (+53%)"
- Title: "Value bridge: what drives the $[X] gap"
- Subtitle: "Current price $[X] → Intrinsic value $[Y]. Each step = contribution of one driver."
- X-axis labels may be split into two lines (7pt font acceptable for waterfall)
- Y-axis: "Value per share ($)"

### 11. CAPEX Cycle Chart (NEW)
**Purpose:** Show industry capacity additions timeline vs demand growth -- relevant for cyclical and commodity companies.

**Input JSON schema:**
```json
{
  "years": [2020, 2021, 2022, 2023, 2024, 2025, 2026, 2027, 2028],
  "demand_growth": [3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 5.0, 4.5, 4.0],
  "capacity_additions": [2.0, 2.5, 3.0, 4.0, 5.5, 6.0, 4.5, 3.0, 2.5],
  "utilization_rate": [0.85, 0.87, 0.88, 0.86, 0.82, 0.78, 0.80, 0.84, 0.88],
  "cycle_phase": "mid-cycle",
  "normalized_spread": 0.06
}
```

**Rendering spec:**
- Dual-axis line chart: demand growth (solid blue, left axis) vs capacity additions (dashed orange, left axis)
- Utilization rate as a shaded area or second line on right axis
- Horizontal line at 100% utilization
- Cycle phase annotation: text box in upper-right with phase label
- Title: "Industry capacity cycle — [sector]"
- Subtitle: "Demand growth rate vs. capacity additions. Current phase: mid-cycle. Normalized spread: 6%."
- Left Y-axis: "Growth rate (YoY %)"
- Right Y-axis: "Utilization rate (%)"
- X-axis: "Year"

### 12. Risk Matrix (NEW)
**Purpose:** Plot key risks by estimated probability vs value impact, creating a visual priority map.

**Input JSON schema:**
```json
{
  "risks": [
    {
      "name": "Regulatory crackdown",
      "probability": 0.15,
      "impact_pct": -0.40,
      "category": "regulatory",
      "description": "New data/privacy regulation reduces addressable market",
      "monitorable": "Legislative calendar, NDRC announcements"
    },
    {
      "name": "Key person departure",
      "probability": 0.10,
      "impact_pct": -0.15,
      "category": "operational",
      "description": "Loss of founder/CEO reduces strategic execution",
      "monitorable": "Company filings, media, LinkedIn alerts"
    },
    {
      "name": "Competitor entry",
      "probability": 0.30,
      "impact_pct": -0.25,
      "category": "competitive",
      "description": "Major tech platform enters core market",
      "monitorable": "Product launches, pricing changes, market share data"
    },
    {
      "name": "Margin compression",
      "probability": 0.40,
      "impact_pct": -0.15,
      "category": "financial",
      "description": "Input cost inflation outpacing pricing power",
      "monitorable": "Quarterly gross margins, PPI vs CPI spread"
    },
    {
      "name": "Currency / macro shock",
      "probability": 0.20,
      "impact_pct": -0.20,
      "category": "macro",
      "description": "USD/CNY moves 10%+ against base case assumption",
      "monitorable": "FX forwards, PBOC fixing rate"
    }
  ],
  "price": 95.0,
  "value": 145.0
}
```

**Rendering spec:**
- Scatter plot: x = probability (0–100%), y = impact (% of value)
- Four quadrants divided by median probability and median impact
  - Top-right: "Mitigate / hedge" (high prob, high impact)
  - Top-left: "Monitor" (low prob, high impact)
  - Bottom-right: "Manage" (high prob, low impact)
  - Bottom-left: "Accept" (low prob, low impact)
- Each risk as a bubble scaled by a third dimension (optional -- default uniform)
- Risk labels as text annotations near each point (6.5pt, ink)
- Quadrant background shading (subtle)
- Title: "Risk matrix — probability vs. value impact"
- Subtitle: "Bubble = risk to intrinsic value. Top-right quadrant requires active mitigation."
- X-axis: "Estimated probability (%)"
- Y-axis: "Value impact (% of intrinsic value)"
- Invert Y-axis so negative values go downward

---

## CJK Font Strategy

### Problem
The current `charts.py` inherits matplotlib's default `font.sans-serif` stack (DejaVu Sans), which has zero CJK glyphs. Any Chinese, Japanese, or Korean text in titles, labels, or annotations renders as tofu boxes (□).

### Solution

A 40-line `cjk_fonts.py` module that auto-detects the best available CJK font on any platform and configures matplotlib `rcParams` accordingly before any figure is created.

**Detection priority by OS:**

| OS | Priority order (first available wins) |
|----|--------------------------------------|
| **Windows** | Noto Sans SC, Microsoft YaHei, SimHei, DengXian, FangSong, KaiTi |
| **macOS** | Noto Sans CJK SC, PingFang SC, Hiragino Sans GB, Heiti SC, STHeiti |
| **Linux** | Noto Sans CJK SC, Noto Sans SC, WenQuanYi Micro Hei, WenQuanYi Zen Hei, Source Han Sans SC |

Full-width glyphs for JP and KR are also checked with separate stacks:
- **Japanese:** Noto Sans CJK JP, Hiragino Sans, MS Gothic, IPA Gothic
- **Korean:** Noto Sans CJK KR, Malgun Gothic, Nanum Gothic, Apple Gothic

**Implementation in `cjk_fonts.py`:**

```python
"""Cross-platform CJK font auto-detection for matplotlib.

Detects the best available CJK font on the current system and configures
matplotlib rcParams to use it. Handles Windows, macOS, and Linux with
appropriate font stacks for each platform.

Usage (call once at module init, before any figure creation):
    from cjk_fonts import configure_cjk_fonts
    configure_cjk_fonts()
"""

import platform
import matplotlib
from matplotlib.font_manager import fontManager

_FONT_STACKS = {
    "windows": [
        "Noto Sans SC", "Microsoft YaHei", "SimHei",
        "DengXian", "FangSong", "KaiTi",
    ],
    "darwin": [
        "Noto Sans CJK SC", "PingFang SC", "Hiragino Sans GB",
        "Heiti SC", "STHeiti",
    ],
    "linux": [
        "Noto Sans CJK SC", "Noto Sans SC",
        "WenQuanYi Micro Hei", "WenQuanYi Zen Hei",
        "Source Han Sans SC",
    ],
    "jp": [
        "Noto Sans CJK JP", "Hiragino Sans", "MS Gothic", "IPA Gothic",
    ],
    "kr": [
        "Noto Sans CJK KR", "Malgun Gothic", "Nanum Gothic", "Apple Gothic",
    ],
}


def _available_fonts():
    """Return a set of font names available in the matplotlib font manager."""
    return {f.name for f in fontManager.ttflist}


def _detect_best_cjk(target_lang="zh-CN"):
    """Return the first available CJK font for the target language.

    Args:
        target_lang: Language code. 'zh-CN', 'zh-TW', 'ja-JP', 'ko-KR'.

    Returns:
        Font name string, or None if no CJK font found.
    """
    available = _available_fonts()
    system = platform.system().lower()

    if "windows" in system:
        stack = _FONT_STACKS["windows"]
    elif "darwin" in system:
        stack = _FONT_STACKS["darwin"]
    else:
        stack = _FONT_STACKS["linux"]

    # Append JP/KR stacks for those languages
    if "ja" in target_lang.lower():
        stack = _FONT_STACKS["jp"] + stack
    elif "ko" in target_lang.lower():
        stack = _FONT_STACKS["kr"] + stack

    for font_name in stack:
        if font_name in available:
            return font_name

    return None


def configure_cjk_fonts(lang="zh-CN"):
    """Configure matplotlib rcParams for CJK font rendering.

    Prepends the best available CJK font to rcParams['font.sans-serif'].
    Call this ONCE at module init, BEFORE any pyplot.figure() call.

    Args:
        lang: Language code for CJK variant selection.
              'zh-CN' (Simplified Chinese), 'zh-TW' (Traditional Chinese),
              'ja-JP' (Japanese), 'ko-KR' (Korean).

    Returns:
        The name of the font that was configured, or None if no CJK font found.
    """
    cjk_font = _detect_best_cjk(lang)
    if cjk_font is None:
        import warnings
        warnings.warn(
            f"No CJK font found for lang={lang}. "
            f"CJK characters will render as tofu boxes. "
            f"Install Noto Sans CJK from Google Fonts."
        )
        return None

    current = matplotlib.rcParams["font.sans-serif"]
    if isinstance(current, str):
        current = [current]
    if cjk_font not in current:
        matplotlib.rcParams["font.sans-serif"] = [cjk_font] + list(current)

    # Ensure negative signs render as proper minus signs
    matplotlib.rcParams["axes.unicode_minus"] = False

    return cjk_font
```

**When CJK is unavailable:**
- Emit a single warning with installation instructions per OS
- Fall back gracefully -- Latin text renders normally, CJK characters render as tofu
- This is acceptable for internal drafts; the warning makes the limitation explicit

**SVG path conversion:**
With `svg.fonttype = 'path'` (the default), SVG text is converted to vector paths,
making SVGs self-contained with no font dependency on the viewing system. This is
the recommended mode for chart distribution.

---

## Theming System

### Theme file format (YAML)

Themes are YAML files in `themes/`. A theme specifies all visual parameters
for a consistent chart family. Reports reference a theme by name; the theme
is applied globally via rcParams before any chart is rendered.

**`themes/default.yaml`:**

```yaml
# Default finance theme — restrained, publication-grade
name: default
description: Standard equity research palette. Suitable for most reports.

# Color palette (all charts inherit these)
palette:
  ink: "#1A1A1A"          # Primary text, title, emphasis
  muted: "#6B7280"        # Secondary text, axis labels, subtle elements
  grid: "#D1D5DB"         # Gridlines, tick marks
  accent: "#002D72"       # Primary data color (navy blue)
  accent_light: "#4A7AB5" # Lighter accent for secondary series
  up: "#0E6E4D"           # Positive / undervalued / cheap
  down: "#CC0000"         # Negative / overvalued / rich
  band: "#F3F4F6"         # Background band / MoS zone fill
  surface: "#FFFFFF"      # Figure background

# Typography
fonts:
  sans_serif: ["TeX Gyre Heros", "Arial", "Helvetica Neue", "Helvetica", "sans-serif"]
  serif: ["TeX Gyre Termes", "Times New Roman", "Georgia", "serif"]
  monospace: ["Fira Code", "Consolas", "Courier New", "monospace"]
  cjk: ["Noto Sans CJK SC", "Noto Sans SC", "SimHei", "Microsoft YaHei", "sans-serif"]

# Dimensions
figure:
  default_width: 7        # inches
  default_height: 4.2     # inches (7:4.2 = golden-ratio-adjacent)
  dpi: 300                # Output resolution
  facecolor: "#FFFFFF"    # Figure background

# matplotlib rcParams overrides
rcparams:
  font.sans-serif: ["TeX Gyre Heros", "Arial", "Helvetica Neue", "Helvetica", "sans-serif"]
  font.size: 10
  axes.titlesize: 11
  axes.labelsize: 9
  axes.unicode_minus: false
  axes.spines.top: false
  axes.spines.right: false
  axes.spines.left: true
  axes.spines.bottom: true
  axes.linewidth: 0.8
  xtick.direction: out
  ytick.direction: out
  xtick.labelsize: 8
  ytick.labelsize: 8
  grid.alpha: 0.3
  grid.linewidth: 0.5
  legend.fontsize: 8
  legend.frameon: false
  figure.facecolor: "#FFFFFF"
  savefig.bbox: tight
  savefig.pad_inches: 0.15
  savefig.format: svg

# Chart-specific defaults
chart_defaults:
  title_fontsize: 10
  title_fontweight: bold
  title_loc: left
  title_pad: 10
  subtitle_fontsize: 7.5
  subtitle_color: muted
  source_fontsize: 6.5
  source_color: muted
  annotation_fontsize: 8
  annotation_color: ink
```

**`themes/goldman.yaml`:**

```yaml
# Goldman Sachs aesthetic — cooler, more restrained
name: goldman
extends: default
palette:
  ink: "#1C1C1C"
  accent: "#003A70"       # GS darker navy
  up: "#007A4D"           # Darker green
  down: "#B31B1B"         # GS red
figure:
  dpi: 300
rcparams:
  font.size: 9.5
  grid.alpha: 0.2
```

**`themes/ms.yaml`:**

```yaml
# Morgan Stanley aesthetic — warmer, slightly larger
name: ms
extends: default
palette:
  ink: "#1E1E1E"
  accent: "#1C4587"       # MS navy
  up: "#006B3F"           # MS green
  down: "#C41230"         # MS red
figure:
  dpi: 300
```

**`themes/cjk.yaml`:**

```yaml
# CJK-optimized overrides — larger fonts for Chinese readability
name: cjk
extends: default
fonts:
  sans_serif: ["Noto Sans CJK SC", "TeX Gyre Heros", "Arial", "sans-serif"]
rcparams:
  font.size: 11
  axes.titlesize: 12
  axes.labelsize: 10
  xtick.labelsize: 9
  ytick.labelsize: 9
chart_defaults:
  title_fontsize: 11
  subtitle_fontsize: 8
  source_fontsize: 7
```

### Theme loading (`theme.py`)

```python
"""Theme loader for chart generation.

Loads theme YAML files, merges with defaults, and applies rcParams globally.
Supports theme inheritance via the 'extends' key.
"""

import yaml
import os
from pathlib import Path

THEMES_DIR = Path(__file__).resolve().parent.parent / "themes"


def load_theme(name="default"):
    """Load a named theme, resolving inheritance.

    Args:
        name: Theme name (matches filename without .yaml). E.g., 'default',
              'goldman', 'ms', 'cjk'.

    Returns:
        Dict with resolved theme configuration.
    """
    # Load all theme files
    themes = {}
    for f in sorted(THEMES_DIR.glob("*.yaml")):
        with open(f, "r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
            if data and "name" in data:
                themes[data["name"]] = data

    if name not in themes:
        raise ValueError(
            f"Theme '{name}' not found. Available: {sorted(themes.keys())}"
        )

    # Resolve inheritance chain
    resolved = {}
    chain = []
    current = name
    while current:
        if current in chain:
            raise ValueError(f"Circular theme inheritance: {chain}")
        chain.append(current)
        t = themes.get(current)
        if not t:
            break
        # Deep merge (child overrides parent)
        resolved = _deep_merge(resolved, t)
        current = t.get("extends")

    return resolved


def _deep_merge(base, override):
    """Recursively merge override into base dict. Immutable — returns new dict."""
    result = dict(base)
    for k, v in override.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = _deep_merge(result[k], v)
        else:
            result[k] = v
    return result


def apply_theme(name="default", lang="zh-CN"):
    """Load theme and apply rcParams + CJK fonts.

    Call once before any figure creation.

    Args:
        name: Theme name.
        lang: Language code for CJK font selection.

    Returns:
        Theme dict.
    """
    import matplotlib
    from .cjk_fonts import configure_cjk_fonts

    theme = load_theme(name)

    # Apply rcParams
    rc = theme.get("rcparams", {})
    for key, value in rc.items():
        matplotlib.rcParams[key] = value

    # Apply CJK fonts
    configure_cjk_fonts(lang)

    # Apply style base
    try:
        import matplotlib.style
        matplotlib.style.use("seaborn-v0_8-whitegrid")
    except Exception:
        pass  # style not critical

    return theme
```

### Per-report customization

Reports can override any theme parameter by passing a partial theme dict
alongside the output manifest:

```json
{
  "ticker": "0700.HK",
  "theme": "default",
  "theme_overrides": {
    "palette": {
      "accent": "#E60000"
    },
    "chart_defaults": {
      "title_fontsize": 12
    }
  },
  ...
}
```

Overrides are merged on top of the resolved theme before any chart is rendered,
allowing per-report palette adjustments (e.g., using the company's brand color
as the accent) without creating a new theme file.

---

## Output Specifications

### Dimensions

| Parameter | Value | Notes |
|-----------|-------|-------|
| Default width | 7 inches (178 mm) | Fits A4/US Letter with margins |
| Default height | 4.2 inches (107 mm) | 5:3 aspect ratio, golden-ratio adjacent |
| Square charts | 5.6 × 5.6 inches | Donut chart only |
| Dual-panel height | 5.5 inches | Revenue trajectory (2 rows) |
| DPI | 300 minimum | 600 for print-quality raster fallback |
| Face color | White (#FFFFFF) | For PDF embedding on white pages |

### Formats (priority order)

1. **SVG (primary)** — Vector format for PDF embedding. Self-contained when
   `svg.fonttype = 'path'`. No font dependency on viewing system.
2. **PDF (alternative for PGF path)** — Direct vector PDF via PGF/XeLaTeX
   backend. Required for CJK reports needing precise glyph positioning.
3. **PNG (fallback)** — 300 DPI raster for quick preview, markdown embedding,
   and environments where SVG rendering is unreliable.

### File naming convention

```
figs/{TICKER}/{TICKER}_{chart_kind}.{ext}

Examples:
  figs/0700/0700_montecarlo.svg
  figs/0700/0700_montecarlo.png
  figs/0700/0700_football.svg
  figs/0700/0700_football.png
  figs/NVDA/NVDA_roic_spread.svg
  figs/NVDA/NVDA_roic_spread.png

Sub-directory per ticker prevents cross-company file collisions
when running multiple valuations in a session.
```

---

## Integration Contract

### Input: `output-manifest.json`

The manifest is produced by `/run-valuation` and consumed by `/generate-charts`.
It declares which charts to render, where their source data lives, and the
styling preferences.

**Full schema:**

```json
{
  "$schema": "generate-charts manifest v1",
  "ticker": "string (e.g., '0700.HK', 'NVDA')",
  "company_name": "string (e.g., 'Tencent Holdings Ltd.')",
  "output_dir": "string (e.g., 'figs/0700')",
  "lang": "string (zh-CN | ja-JP | ko-KR | en-US)",
  "theme": "string (default | goldman | ms | cjk)",
  "theme_overrides": {},
  "charts": [
    {
      "kind": "string (chart kind name)",
      "in": "string (path to source JSON, relative to workspace)",
      "name": "string (output file stem, defaults to kind)",
      "title_override": "string (optional, overrides auto-generated title)",
      "subtitle_override": "string (optional)"
    }
  ]
}
```

### Output

The sub-skill produces:
1. All chart files in `output_dir/` (SVG + PNG per chart)
2. A `chart-index.json` listing every generated chart with metadata:

```json
{
  "ticker": "0700.HK",
  "generated_at": "2026-06-28T14:30:00Z",
  "theme": "default",
  "lang": "zh-CN",
  "cjk_font": "Noto Sans SC",
  "cjk_font_available": true,
  "files": [
    {
      "kind": "montecarlo",
      "svg": "figs/0700/0700_montecarlo.svg",
      "png": "figs/0700/0700_montecarlo.png",
      "title": "Intrinsic value distribution — Monte Carlo (N=20,000 trials)",
      "width": 7.0,
      "height": 4.2
    }
  ]
}
```

### Downstream consumers

| Consumer | What it reads | How it uses it |
|----------|--------------|----------------|
| `/write-report` | PNG files | `![](figs/0700/0700_montecarlo.png)` in Markdown |
| `/generate-pdf` | SVG files | `<img src="figs/0700/0700_montecarlo.svg">` for vector embed |
| `/self-audit` | `chart-index.json` | Verifies all declared charts were generated |
| `/refresh-valuation` | `output-manifest.json` | Re-runs only charts whose source JSON changed |

---

## Migration Plan: `scripts/charts.py`

### What to keep

The existing `charts.py` (217 lines) is clean, well-structured, and battle-tested.
We preserve:

1. **The 5 existing chart functions** — `monte_carlo_hist()`, `football_field()`,
   `breakeven_heatmap()`, `sensitivity_tornado()`, `terminal_share()` — extracted
   into individual modules but logic preserved.
2. **The `_style()` / `_save()` utility pattern** — upgraded in `chart_utils.py`
   with theme-awareness.
3. **The CLI pattern** — `--kind` / `--in` / `--out` / `--name` flags preserved
   for backward compatibility.
4. **The `KINDS` dispatch dict** — expanded to 12 entries.
5. **The "never recomputes a valuation" principle** — unchanged. Charts only
   visualise engine output.

### What to rewrite

| Current | Replacement | Rationale |
|---------|-------------|-----------|
| Hardcoded `PALETTE` dict | `theme.py` load from YAML | Per-report customization |
| `matplotlib.use("Agg")` only | Agg default, PGF optional for CJK PDF | Vector CJK rendering |
| `DPI = 144` | 300 DPI default | Print-quality output |
| `FIGSIZE = (9.0, 5.2)` | (7.0, 4.2) default | Better A4 fit, configurable |
| No CJK font config | `cjk_fonts.configure_cjk_fonts()` | CJK glyph rendering |
| Inline chart functions | One module per chart kind | Maintainability, testing |
| No theme system | YAML theme files + `theme.py` | Consistent styling |

### Backward compatibility

The existing `charts.py` CLI is preserved 100%:

```bash
# Existing invocations continue to work unchanged
python charts.py --kind montecarlo --in mc.json   --out figs/
python charts.py --kind breakeven  --in be.json   --out figs/
python charts.py --kind football   --in ff.json   --out figs/
python charts.py --kind tornado    --in to.json   --out figs/
python charts.py --kind terminal   --in dcf.json  --out figs/
```

The new code adds but does not break:
```bash
# New batch mode (primary)
python charts.py --manifest output-manifest.json

# New theme override
python charts.py --manifest output-manifest.json --theme goldman

# New language/locale flag
python charts.py --kind montecarlo --in mc.json --out figs/ --lang zh-CN
```

The refactored `charts.py` becomes a thin CLI wrapper that delegates to
per-chart modules and the theme system. The dispatch dict grows:

```python
KINDS = {
    "montecarlo":     chart_montecarlo.render,
    "football":       chart_football.render,
    "breakeven":      chart_breakeven.render,
    "tornado":        chart_tornado.render,
    "terminal":       chart_terminal.render,
    "revenue_traj":   chart_revenue_traj.render,
    "roic_spread":    chart_roic_spread.render,
    "scenarios":      chart_scenarios.render,
    "price_vs_value": chart_price_vs_value.render,
    "waterfall":      chart_waterfall.render,
    "capex_cycle":    chart_capex_cycle.render,
    "risk_matrix":    chart_risk_matrix.render,
}
```

### Module structure for chart modules

Each chart module follows a uniform signature:

```python
"""chart_montecarlo.py — Monte Carlo histogram."""

from __future__ import annotations
import matplotlib.pyplot as plt
from .chart_utils import style_ax, save_fig, format_currency, add_source_footnote


def render(data: dict, out_dir: str, *, name: str = "montecarlo",
           theme: dict | None = None, lang: str = "en-US") -> list[str]:
    """Render a Monte Carlo histogram from engine JSON data.

    Args:
        data: Parsed JSON dict matching the montecarlo input schema.
        out_dir: Output directory. Created if it doesn't exist.
        name: Output file stem.
        theme: Resolved theme dict (from theme.py). If None, uses defaults.
        lang: Language code for labels and annotations.

    Returns:
        List of output file paths (SVG + PNG).
    """
    fig, ax = plt.subplots(figsize=(7.0, 4.2))
    # ... chart-specific rendering logic ...
    style_ax(ax, theme, title="...", xlabel="...", ylabel="...")
    return save_fig(fig, out_dir, name, dpi=theme.get("figure", {}).get("dpi", 300))
```

### Risk matrix

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| CJK font not installed on target system | Medium (Linux CI) | Graceful fallback with warning; document installation in `fonts/README.md` |
| Theme YAML parse error | Low | Validate on load; fall back to hardcoded defaults |
| Backward-incompatible JSON schema change | Low | Version the schema; new charts accept v1, old charts unchanged |
| PGF/XeLaTeX not available | Medium (Windows) | PGF path is optional; Agg backend is the always-available default |
| Chart file conflicts between runs | Low | `output_dir` is ticker-scoped; overwrite is safe |

---

## Workflow: How the Agent Operates

When invoked as `/generate-charts`:

1. **Receive the output-manifest.json path** from the orchestrator (produced by `/run-valuation`).
2. **Load and validate** the manifest — check all `in` paths exist, all `kind` values are valid.
3. **Load theme** via `theme.apply_theme(name, lang)` — this configures rcParams and CJK fonts globally.
4. **Render charts sequentially or in parallel:**
   - Charts are independent (each reads its own JSON input). They CAN be rendered in parallel
     using Python's `concurrent.futures` if performance matters for large batches.
   - For the 5 core chart kinds, render is fast (<1s each at 300 DPI). Parallelism is a
     nice-to-have, not a requirement for correctness.
5. **Save outputs** — SVG + PNG per chart, plus `chart-index.json`.
6. **Run a self-check** against the review criteria below.
7. **Return** the `chart-index.json` path to the orchestrator.

---

## Adversarial Review Gate

### Review criteria

- [ ] **All declared charts generated:** Every chart in the manifest produced both
  SVG and PNG outputs. Missing output → REVISE.
- [ ] **Input JSON validated:** Each source JSON file was parseable and matched the
  expected schema for its chart kind. Invalid input → REVISE.
- [ ] **CJK font configured (if lang is CJK):** `cjk_fonts.configure_cjk_fonts()` ran
  without warning. Tofu boxes in output → REVISE (fix font detection).
- [ ] **Palette respects theme:** No hardcoded colors; all color references come from
  the loaded theme dict. Hardcoded hex → REVISE.
- [ ] **Single-takeaway titles:** Every chart title states a conclusion, not just a
  topic. Compare: "Revenue Growth Slowed to 6% in FY2024" vs "Revenue by Year".
  Topic-only title → REVISE.
- [ ] **Zero-baseline for bar charts:** Football field, tornado, waterfall all have
  x=0 visible. Truncated axis → REVISE (CRITICAL — this is the #1 tell of an
  amateur chart).
- [ ] **No 3D, no shadows, no rotated labels:** Visual grep of generated SVGs. Any
  found → REVISE.
- [ ] **Scale labels present on all axes:** Every axis has visible tick marks and
  labeled units. Missing → REVISE.
- [ ] **Source footnote on every chart:** 6.5–7pt source line at bottom. Missing → REVISE.
- [ ] **SVG output is valid XML:** `xml.etree.ElementTree.parse(svg_path)` succeeds.
  Broken SVG → REVISE.
- [ ] **Chart-index.json is valid and complete:** All files listed, paths resolve.
  Incomplete → REVISE.

### Common failure modes

- CJK font not found → tofu boxes in Chinese labels
  (fix: install Noto Sans CJK SC or run with `--lang en-US`)
- Truncated Y-axis on bar charts → visually inflated differences
  (fix: always set `ax.set_xlim(left=0)` for bar charts)
- Topic-only chart titles → no conclusion stated
  (fix: rephrase title as finding, e.g., "Terminal Value Represents 72% of DCF Value")
- Hardcoded palette colors → theming system bypassed
  (fix: all colors must come from `theme['palette']`)
- Missing source footnote → chart has no data provenance
  (fix: add `add_source_footnote(fig, theme, "Source: DCF valuation engine, [date]")`)
- Low DPI output → blurry in PDF
  (fix: ensure 300 DPI minimum; check `savefig.dpi` rcParam)

### Verdict thresholds

- **PASS:** All criteria met. Every chart rendered, CJK fonts working, no common
  mistakes. Chart-index.json is complete and valid.
- **REVISE:** Correctable issues: missing footnote, topic-only title, missing CJK
  font, truncated axis. Fix and re-render affected charts only.
- **BLOCK:** Fatal issues: input JSON unparseable, theme load failure, all charts
  broken. Halt pipeline; escalate to orchestrator with specific diagnosis.

### Self-check (run before submitting to review)

- [ ] All declared charts have SVG + PNG output
- [ ] CJK font detection succeeded (if applicable)
- [ ] Every chart has a conclusion-stating title
- [ ] Zero-baseline enforced on all bar-type charts
- [ ] No 3D, shadows, or rotated labels visible
- [ ] Source footnote present on every chart
- [ ] SVG output validates as XML
- [ ] chart-index.json is complete and paths resolve

---

## Prerequisites

```bash
pip install matplotlib pyyaml
# Optional: for PGF/XeLaTeX backend (CJK PDF)
# Windows: Install MiKTeX or TeX Live, then:
#   pip install matplotlib[pgf]
# macOS: brew install mactex
# Linux: apt install texlive-xetex texlive-lang-chinese
```

Font installation instructions per OS: see `fonts/README.md`.

## Files delivered

| File | Purpose |
|------|---------|
| `SKILL.md` | This specification |
| `scripts/charts.py` | CLI entry point (refactored) |
| `scripts/theme.py` | Theme loader + rcParams application |
| `scripts/cjk_fonts.py` | Cross-platform CJK font detection |
| `scripts/chart_utils.py` | Shared utilities (style_ax, save_fig, formatting) |
| `scripts/chart_montecarlo.py` | Monte Carlo histogram |
| `scripts/chart_breakeven.py` | Breakeven heatmap |
| `scripts/chart_terminal.py` | Terminal value donut |
| `scripts/chart_football.py` | Football field |
| `scripts/chart_tornado.py` | Sensitivity tornado |
| `scripts/chart_revenue_traj.py` | Revenue & margin trajectory (NEW) |
| `scripts/chart_roic_spread.py` | ROIC-WACC spread (NEW) |
| `scripts/chart_scenarios.py` | Scenario comparison (NEW) |
| `scripts/chart_price_vs_value.py` | Price vs value history (NEW) |
| `scripts/chart_waterfall.py` | Driver waterfall (NEW) |
| `scripts/chart_capex_cycle.py` | CAPEX cycle chart (NEW) |
| `scripts/chart_risk_matrix.py` | Risk matrix (NEW) |
| `themes/default.yaml` | Default finance theme |
| `themes/goldman.yaml` | Goldman Sachs theme |
| `themes/ms.yaml` | Morgan Stanley theme |
| `themes/cjk.yaml` | CJK-optimized overrides |
| `fonts/README.md` | Font installation instructions per OS |
| `tests/test_charts.py` | Chart rendering tests |
| `tests/test_theme.py` | Theme loading tests |
