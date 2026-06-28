# Methodology: Damodaran's "Story → Numbers → Value"

This is the backbone of the skill, distilled from Aswath Damodaran's valuation
framework and continuously updated. The core belief: **a valuation is a story
disciplined by numbers**. A story without numbers is a fairy tale; numbers without
a story are a spreadsheet nobody believes. Every input must trace back to a
narrative, and the narrative must be *possible, plausible, and probable*.

> **Primary sources (current):** Damodaran's *Musings on Markets* blog (ongoing);
> *The Corporate Life Cycle* book (Aug 2024, Portfolio/Penguin); 17th annual ERP
> study (March 2026, SSRN #6361419); January 2026 data update; July 2025 country
> risk update; "Data Update 3 for 2026: The Trust Deficit" (Jan 28, 2026). The
> worked NVIDIA example used in the 2023 blog post remains a pedagogical
> illustration of method, not a source of current numbers. **All market data
> (riskfree rate, ERP, country risk premiums, industry betas/cost-of-capital)
> must be fetched from Damodaran's current data page at the time of each
> valuation.** See §6 "Data freshness protocol" below.

> Damodaran's data page: `https://pages.stern.nyu.edu/~adamodar/New_Home_Page/data.html`

---

## Table of contents
1. The six-layer structure (the order he reasons in)
2. The four value drivers (the numbers the story must feed)
3. The life-cycle lens (overlay from the 2024 book)
4. Signature moves (the techniques that make it rigorous)
5. The decision layer (value → action)
6. Data freshness protocol (living data, not hardcoded numbers)
7. How the layers map to the engine scripts

---

## 1. The six-layer structure

Damodaran reasons **top-down**, narrowing from the macro field to a single
share price. Reproduce this order for any company:

| # | Layer | What he establishes | Questions to answer |
|---|-------|--------------------|--------------------|
| 1 | **Industry / macro** | The business's life-cycle stage, profitability cycle, market-cap/revenue history, and how winners/losers rotate. | Is the sector growing or maturing? Cyclical? Where do margins sit and why? Who leads and why does leadership change? |
| 2 | **Company narrative** | The firm's history, business model, competitive position, and the *risks embedded in the model*. | How does it actually make money? What is the moat? What structural risk comes with the model (e.g., NVIDIA's fabless reliance on TSMC → margin upside but Taiwan supply-chain risk)? |
| 3 | **Thematic / disruption** | The big driver. Is the change *revolutionary or incremental*? Break the ecosystem into layers and locate the company. | Where in the value chain does the company sit (hardware / software / data / applications)? How big is the addressable market and how fast does it grow? Does "everyone has it → no one does" erode the margin? |
| 4 | **Story → numbers (DCF)** | Translate the narrative into the four value drivers and run an intrinsic DCF. | What revenue, margin, reinvestment efficiency, and risk does the story imply? |
| 5 | **Uncertainty** | Convert point estimates into a *distribution* via Monte Carlo, and a *breakeven* table for "what has to be true". | How wide is the value range? Where does the current price sit in that range? |
| 6 | **Decision** | Compare value to price, separate investing from trading, and act. | Buy / hold / sell? What would change the thesis? |

**Why the order matters:** the macro and company layers are where the *judgment*
lives. By the time you reach the DCF, every number should already be defensible
from the story above it. Analysts who skip to the spreadsheet produce precise
answers to the wrong question.

---

## 2. The four value drivers

Damodaran reduces intrinsic value to four inputs. Everything in layers 1–3 exists
to justify these four numbers:

1. **Revenue growth** — the proxy for growth potential. Built **bottom-up by
   segment** as *Total Addressable Market × market share*. Growth declines over
   the horizon toward the riskfree rate.
2. **Target operating margin** — the proxy for profitability. Use the
   **R&D-adjusted** margin (see signature moves). Justify against the firm's
   history and peer group.
3. **Reinvestment efficiency** — measured by **sales-to-capital** ($ of revenue
   per $ of capital invested). Reinvestment = ΔRevenue ÷ sales-to-capital. Ground
   in the firm's history and industry median.
4. **Risk** — the **cost of capital** plus an optional **failure probability**.
   The cost of capital = riskfree rate + β × ERP + country/geography adjustments.
   See `input-estimation.md` §4 for the full estimation protocol including
   the current implied ERP approach, country risk premiums, and the optional
   trust-deficit / institutional-risk overlay.

FCFF = After-tax operating income − Reinvestment. Discount at the cost of
capital; add a terminal value at stable growth (≤ riskfree rate). See
`input-estimation.md` for how to estimate each driver defensibly.

---

## 3. The life-cycle lens

Damodaran's 2024 book *The Corporate Life Cycle* (576 pages, Portfolio/Penguin,
August 2024) introduced a refined 6-phase framework. Every valuation must
explicitly consider the company's life-cycle phase because the phase determines:

- **Narrative emphasis** (what the story is about — market size vs. moat defense
  vs. capital return)
- **Which drivers are most sensitive** (revenue growth dominates for young
  companies; terminal assumptions dominate for mature ones)
- **The appropriate valuation metrics** (EV/revenue for high growth; P/E for
  mature stable; price/book for decline)
- **The financing and dividend assumptions** (all equity → debt capacity →
  returning cash → paying down debt)

The six phases are:

| Phase | Growth profile | Narrative emphasis | Valuation priority |
|-------|---------------|-------------------|-------------------|
| Start-Up | Zero revenue; idea stage | Can this idea become a business? | TAM × probability of success; cash runway |
| Young Growth | Scaling from tiny base; negative margins | Will the business model work at scale? | Revenue path; margin glide to positive; failure branch |
| High Growth | 30%+ revenue growth; margins turning positive | How big can this get? | TAM × share; growth deceleration; margin expansion |
| Mature Growth | 5–30% growth; positive margins expanding | How long can the moat defend above-average returns? | Competitive advantage period; margin durability |
| Mature Stable | 0–5% growth; stable margins; strong FCF | How will value be preserved? | Terminal value; capital allocation; payout |
| Decline | Negative growth; compressing margins | How fast does it shrink and what's the floor? | Liquidation value; pace of decline; debt paydown |

**Full detail in `references/methodology-lifecycle.md`.** The classification
step (`skills/classify-archetype/SKILL.md`) now produces both a business-model
archetype AND a life-cycle phase. Both feed the driver estimates and the
narrative structure of the report.

---

## 4. Signature moves (what makes it rigorous, not hand-waving)

These recur in every Damodaran valuation and are encoded in the engine:

- **Capitalize R&D.** Treating R&D as an operating expense understates margins
  and capital. Add back current-year R&D, subtract amortization of prior years'
  R&D (straight-line over its useful life, ~5 yrs for chips/software, longer for
  pharma). Apply the same to leases. → *adjust the financials before you forecast
  them.*
- **Build revenue bottom-up: TAM × share.** Don't extrapolate a single growth
  rate. Size each market and assign a defensible share, segment by segment. This
  forces the story to confront the size of the prize.
- **Converge to the mean.** High margins, low cost of capital, and reinvestment
  efficiency all drift toward industry/market norms over the horizon. Excess
  returns fade unless a moat justifies otherwise. Terminal growth ≤ riskfree rate
  (a company cannot outgrow the economy forever).
- **Quantify uncertainty; don't hide behind it.** "Too much uncertainty" is not a
  reason to skip the estimate — it's the reason to *simulate* it. Monte Carlo over
  the drivers → a value distribution. Breakeven table → "what has to be true".
- **Value drives action via the price gap.** Intrinsic value is only useful
  relative to price. The output is a *decision*, not a number.
- **Use the implied ERP, not a historical average.** Damodaran's forward-looking
  implied ERP (backed out from current S&P 500 prices and expected cash flows) is
  the most relevant signal for current valuations. Historical averages lag and can
  misrepresent the current risk environment. See §6 below.
- **Be honest about your own biases.** Damodaran opens by disclosing he owns the
  stock and got lucky. Name your priors; they leak into your inputs.

---

## 5. The decision layer

- **Investing vs trading.** Investing closes the gap between price and *value*;
  trading rides the gap between price and a *higher future price* (momentum),
  agnostic to value. Decide which game you're playing — they need different tools.
- **Act on the gap, but allow pragmatism.** Value < price → sell discipline.
  Damodaran sold *half* and kept half for optionality — purist logic, pragmatic
  execution. State the rule, then state any deviation and why.
- **Robustness over precision.** The conclusion should hold across the simulation
  and breakeven. A thesis that flips on a 2% margin tweak isn't a thesis. Stress
  the conclusion, not just the point estimate.

Three closing lessons (the "bottom line"):
1. Getting the macro story right ≠ making money — you must pick the right company.
2. Refusing to estimate doesn't remove uncertainty; it just lets arbitrary
   premiums fill the vacuum.
3. Even great companies have near-death drawdowns (NVIDIA fell >50% in 2002, 2008,
   2018) — which is when value investors get their entry.

---

## 6. Data freshness protocol

**CRITICAL: Never hardcode the riskfree rate, ERP, country risk premiums, or
industry cost-of-capital data. These numbers change monthly (implied ERP) and
annually (full data library). Every valuation must use the most current data
available from Damodaran's NYU Stern data page.**

### Data sources (all at `https://pages.stern.nyu.edu/~adamodar/`)

| Data item | Update frequency | Source URL / file | Notes |
|-----------|-----------------|-------------------|-------|
| **US implied ERP** | Monthly (around the 1st) | `pc/datasets/histimpl.xls` | Forward-looking ERP backed out from S&P 500 + consensus cash flows. Current (Jan 2026): **4.23%** (trailing 12-month basis). 17th annual study (March 2026, SSRN #6361419) formalized the methodology. |
| **Country risk premiums** | Annually (January, with mid-year updates) | `pc/datasets/ctryprem.xlsx` | Based on Moody's sovereign ratings. July 2025 methodology change: US downgrade to Aa1 means the US ERP (4.48% as of June 2025) is now separate from the mature-market (Aaa) premium (4.21%). ~140+ countries covered. |
| **Industry betas** | Annually (January) | `pc/datasets/betas.xls` | Levered/unlevered betas by industry (US, Europe, Japan, Emerging Markets, Global). |
| **Industry cost of capital** | Annually (January) | `pc/datasets/wacc.xls` | Cost of capital by industry (US and global). |
| **Riskfree rate** | Current market | US 10-year Treasury yield (or equivalent government bond for non-US markets). Adjust for sovereign default spread if the sovereign is not Aaa-rated. |
| **ERP (historical)** | Annually | `pc/datasets/histretSP.xls` | For reference/comparison only. The historical average (1928–2024: ~5.5%) is NOT recommended as the primary ERP input — use the implied ERP. |

### Data-fetch procedure (to be run at the start of every Mode A valuation)

1. **Fetch the latest implied ERP** from Damodaran's data page. The current value
   is typically found in the "Risk/Discount Rate" section of `datacurrent.html`
   with a link to `histimpl.xls`. WebFetch: the HTML view at
   `https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/histimpl.html`
   displays the most recent ERP figure.

2. **Fetch country risk premiums** from the latest `ctryprem.xlsx` (January data)
   or `ctrypremJuly25.xlsx` (mid-year update). For companies with significant
   non-US operations, apply country-specific ERPs to those revenue streams (country
   risk follows operations, not incorporation).

3. **Fetch industry betas and cost of capital** from `betas.xls` and `wacc.xls`.
   Use the **unlevered beta** for the company's industry, then re-lever to the
   company's target debt ratio. Bottom-up betas are preferred over regression betas.

4. **Use the current riskfree rate** from the market (US 10-year Treasury yield
   or equivalent). If the sovereign has a non-trivial default spread (as the US
   does since Moody's May 2025 downgrade to Aa1), subtract the default spread to
   arrive at a true riskfree rate. Damodaran's July 2025 methodology: US riskfree
   = 4.24% (T-bond) − 0.27% (Aa1 default spread) = 3.97%.

5. **Record all data sources and dates** in the assumptions file. A valuation
   without dates is not reproducible.

### The implied ERP approach (forward-looking, preferred)

Damodaran's implied ERP is the preferred risk premium input. The methodology:

1. Treat the S&P 500 like a stock with observable expected cash flows (consensus
   estimates for dividends + buybacks, declining over a two-stage model).
2. Find the discount rate that equates the present value of those cash flows to
   the current index level.
3. Subtract the riskfree rate — the remainder is the implied ERP.

This is forward-looking (embedded in current prices), avoids historical-average
anchoring, and updates with market conditions. The 17th annual study (March 2026)
formalized this as the primary ERP estimation approach.

**Key ERP reference points:**
- Q1 2026 implied ERP: ~3.2% (bottom quartile of post-1960 distribution)
- Jan 2026 implied ERP (trailing 12-month): 4.23%
- Mid-2025 implied ERP (after US downgrade): 4.48%
- Long-run historical ERP (1928–2024): 5.5%
- Peak ERP (March 2009 trough): 8.4%
- Trough ERP (1999 dot-com peak): 2.1%

The ERP is **NOT a constant**. It moves with equity markets, risk appetite, and
macro conditions. The 2026 edition of Damodaran's ERP study (154 pages, SSRN
#6361419) argues that using a static "normalized" ERP is a common valuation error.

### Trust-deficit / institutional-risk overlay (optional, from Jan 2026 blog)

Damodaran's "Data Update 3 for 2026: The Trust Deficit" (Jan 28, 2026 blog post)
introduced a framework for assessing **institutional trust as a risk factor**.
Key signals of a trust deficit that may warrant a risk premium overlay:

| Signal | What it measures | Threshold for concern |
|--------|-----------------|----------------------|
| Sovereign credit downgrade | Institutional creditworthiness | Any downgrade from Aaa |
| USD trade-weighted index decline | Global confidence in US institutions | Sustained >5% annual decline |
| Gold price surge | Flight to hard assets (distrust of fiat/central banks) | >30% annual increase; divergence from CPI-scaled fair value |
| Central bank independence challenge | Monetary policy credibility | Political pressure on rate decisions; Fed seen as "extension of government" |
| Government shutdown duration | Governance functionality | Extended shutdowns (>2 weeks) |

If multiple signals are active, consider adding a **trust-deficit premium** of
0.25–1.00% to the cost of capital for companies whose operations or valuation
are sensitive to institutional stability (financials, regulated utilities,
sovereign-linked businesses, and companies in countries with weak institutions).
Document this as a named, separate overlay so it can be debated and adjusted.

> The trust-deficit overlay is NOT a permanent fixture — it should be evaluated
> fresh at each valuation date and removed when the signals recede. The key
> insight from Damodaran's framework: the market is not a monolith. Bond markets
> may shrug off institutional risk while currency and gold markets price it
> aggressively. The equity risk premium already embeds some of this, but a
> specific overlay makes the reasoning explicit and falsifiable.

---

## 7. How the layers map to the engine

| Layer / driver | Script |
|---|---|
| Story → numbers DCF (drivers 1–4) | `scripts/dcf_valuation.py` |
| Life-cycle phase calibration | `skills/classify-archetype/SKILL.md` → phase informs driver ranges, convergence timing, and terminal structure |
| Uncertainty → distribution | `scripts/monte_carlo.py` |
| "What has to be true" | `scripts/breakeven.py` |
| "What's priced in" (expectations) | `scripts/reverse_dcf.py` |
| Relative cross-check | `scripts/comps.py` |
| Immutable assumptions model | `scripts/valuation_inputs.py` |
| SOTP (holding companies) | `scripts/sotp.py` |
| Financials valuation | `scripts/financial_valuation.py` |

**Reference valuation ranges** (illustrative, from Damodaran's NVIDIA work — NOT
current; always use live data and company-specific inputs):
- The worked NVIDIA example (`templates/assumptions.example.json`) reproduces
  Damodaran's 2023 method end-to-end and serves as a structural template. The
  *numbers* in that example date to June 2023 — the *method* is timeless.

---

## Related methodology documents

- `methodology-lifecycle.md` — The 6-phase corporate life cycle framework (2024 book)
- `input-estimation.md` — How to estimate each value driver, with current ERP protocol
- `analyst-playbook.md` — How top-tier research operationalizes each lens
- `valuation-lenses.md` — The four valuation lenses and triangulation rules
