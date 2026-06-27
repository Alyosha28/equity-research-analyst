# Methodology: Damodaran's "Story → Numbers → Value"

This is the backbone of the skill, distilled from Aswath Damodaran's NVIDIA
valuation (*Musings on Markets*, 23 Jun 2023). The core belief: **a valuation is
a story disciplined by numbers**. A story without numbers is a fairy tale; numbers
without a story are a spreadsheet nobody believes. Every input must trace back to
a narrative, and the narrative must be *possible, plausible, and probable*.

> Source: https://aswathdamodaran.blogspot.com/2023/06/ais-winners-losers-and-wannabes-nvidia.html

---

## Table of contents
1. The six-layer structure (the order he reasons in)
2. The four value drivers (the numbers the story must feed)
3. Signature moves (the techniques that make it rigorous)
4. The decision layer (value → action)
5. How the layers map to the engine scripts

---

## 1. The six-layer structure

Damodaran reasons **top-down**, narrowing from the macro field to a single
share price. Reproduce this order for any company:

| # | Layer | What he establishes | Questions to answer |
|---|-------|--------------------|--------------------|
| 1 | **Industry / macro** | The business's life-cycle stage, profitability cycle, market-cap/revenue history, and how winners/losers rotate. | Is the sector growing or maturing? Cyclical? Where do margins sit and why? Who leads and why does leadership change? |
| 2 | **Company narrative** | The firm's history, business model, competitive position, and the *risks embedded in the model*. | How does it actually make money? What is the moat? What structural risk comes with the model (e.g., NVIDIA's fabless reliance on TSMC → margin upside but Taiwan supply-chain risk)? |
| 3 | **Thematic / disruption** | The big driver (here: AI). Is the change *revolutionary or incremental*? Break the ecosystem into layers and locate the company. | Where in the value chain does the company sit (hardware / software / data / applications)? How big is the addressable market and how fast does it grow? Does "everyone has it → no one does" erode the margin? |
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
   segment** as *Total Addressable Market × market share* (NVIDIA: AI chips +
   Auto + Gaming). Growth declines over the horizon toward the riskfree rate.
2. **Target operating margin** — the proxy for profitability. Use the
   **R&D-adjusted** margin (see signature moves). NVIDIA target: 40% by 2027.
3. **Reinvestment efficiency** — measured by **sales-to-capital** ($ of revenue
   per $ of capital invested). NVIDIA: rising from a historic 0.65 to the
   industry median 1.15. Reinvestment = ΔRevenue ÷ sales-to-capital.
4. **Risk** — the **cost of capital** plus an optional **failure probability**.
   NVIDIA: 12.21% (US semiconductor average) in the growth phase, gliding to the
   mature market average 8.85%.

FCFF = After-tax operating income − Reinvestment. Discount at the cost of
capital; add a terminal value at stable growth (≤ riskfree rate). See
`input-estimation.md` for how to estimate each driver defensibly.

---

## 3. Signature moves (what makes it rigorous, not hand-waving)

These recur in every Damodaran valuation and are encoded in the engine:

- **Capitalize R&D.** Treating R&D as an operating expense understates margins
  and capital. Add back current-year R&D, subtract amortization of prior years'
  R&D (straight-line over its useful life, ~5 yrs for chips). This raised
  semiconductor margins ~2–4%. Apply the same to leases. → *adjust the financials
  before you forecast them.*
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
- **Be honest about your own biases.** Damodaran opens by disclosing he owns the
  stock and got lucky. Name your priors; they leak into your inputs.

---

## 4. The decision layer

- **Investing vs trading.** Investing closes the gap between price and *value*;
  trading rides the gap between price and a *higher future price* (momentum),
  agnostic to value. Decide which game you're playing — they need different tools.
- **Act on the gap, but allow pragmatism.** Value < price → sell discipline.
  Damodaran sold *half* and kept half for optionality — purist logic, pragmatic
  execution. State the rule, then state any deviation and why.
- **Robustness over precision.** The conclusion ("overvalued") held across the
  simulation and breakeven. A thesis that flips on a 2% margin tweak isn't a
  thesis. Stress the conclusion, not just the point estimate.

Three closing lessons (the "bottom line"):
1. Getting the macro story right ≠ making money — you must pick the right company.
2. Refusing to estimate doesn't remove uncertainty; it just lets arbitrary
   premiums fill the vacuum.
3. Even great companies have near-death drawdowns (NVIDIA fell >50% in 2002, 2008,
   2018) — which is when value investors get their entry.

---

## 5. How the layers map to the engine

| Layer / driver | Script |
|---|---|
| Story → numbers DCF (drivers 1–4) | `scripts/dcf_valuation.py` |
| Uncertainty → distribution | `scripts/monte_carlo.py` |
| "What has to be true" | `scripts/breakeven.py` |
| "What's priced in" (expectations) | `scripts/reverse_dcf.py` |
| Relative cross-check | `scripts/comps.py` |
| Immutable assumptions model | `scripts/valuation_inputs.py` |

The worked NVIDIA example (`templates/assumptions.example.json`) reproduces this
methodology end-to-end: intrinsic ≈ $236 vs the $409 price, with the price at the
~94th percentile of the simulated value distribution — Damodaran's exact finding.
