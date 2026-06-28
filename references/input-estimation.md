# Input Estimation: turning a story into defensible numbers

How to estimate each of the four value drivers (and the accounting adjustments
that come first) without hand-waving. Every number should be traceable to data
or an explicit, falsifiable judgment. When you assume, *say you are assuming* and
show the basis.

> **Data freshness:** The riskfree rate, ERP, country risk premiums, and industry
> cost-of-capital data change monthly to annually. **Never hardcode these values.**
> At the start of every valuation, fetch the current data from Damodaran's NYU
> Stern data page: `https://pages.stern.nyu.edu/~adamodar/New_Home_Page/data.html`.
> See `methodology-damodaran.md` §6 for the full data-fetch protocol and source URLs.

---

## 0. Accounting adjustments (do these BEFORE forecasting)

Reported financials misstate economic reality in predictable ways. Fix them first:

- **Capitalize R&D.** R&D is an investment, not an expense. Add current-year R&D
  back to operating income; subtract amortization of prior years' R&D
  (straight-line over a useful life — ~5 yrs software/chips, 8–10 yrs for pharma).
  Recompute operating margin and invested capital. Effect: higher, truer margins
  and a truer return on capital.
- **Capitalize operating leases** as debt (where not already under IFRS16/ASC842).
- **Normalize one-offs.** Strip non-recurring writedowns/gains; use a through-cycle
  margin for cyclical firms, not the peak or trough.
- **Treat SBC as a real cost.** Stock-based comp is an expense; account for
  dilution in the share count, don't add it back as "non-cash" and forget it.

---

## 1. Revenue growth — TAM × market share, bottom-up

Do **not** pick one growth rate and extrapolate. Instead:

1. **Segment the business** by product/market/geography.
2. For each segment, estimate the **Total Addressable Market** path and a
   **defensible market share** path. Revenue = Σ (TAM × share).
   - Anchor TAM to credible third-party sizing; show low/base/high.
   - Anchor share to current position + competitive dynamics. A *rising* share
     needs a reason (moat, capacity, switching costs).
3. **Decline growth over the horizon** toward the riskfree rate by the terminal
   year — scale brings the law of large numbers; nothing compounds at 50% forever.
4. **Sanity-check the absolute dollars.** A high % on a large base can imply the
   company must capture an implausible share of the entire market. Apply the
   **"Big Market Delusion" cross-check**: sum the implied breakeven revenues of
   all credible players in the TAM — if the total exceeds a plausible total market,
   the individual stories are collectively delusional.
5. **Life-cycle phase matters for growth shape.** See `methodology-lifecycle.md`:
   - Start-Up: growth is speculative; TAM is the input, share is a guess.
   - Young Growth/High Growth: growth declines from a high rate to the riskfree
     rate over the horizon (typically 10 years).
   - Mature Growth: growth converges from moderate to riskfree over a shorter
     horizon (5–7 years).
   - Mature Stable: growth already near riskfree; explicit horizon may be shorter.
   - Decline: growth is negative; explicit model of the decline path.

Engine: `Segment` in `valuation_inputs.py` builds revenue from `tam_path` ×
`share_path`; `build_declining_growth()` shapes an aggregate declining path.

---

## 2. Target operating margin — R&D-adjusted, converging

- Use the **R&D-adjusted** margin (see §0), not the reported one.
- Set a **target** steady-state margin from: the firm's own best historical years,
  peer-group margins, and pricing power. Justify any premium to peers with the
  moat.
- Specify the **convergence path**: how fast does today's margin reach the target?
- **Pricing power vs cost.** Note where margin gains must come from: a fabless
  firm gets margin from price increases, not cost cuts. A platform company gets
  it from operating leverage.
- Caution on aggregate-margin stories: "if everyone adopts AI, no one keeps the
  surplus" — economy-wide efficiency gains often compete away into lower prices.
- **Life-cycle phase matters for margin targets:**
  - Young Growth: current margin is negative; target is the steady-state margin
    of comparable mature companies in the same industry. The convergence path is
    the critical input — how long from here to there?
  - High Growth: margin expanding toward target; convergence typically over 3–7
    years.
  - Mature Growth: margin approaching or at target; convergence is shorter.
  - Mature Stable: margin at or near peak; no further expansion assumed.
  - Decline: margins compressing; model the compression explicitly — fixed costs
    spread over declining revenue means margin falls faster than revenue.

---

## 3. Reinvestment efficiency — sales-to-capital

- **Sales-to-capital** = revenue ÷ invested capital (incl. capitalized R&D). It
  says how many dollars of revenue each dollar of investment buys.
- Reinvestment in year *t* = (Revenue_t − Revenue_{t-1}) ÷ sales-to-capital.
- Estimate from the firm's history and the industry median; a capital-light path
  (higher ratio) means more value per growth dollar — justify it.
- This driver is the discipline on growth: fast growth that needs heavy
  reinvestment creates far less value than the same growth done capital-efficiently.
- **Life-cycle phase matters:**
  - Young Growth/High Growth: reinvestment is heavy; sales-to-capital may be
    below the industry median as the company builds capacity.
  - Mature Growth: sales-to-capital converges to the industry median.
  - Mature Stable: reinvestment is minimal; growth is organic and capital-light.
  - Decline: negative reinvestment (divesting); sales-to-capital is mostly
    irrelevant — focus on asset liquidation value instead.

---

## 4. Risk — cost of capital (+ failure + optional overlays)

### 4.1 Base cost of capital

The cost of capital = weighted blend of cost of equity and after-tax cost of debt,
at market-value weights.

**Cost of equity** = riskfree rate + β × ERP + country risk premium (if applicable).

**Step-by-step estimation protocol:**

1. **Riskfree rate.** Use the current 10-year government bond yield for the
   currency of the cash flows. If the sovereign's bonds carry default risk (i.e.,
   the sovereign is rated below Aaa), subtract the sovereign default spread to
   arrive at a true riskfree rate. *Example: US 10-year T-bond at 4.24% minus
   0.27% Aa1 default spread = 3.97% riskfree (as of Damodaran's July 2025
   methodology).*

2. **Equity risk premium (ERP).** Use Damodaran's **implied ERP** — the
   forward-looking premium backed out from current S&P 500 prices and expected
   cash flows. **Do NOT use a hardcoded historical average** (though the 1928–2024
   average of ~5.5% may be noted for comparison). The implied ERP changes monthly;
   fetch the current value from Damodaran's data page. *Reference: Jan 2026 implied
   ERP was 4.23% (trailing 12-month); the 17th annual ERP study (March 2026, SSRN
   #6361419) formalized this methodology in 154 pages.*

3. **Beta.** Use Damodaran's industry betas (`betas.xls` on his data page).
   Prefer **bottom-up betas** (unlevered industry beta, re-levered to the
   company's target debt ratio) over regression betas. For young companies with
   limited trading history, use the industry average unlevered beta or a total
   beta (which incorporates the correlation with the market).

4. **Country risk premium (if applicable).** For companies with significant
   non-US operations, add a country-specific risk premium to the ERP for those
   revenue streams. Country risk follows *operations, not incorporation* — a
   US-domiciled company with Brazilian operations should use Brazil's ERP for
   those cash flows. Fetch current country risk premiums from Damodaran's
   `ctryprem.xlsx` (January data) or the most recent mid-year update. *Reference:
   July 2025 update covers ~140+ countries; mature market (Aaa) premium 4.21%;
   India 7.46%; Turkey 10.87%.*

5. **Cost of capital glide path.** Use the **industry/sector** cost of capital
   for the growth phase if the firm is young, then **glide to the mature market
   average** as it ages. The glide timing is informed by the life-cycle phase:
   - Start-Up/Young Growth: hold at elevated sector CoC; begin gliding as the
     company enters High Growth.
   - High Growth: begin glide toward mature CoC; complete by the terminal year.
   - Mature Growth: shorter glide; CoC approaches mature average sooner.
   - Mature Stable/Decline: mature market average throughout.

### 4.2 Failure probability

For firms with real distress risk, value = (1−p)×going-concern + p×distress value.
Set p ≈ 0 for cash-rich incumbents; raise it for levered or single-product firms.
Engine supports `failure_probability` / `failure_value_per_share`.

- Start-Up: p = 50–90% (most start-ups fail)
- Young Growth: p = 20–50% (business model not yet proven; chance of running out
  of cash)
- High Growth and beyond: p ≈ 0–10% (business model established; distress only
  from excess leverage or catastrophic disruption)

### 4.3 Trust-deficit / institutional-risk overlay (optional)

Damodaran's "Data Update 3 for 2026: The Trust Deficit" (Jan 28, 2026 blog post)
introduced a framework for assessing institutional trust as a risk factor. When
active, it justifies an additional premium on the cost of capital.

**When to apply:**
Evaluate the following signals at each valuation date. If 3+ signals are active,
add a **trust-deficit premium of 0.25–1.00%** to the cost of equity:

| Signal | What it measures | Current context (as of early 2026) |
|--------|-----------------|-------------------------------------|
| Sovereign credit downgrade | Institutional creditworthiness | US downgraded to Aa1 by Moody's (May 2025); last major agency to downgrade |
| USD trade-weighted index decline | Global confidence in US institutions | USD down −7.24% in 2025 |
| Gold price surge beyond CPI-scaled fair value | Flight to hard assets (distrust of fiat/central banks) | Gold up +65% in 2025; silver +148% |
| Central bank independence challenge | Monetary policy credibility | Questions over Fed independence emerged in 2025 |
| Extended government dysfunction | Governance functionality | Longest US government shutdown in history (Oct–Nov 2025) |
| Bond market shows stress | Sovereign default risk perception | US CDS spreads dropped in 2025 — bond market *did not* stress; this signal is currently NOT active |

**How to apply:**
- Add the premium as a **named, separate line item** in the cost of equity
  calculation. Do not silently fold it into the ERP — it must be visible and
  falsifiable.
- The premium should be higher (0.50–1.00%) for companies directly exposed to
  institutional stability: financials, regulated utilities, sovereign-linked
  businesses, and companies operating in countries with weak institutions.
- The premium should be lower (0–0.25%) for companies whose value is driven by
  global demand for non-sovereign-substitute goods.
- **Re-evaluate at each valuation date.** The trust deficit is a market-state
  variable, not a permanent company characteristic. Remove the overlay when
  signals recede.

**Rationale:** The ERP already embeds some institutional risk, but when multiple
signals fire simultaneously, the market may not be pricing all channels of
institutional erosion. A named overlay makes the reasoning explicit and lets the
reader agree or disagree with a specific, quantified judgment.

### 4.4 Cyclicality

Cyclicality keeps the cost of capital elevated even for winners — don't under-risk
a cyclical business in a boom. Use through-cycle (normalized) cost of capital, not
the trough cost.

---

## Terminal value (where most of the value usually sits)

- **Stable growth ≤ riskfree rate.** No firm outgrows the economy forever.
- **Terminal cost of capital** = mature market average.
- **Terminal reinvestment** is pinned by the stable return on capital:
  reinvestment rate = g ÷ terminal ROC. A terminal ROC above the cost of capital
  asserts a *perpetual moat* — defensible only for the strongest franchises.
- **Always report the % of value in the terminal.** If >75% sits beyond the
  explicit horizon, say so — the valuation is really a bet on the terminal
  assumptions.
- **Life-cycle phase matters for terminal structure:**
  - Start-Up/Young Growth: terminal value may be >100% of operating value
    (explicit-period FCFF is negative). The terminal is a bet on the *existence*
    of a viable business — use probability-weighting or a failure branch.
  - High Growth: terminal value is 60–80%. It is a bet on *durability* — how long
    can above-average returns persist?
  - Mature Growth/Mature Stable: terminal value is 70–85%. It is a bet on
    *perpetual moat* — does the terminal ROC > CoC assumption hold?
  - Decline: terminal value may be a **liquidation value**, not a going-concern
    terminal. Cross-check with price/book.

---

## Estimation discipline (checklist)

- [ ] Financials adjusted (R&D, leases, one-offs, SBC) before forecasting.
- [ ] Revenue built bottom-up (TAM × share), absolute dollars sanity-checked.
- [ ] "Big Market Delusion" cross-check applied.
- [ ] Growth declines to ≤ riskfree by the terminal year.
- [ ] Margin target justified vs the firm's history and peers; convergence path stated.
- [ ] Sales-to-capital grounded in history/industry; reinvestment follows from it.
- [ ] Cost of capital uses **current implied ERP** (fetched from Damodaran's data page), not a hardcoded number.
- [ ] Country risk premium applied where operations warrant it (fetched from current data).
- [ ] Riskfree rate adjusted for sovereign default spread if the sovereign is not Aaa-rated.
- [ ] Trust-deficit / institutional-risk overlay evaluated and documented (or explicitly declined with reason).
- [ ] Cost of capital glide reflects the life-cycle phase.
- [ ] Failure probability assessed and documented.
- [ ] Terminal growth ≤ riskfree; terminal-value share of total reported.
- [ ] Every non-trivial input has a one-line justification and a low/base/high range.
- [ ] All market data (riskfree, ERP, CRP, betas) carries the date it was fetched.
