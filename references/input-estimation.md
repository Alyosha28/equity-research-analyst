# Input Estimation: turning a story into defensible numbers

How to estimate each of the four value drivers (and the accounting adjustments
that come first) without hand-waving. Every number should be traceable to data
or an explicit, falsifiable judgment. When you assume, *say you are assuming* and
show the basis.

---

## 0. Accounting adjustments (do these BEFORE forecasting)

Reported financials misstate economic reality in predictable ways. Fix them first:

- **Capitalize R&D.** R&D is an investment, not an expense. Add current-year R&D
  back to operating income; subtract amortization of prior years' R&D
  (straight-line over a useful life — ~5 yrs software/chips, longer for pharma).
  Recompute operating margin and invested capital. Effect: higher, truer margins
  and a truer return on capital. (Raised NVIDIA's margin to a ~37.8% three-year
  pre-tax average.)
- **Capitalize operating leases** as debt (where not already under IFRS16/ASC842).
- **Normalize one-offs.** Strip non-recurring writedowns/gains; use a through-cycle
  margin for cyclical firms, not the peak or trough.
- **Treat SBC as a real cost.** Stock-based comp is an expense; account for
  dilution in the share count, don't add it back as "non-cash" and forget it.

---

## 1. Revenue growth — TAM × market share, bottom-up

Do **not** pick one growth rate and extrapolate. Instead:

1. **Segment the business** (NVIDIA: Data Center/AI, Gaming, Auto, ProViz).
2. For each segment, estimate the **Total Addressable Market** path and a
   **defensible market share** path. Revenue = Σ (TAM × share).
   - Anchor TAM to credible third-party sizing; show low/base/high.
   - Anchor share to current position + competitive dynamics. A *rising* share
     needs a reason (moat, capacity, switching costs).
3. **Decline growth over the horizon** toward the riskfree rate by the terminal
   year — scale brings the law of large numbers; nothing compounds at 50% forever.
4. **Sanity-check the absolute dollars.** A high % on a large base can imply the
   company must capture an implausible share of the entire market. (NVIDIA's story
   implied ~$267B revenue by 2033 — interrogate whether the markets are that big.)

Engine: `Segment` in `valuation_inputs.py` builds revenue from `tam_path` ×
`share_path`; `build_declining_growth()` shapes an aggregate declining path.

## 2. Target operating margin — R&D-adjusted, converging

- Use the **R&D-adjusted** margin (see §0), not the reported one.
- Set a **target** steady-state margin from: the firm's own best historical years,
  peer-group margins, and pricing power. Justify any premium to peers with the
  moat. (NVIDIA: 40% target vs 42.5% achieved in 2020 — a premium, but within its
  own history.)
- Specify the **convergence path**: how fast does today's margin reach the target?
- **Pricing power vs cost.** Note where margin gains must come from: a fabless
  firm (NVIDIA → TSMC) gets margin from price increases, not cost cuts.
- Caution on aggregate-margin stories: "if everyone adopts AI, no one keeps the
  surplus" — economy-wide efficiency gains often compete away into lower prices.

## 3. Reinvestment efficiency — sales-to-capital

- **Sales-to-capital** = revenue ÷ invested capital (incl. capitalized R&D). It
  says how many dollars of revenue each dollar of investment buys.
- Reinvestment in year *t* = (Revenue_t − Revenue_{t-1}) ÷ sales-to-capital.
- Estimate from the firm's history and the industry median; a capital-light path
  (higher ratio) means more value per growth dollar — justify it. (NVIDIA: 0.65
  historic → 1.15 industry median; the 75th percentile is ~1.94.)
- This driver is the discipline on growth: fast growth that needs heavy
  reinvestment creates far less value than the same growth done capital-efficiently.

## 4. Risk — cost of capital (+ failure)

- **Cost of capital** = blend of cost of equity (riskfree + β × equity risk
  premium, adjusted for geography) and after-tax cost of debt, weighted by
  market-value weights. Use the **industry/sector** cost of capital for the growth
  phase if the firm is young, then **glide to the mature market average** as it
  ages. (NVIDIA: 12.21% → 8.85%.)
- **Cyclicality keeps the cost of capital elevated** even for winners — don't
  under-risk a cyclical business in a boom.
- **Failure probability.** For firms with real distress risk, value =
  (1−p)×going-concern + p×distress value. Set p ≈ 0 for cash-rich incumbents;
  raise it for levered or single-product firms. Engine supports
  `failure_probability` / `failure_value_per_share`.

## Terminal value (where most of the value usually sits)

- **Stable growth ≤ riskfree rate.** No firm outgrows the economy forever.
- **Terminal cost of capital** = mature market average.
- **Terminal reinvestment** is pinned by the stable return on capital:
  reinvestment rate = g ÷ terminal ROC. A terminal ROC above the cost of capital
  asserts a *perpetual moat* — defensible only for the strongest franchises.
- **Always report the % of value in the terminal.** If >75% sits beyond the
  explicit horizon (NVIDIA: ~77%), say so — the valuation is really a bet on the
  terminal assumptions.

---

## Estimation discipline (checklist)

- [ ] Financials adjusted (R&D, leases, one-offs, SBC) before forecasting.
- [ ] Revenue built bottom-up (TAM × share), absolute dollars sanity-checked.
- [ ] Growth declines to ≤ riskfree by the terminal year.
- [ ] Margin target justified vs the firm's history and peers; convergence path stated.
- [ ] Sales-to-capital grounded in history/industry; reinvestment follows from it.
- [ ] Cost of capital reflects sector, geography, cyclicality; glides to mature.
- [ ] Terminal growth ≤ riskfree; terminal-value share of total reported.
- [ ] Every non-trivial input has a one-line justification and a low/base/high range.
