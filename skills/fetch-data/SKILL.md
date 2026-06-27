---
name: equity-research-analyst/fetch-data
description: >
  Shared utility: fetch financial data for a company and pre-fill an assumptions
  skeleton. Uses yfinance, EDGAR, or Wind MCP. Data is third-party tier — must be
  confirmed before use in valuation. Callable by any sub-skill.
license: MIT
---

# Fetch Data (Shared Utility)

**Pipeline position:** Shared — callable at any point when raw financial data is
needed. Typically invoked early in Mode A, or by `/build-assumptions` to ground
a number. Not a required pipeline step — skip if data is already in hand.

## Input
- Company ticker (e.g., `NVDA`, `0700.HK`, `600519.SS`)
- Optional: specific data needed (income statement, balance sheet, cash flow, segments)

## What you produce

A **data skeleton** — a pre-filled JSON file with third-party data, explicitly
marked as **UNCONFIRMED — VERIFY BEFORE USE**.

## Data sources (priority order)

| Tier | Source | Access | Best for |
|------|--------|--------|----------|
| 1 | Company filings (10-K, 20-F) | EDGAR / HKEX / SSE | Audited financials |
| 2 | Wind Financial Terminal | Wind MCP (`wind-find-finance-skill`) | A-shares, HK, industry data |
| 3 | yfinance | `scripts/fetch_financials.py` | Quick US-listed skeleton |
| 4 | Web search | WebSearch | Segment data, recent quarters, guidance |

## Usage

### Quick skeleton (US-listed)
```bash
cd scripts/
python fetch_financials.py NVDA --out nvda_skel.json
```

Pulls from yfinance: revenue, operating income, R&D, shares, cash, debt, growth.

### Manual collection (A-shares, HK, unlisted)
1. Use Wind MCP if available: `wind-find-finance-skill` / `wind-mcp-skill`
2. Use WebSearch + WebFetch for: latest annual report, segment breakdown,
   historical growth (5-10 years), beta, peer multiples
3. Fill the appropriate template from `templates/`

### Required data points

```
Company info:     name, ticker, sector
Current price:    [date] close
Shares:           basic + diluted (millions)
Income:           revenue (3-5 yrs), operating income, R&D, D&A, SBC, tax rate
Balance sheet:    cash, total debt, minority interests, invested capital
Cash flow:        capex, FCF, buybacks, dividends (3-5 yrs)
Segments:         revenue by segment (current year)
Market:           beta, historical P/E range
For financials:   book value, ROE, tier-1 capital, NIM, loan loss reserves,
                  float, combined ratio (NOT standard income statement items)
```

## Output

A JSON skeleton (e.g., `NVDA_skel.json`) with:
- All available fields populated
- Source annotation for each value (`_source`, `_tier`, `_date`)
- Estimated fields marked `"_estimate": true`
- Clear header warning: "THIRD-PARTY DATA — CONFIRM BEFORE USE"

## Data confidence tiers

Every number tagged:
- `audited` — From company filings (10-K, annual report)
- `management-guidance` — Company's own forward guidance
- `sell-side-consensus` — Consensus estimates
- `third-party-aggregator` — yfinance, Wind, Bloomberg data
- `own-estimate` — Your judgment

## Critical warnings

1. **yfinance data can be stale, wrong, or restated.** Always confirm against
   the most recent filing.
2. **Segment data is rarely in yfinance.** Manual collection required.
3. **Chinese company data from yfinance is unreliable.** Use Wind MCP or filings.
4. **For banks/insurers:** yfinance metrics are *meaningless*. You need: book value,
   ROE, tier-1 capital, NIM, loan loss reserves, float, combined ratio.
5. **This is a STARTING POINT, not the assumptions file.** Every number needs
   verification, accounting adjustment, and low/base/high range in `/build-assumptions`.

## Integration
- Output feeds `/build-assumptions` as a starting skeleton
- Not a substitute for reading actual filings
- For refreshes (Mode C): used to check if reported financials have changed

## Self-check
- [ ] All data fields have source + tier + date annotations
- [ ] Third-party warnings are visible in the output
- [ ] For financials: correct metrics collected (not standard P&L items)
- [ ] Skeleton is valid JSON
- [ ] User is warned: "confirm against filings before using"
