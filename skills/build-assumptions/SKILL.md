---
name: equity-research-analyst/build-assumptions
description: >
  Translate the story into the four value drivers with accounting adjustments.
  Produces a complete assumptions.json file for the Python engine. Step 5 of Mode A.
  Consumes industry, company, and theme analyses.
license: MIT
---

# Build Assumptions

**Pipeline position:** STEP 5 of Mode A. This is the critical translation step —
story becomes numbers. Consumes steps 2 (industry), 3 (company), 4 (theme).
Produces the `assumptions.json` that the engine runs on.

## Input
- Industry analysis (step 2)
- Company analysis (step 3)
- Theme/TAM/competitive analysis (step 4)
- Archetype classification (step 1) — determines which drivers are needed

## What you produce

1. **Accounting adjustments** — R&D capitalization, lease capitalization, one-off
   normalization, SBC treatment — computed with actual numbers, not described
2. **The four drivers** (or archetype-specific equivalents) — each with basis,
   low/base/high range, and convergence path
3. **A complete `assumptions.json` file** — written to disk, ready for engine execution
4. **An assumptions narrative** — prose that explains every material input

### Accounting adjustments (NON-NEGOTIABLE — do these FIRST)

Before forecasting, adjust the historical financials:

- **Capitalize R&D.** Add current-year R&D back to operating income; amortize prior
  years' R&D over an appropriate life (5 yrs for software/chips, 8–10 for pharma).
  Recompute operating margin and invested capital on the adjusted basis.
  *This typically raises margins by 2–5pp and changes ROIC meaningfully.*
  Output: R&D-adjusted historical margin, R&D-adjusted ROIC.
- **Capitalize operating leases** as debt (if not already under IFRS 16 / ASC 842).
- **Normalize one-offs.** Strip non-recurring items; for cyclicals, use through-cycle
  average margins, not peak or trough.
- **Treat SBC as a real cost.** Count dilution in share count; do NOT add back as
  "non-cash" and ignore. State the annual dilution rate over the past 5 years.

### The four drivers (Default archetype)

For each driver, produce: **current value → target value → convergence path → basis
→ low/base/high range.**

1. **Revenue growth** — from the theme step's TAM × share build
   - Segment-by-segment, declining toward riskfree rate by year 10
   - Stated as an annual growth path, not a single rate
   - Two-way reconciliation: top-down TAM×share vs bottom-up units×ASP

2. **Target operating margin** — R&D-adjusted
   - Justified against: firm's own best historical years, peer-group margins, moat
   - Convergence year stated (how fast from current to target)
   - Premium to peers requires moat justification

3. **Reinvestment efficiency (sales-to-capital)**
   - Grounded in firm's history and industry median
   - Reinvestment = ΔRevenue ÷ sales-to-capital
   - Capital-light path requires justification

4. **Cost of capital**
   - Riskfree rate + β × ERP + country/geography adjustments
   - Initial at sector average, glides to mature market average
   - For financials: cost of equity only (Ke)
   - For young companies: consider failure probability

### Assumptions.json structure

```json
{
  "_company": "NVIDIA Corporation",
  "_ticker": "NVDA",
  "_valuation_date": "2023-06-10",
  "_archetype": "default",

  "shares_outstanding": 2470,
  "cash_and_equivalents": 15320,
  "total_debt": 10952,
  "minority_interests": 0,
  "cross_holdings": 0,
  "effective_tax_rate": 0.15,

  "current_revenue": 26914,
  "current_rd_adj_operating_margin": 0.378,
  "sales_to_capital": 0.65,

  "segments": [
    {"name": "Data Center / AI", "tam_path": [15000, 200000], "share_path": [0.80, 0.35]}
  ],

  "target_rd_adj_operating_margin": 0.40,
  "margin_convergence_year": 5,

  "initial_cost_of_capital": 0.1221,
  "terminal_cost_of_capital": 0.0885,
  "cost_of_capital_glide_start": 5,
  "cost_of_capital_glide_end": 10,

  "terminal_growth": 0.03,
  "terminal_roc": 0.12,

  "failure_probability": 0.0,
  "failure_value_per_share": 0
}
```

For other archetypes, use the appropriate template from `templates/`:
- Financials → `templates/financials.example.json`
- Cyclical → `templates/cyclical.freeport.json`
- Young → `templates/young.example.json`
- Mature → `templates/mature.example.json`
- Holding-co → `templates/tencent.sotp.json`

## Output

1. Write the assumptions JSON file to disk (name it after the ticker: `TICKER_assumptions.json`)
2. Produce an assumptions narrative (~500 words) explaining each driver's basis,
   the accounting adjustments made, and the key judgment calls

## Integration notes
- Feeds directly into `/run-valuation` (step 6)
- The input-estimation methodology is in `references/input-estimation.md`
- Template files in `templates/` show the exact JSON structure expected
- The assumptions narrative is used verbatim in the report's "Story → numbers" section

## Self-check
- [ ] Accounting adjustments done BEFORE forecasting (R&D, leases, one-offs, SBC)
- [ ] Revenue built bottom-up by segment, growth declines to ≤ riskfree
- [ ] Margin target justified vs history and peers
- [ ] Sales-to-capital grounded in history
- [ ] Cost of capital reflects sector, geography, cyclicality
- [ ] Every non-trivial input has a one-line basis and a low/base/high range
- [ ] JSON is valid and matches the archetype's template structure
- [ ] Quick sanity: run `python scripts/dcf_valuation.py TICKER_assumptions.json` —
    does it produce a positive, non-absurd value?
