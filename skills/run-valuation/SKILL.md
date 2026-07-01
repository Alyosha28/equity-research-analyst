---
name: equity-research-analyst/run-valuation
description: >
  Execute the Python valuation engine suite on the assumptions file: DCF, Monte Carlo,
  breakeven, reverse DCF, comps, and (if applicable) SOTP or financials. Produces all
  numerical outputs for the report. Step 6 of Mode A.
license: MIT
---

# Run Valuation

**Pipeline position:** STEP 6 of Mode A. Consumes the `assumptions.json` from step 5.
Runs the full engine suite and collects all numerical outputs.

## Input
- `assumptions.json` from step 5 (path to file)
- `cyclical_inputs.json` from step 5 when archetype is Cyclical
- Current stock price (for Monte Carlo percentile, breakeven, reverse DCF)
- Archetype from step 1 (determines which scripts to run)

## Engine execution matrix

| Archetype | Scripts to run | Outputs |
|-----------|---------------|---------|
| Default | `dcf_valuation.py`, `monte_carlo.py`, `breakeven.py`, `reverse_dcf.py`, `comps.py` | value/share, distribution, breakeven grid, implied expectations |
| Financials | `financial_valuation.py`, `comps.py` | RIM value, DDM cross-check, implied P/B |
| Cyclical | `dcf_valuation.py`, `monte_carlo.py`, `breakeven.py`, `reverse_dcf.py`, `cyclical_valuation.py` | normalized DCF plus explicit price-deck DCF, mid-cycle EV/EBITDA, asset NPV, and implied commodity/panel price |
| Young | `dcf_valuation.py`, `monte_carlo.py`, `breakeven.py` | value with/without failure branch |
| Mature | `dcf_valuation.py`, `breakeven.py`, `reverse_dcf.py` | near-term cash dominated value |
| Holding-co | `sotp.py`, `dcf_valuation.py` (core only), `comps.py` | SOTP bridge, stub multiple |

## Execution commands

```bash
cd scripts/

# Core DCF
python dcf_valuation.py ../PATH/assumptions.json
python dcf_valuation.py ../PATH/assumptions.json --json > dcf_result.json

# Monte Carlo (at least 10k trials for report quality)
python monte_carlo.py ../PATH/assumptions.json --price CURRENT_PRICE --trials 20000
python monte_carlo.py ../PATH/assumptions.json --price CURRENT_PRICE --trials 20000 --json > mc.json

# Breakeven table
python breakeven.py ../PATH/assumptions.json --price CURRENT_PRICE

# Reverse DCF (what's priced in)
python reverse_dcf.py ../PATH/assumptions.json --price CURRENT_PRICE --solve-for terminal_revenue
python reverse_dcf.py ../PATH/assumptions.json --price CURRENT_PRICE --solve-for target_operating_margin

# Cyclical reverse DCF (what commodity / panel price is priced in)
python cyclical_valuation.py ../PATH/TICKER_cyclical_inputs.json --output ../PATH/TICKER_cyclical_valuation.json
python reverse_dcf.py ../PATH/assumptions.json --price CURRENT_PRICE --solve-for commodity_price --cyclical-inputs ../PATH/TICKER_cyclical_inputs.json --json > ../PATH/TICKER_reverse_commodity_price.json

# Comps
python comps.py ../PATH/comps.json

# Charts (generate from JSON outputs)
python charts.py --kind montecarlo --in mc.json --out ../figs/
python charts.py --kind football --in football.json --out ../figs/

# Financials variant
python financial_valuation.py ../PATH/financials.json

# SOTP variant
python sotp.py ../PATH/sotp.json
```

## What you produce

A **valuation results package** containing:

1. **Intrinsic value**
   - Value per share (base case)
   - % of value in terminal
   - FCFF year-by-year schedule (summary table)

2. **Monte Carlo results**
   - Distribution statistics (mean, median, std dev, percentiles)
   - Where the current price sits in the distribution (percentile)
   - P(value > price) = probability stock is undervalued
   - **Margin-of-safety buy-band** (accumulate-below / fair / rich-above)

3. **Breakeven analysis**
   - 2-variable table: year-10 revenue × operating margin → value
   - Cells that reach the current price are marked
   - "What has to be true" narrative

4. **Reverse DCF**
   - Implied year-10 revenue at current price
   - Implied operating margin at current price
   - For cyclicals: implied normalized commodity/panel price and gap vs base deck
   - Gap vs base case (in % and absolute)
   - Plausibility assessment

5. **Comps (relative valuation)**
   - Peer median multiples
   - Implied value per share from each multiple
   - Range of comps-implied values

6. **Charts** (if generating report-quality output)
   - Monte Carlo histogram (PNG + SVG)
   - Football field chart (valuation range comparison)
   - Breakeven heatmap (optional)
   - For cyclicals: commodity price deck, cost-curve position, cycle-position dashboard, and mid-cycle valuation bridge when `TICKER_cyclical_valuation.json` exists

## Output format

```markdown
## Valuation Results: [TICKER]

### Intrinsic DCF
| Metric | Value |
|--------|-------|
| Intrinsic value/share | $X |
| Terminal value % | Y% |
| Price | $Z |
| Price / Value | A× |

### Monte Carlo (20,000 trials)
| Metric | Value |
|--------|-------|
| Median value | $X |
| Price at | Nth percentile |
| P(undervalued) | N% |
| MoS buy-below | $X |
| MoS fair range | $X – $Y |
| MoS rich-above | $Z |

### What's priced in
| Driver | Base case | Price-implied | Gap |
|--------|-----------|---------------|-----|
| Y10 revenue | $X B | $Y B | +Z% |
| Op margin | X% | Y% | +Zpp |

### Breakeven (Y10 rev × margin → value)
[Table]
```

## Troubleshooting

- If `dcf_valuation.py` produces negative value → check terminal assumptions
  (growth > CoC? Terminal ROC too low?)
- If Monte Carlo distribution is degenerate → widen the input distributions
- If `reverse_dcf.py` solves to absurd values → the price IS pricing absurdity;
  report it honestly
- If `comps.py` output is vastly different from DCF → expected for high-growth
  names; note the gap as information

## Integration notes
- All numerical outputs feed `/durability-check` (step 7) and `/triangulate` (step 8)
- The results summary is used verbatim in `/write-report` (step 9)
- Charts are embedded in the final report and PDF
- JSON outputs are preserved for reproducibility

## Adversarial Review Gate

### Review criteria
- [ ] **All scripts executed:** Every applicable script (DCF, MC, breakeven, reverse,
  comps) ran without errors. Missing a script → REVISE.
- [ ] **MC trials sufficient:** At least 10,000 trials for report-quality output.
  <5,000 → REVISE.
- [ ] **Terminal transparency:** % of value in terminal explicitly stated in the
  results summary. Missing → REVISE.
- [ ] **Price percentile:** Where the current price sits in the MC distribution is
  stated (e.g., "94th percentile"). Missing → REVISE.
- [ ] **MoS buy-band:** Margin-of-safety band (accumulate-below / fair / rich-above)
  extracted from MC output and stated. Missing → REVISE.
- [ ] **Reverse DCF comparison:** Price-implied driver values compared to base case
  with gap in % and absolute terms. Missing comparison → REVISE.
- [ ] **Cyclical triangulation:** For cyclical archetypes, `cyclical_valuation.py`
  ran and produced price-deck DCF, mid-cycle EV/EBITDA, asset NPV if applicable,
  and implied normalized commodity/panel price. Missing → REVISE.
- [ ] **Breakeven table:** 2-variable table (Y10 rev × margin) with cells that reach
  price marked. Missing → REVISE.
- [ ] **JSON outputs saved:** For chart generation and reproducibility.

### Common failure modes
- Monte Carlo run with too few trials (noise-dominated distribution)
- Terminal % not reported (hides the big bet)
- MoS band missing (most common — extract from MC output)
- Reverse DCF results not compared to base case (just numbers, no interpretation)
- Charts not generated (no PNG/SVG output)

### Verdict thresholds
- **PASS:** All scripts executed, all summary stats present, charts generated.
- **REVISE:** Missing script, insufficient trials, missing stats.
- **BLOCK:** Engine errors, negative values with no explanation, fundamentally
  broken valuation.

### Self-check (run before submitting to review)
- [ ] All applicable scripts executed without errors
- [ ] Terminal value % is explicitly stated
- [ ] Price percentile in distribution is reported
- [ ] MoS buy-band is extracted from Monte Carlo output
- [ ] Reverse DCF results are compared to base case
- [ ] JSON outputs saved for chart generation
