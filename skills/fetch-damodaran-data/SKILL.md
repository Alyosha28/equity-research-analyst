---
name: equity-research-analyst/fetch-damodaran-data
description: >
  Fetch the current cost-of-capital inputs from Aswath Damodaran's NYU Stern data
  pages: implied Equity Risk Premium (ERP), country risk premiums (CRP), industry
  betas and cost of capital, and the current riskfree rate. Produces a single
  damodaran_data.json consumed by /build-assumptions. First step of Mode A Phase 0.
license: MIT
---

# Fetch Damodaran Data

**Pipeline position:** STEP 0.1 of Mode A Phase 0. Runs BEFORE `/classify-archetype`.
Fetches all market-data inputs from Damodaran's public NYU Stern data pages so that
every downstream step uses current, dated cost-of-capital parameters — never hardcoded.

This is a **fetch utility**, not an analysis sub-skill. Its job is to pull current
numbers accurately and date them. No judgment, no interpretation, no adjustment —
just clean date-stamped retrieval.

## Why this exists

Cost of capital is the most consequential input in any valuation. A 1pp error in
the discount rate changes intrinsic value by 10–25% for most companies. Without this
sub-skill, every analysis either hardcodes stale numbers or DIY-fetches inconsistently.

This sub-skill is the **single point of truth** for all cost-of-capital inputs in the
pipeline. It runs once at the start of every Mode A valuation. The output is consumed
by `/build-assumptions` (Step 5) which applies the numbers to the specific company.

## Input

None required. This sub-skill fetches directly from public NYU Stern data pages.

Optional inputs that improve accuracy:
- Company domicile (for sovereign default spread lookup)
- Countries of significant operations (for country risk premium basket)
- Industry classification (for industry beta/cost of capital lookup)

## Data sources (all from pages.stern.nyu.edu/~adamodar)

| Data | Source URL | Update frequency | Format |
|------|-----------|-----------------|--------|
| **Implied ERP** | `pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/impliedERP.html` | Monthly | HTML table |
| **Historical ERP / Risk Premiums** | `pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/histimpl.html` | Annual | HTML table |
| **Country Risk Premiums** | `pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/ctryprem.html` | Semi-annual (Jan, Jul) | HTML table |
| **Industry Betas** | `pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/Betas.html` | Annual | HTML table |
| **Industry Cost of Capital** | `pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/wacc.html` | Annual | HTML table |
| **Riskfree Rate Guidance** | `pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/ratings.html` | Periodic | HTML table (sovereign ratings for default spread) |
| **Sovereign Default Spreads** | `pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/ctryprem.html` (same source as CRP) | Semi-annual | HTML table |

All data is hosted on the public Damodaran site. Data is pulled via `WebFetch` (single-page HTML tables). No API key, no login, no authentication required.

## What you produce

A single `damodaran_data.json` file with all fetched data, dates, and source URLs.

```json
{
  "_fetched_at": "2024-06-15T14:30:00Z",
  "_fetched_by": "equity-research-analyst/fetch-damodaran-data",
  "_notes": "All data from Aswath Damodaran's public NYU Stern data pages. Dates reflect the data vintage, not the fetch date.",

  "equity_risk_premium": {
    "implied_erp": 0.0450,
    "implied_erp_date": "2024-06-01",
    "historical_erp": 0.0523,
    "historical_erp_method": "Geometric average 1928-2023 vs 10yr T-bond",
    "source_url": "https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/impliedERP.html",
    "data_vintage": "2024-06-01",
    "notes": "Implied ERP from S&P 500 aggregate — forward-looking, updated monthly. Preferred for cost of equity."
  },

  "riskfree_rate": {
    "rate": 0.0425,
    "instrument": "US 10-year Treasury bond",
    "as_of_date": "2024-06-14",
    "sovereign_default_spread": 0.00,
    "sovereign_moodys_rating": "Aaa",
    "sovereign_default_spread_source": "Damodaran sovereign ratings page",
    "notes": "US is Aaa-rated — no sovereign default spread. For non-Aaa domiciled companies: riskfree rate = US 10yr + sovereign default spread.",
    "non_aaa_adjustment_rule": "If the company's domicile sovereign is not Aaa-rated, the riskfree rate MUST be adjusted upward by the sovereign default spread from Damodaran's ratings table. See Damodaran July 2025 methodology update."
  },

  "country_risk_premiums": {
    "fetched_for_all_countries": true,
    "data_vintage": "2024-01-01",
    "source_url": "https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/ctryprem.html",
    "countries": [
      {
        "country": "United States",
        "crp": 0.0000,
        "default_spread": 0.0000,
        "equity_risk_premium": 0.0450,
        "country_risk_premium": 0.0000
      },
      {
        "country": "China",
        "crp": 0.0069,
        "default_spread": 0.0069,
        "equity_risk_premium": 0.0519,
        "country_risk_premium": 0.0069
      }
    ]
  },

  "industry_betas": {
    "data_vintage": "2024-01-01",
    "source_url": "https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/Betas.html",
    "total_market": {
      "beta": 1.00,
      "number_of_firms": null
    },
    "industries": [
      {
        "industry": "Software (System & Application)",
        "beta": 1.25,
        "unlevered_beta": 1.18,
        "debt_to_equity": 5.91,
        "number_of_firms": 288
      }
    ]
  },

  "industry_cost_of_capital": {
    "data_vintage": "2024-01-01",
    "source_url": "https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/wacc.html",
    "industries": [
      {
        "industry": "Software (System & Application)",
        "cost_of_equity": 0.0872,
        "cost_of_capital": 0.0829,
        "number_of_firms": 288
      }
    ]
  },

  "trust_deficit_signals": {
    "evaluated_at": "2024-06-15",
    "sovereign_downgrade_risk": false,
    "sovereign_downgrade_note": "US Moody's Aaa, stable outlook — no downgrade active",
    "usd_trend_weakening": false,
    "usd_trend_note": "DXY within 2-year range — no sharp depreciation signal",
    "gold_price_surge": false,
    "gold_price_note": "Gold at $2,320/oz — elevated but not in acute breakout vs 2-year trend",
    "cb_independence_concern": false,
    "cb_independence_note": "No recent legislative or executive action threatening Fed independence",
    "governance_institutional_risk": false,
    "governance_note": "No active constitutional or institutional crisis affecting sovereign credit",
    "trust_deficit_premium_applied": false,
    "trust_deficit_premium_bps": 0,
    "trust_deficit_rationale": "No active trust-deficit signals. Premium = 0. If signals were active, apply 25-100 bps as named, separate premium to cost of capital."
  }
}
```

## Workflow

### 1. Fetch implied ERP (most current)

```bash
# Use WebFetch on the HTML page
# The implied ERP is the "Implied Premium (FCFE)" row in the main table
# It is updated monthly — use the most recent row
```

**What to extract:**
- Implied ERP (the "Implied Premium" number)
- Date of the estimate (month/year header)
- Historical ERP for reference (from the histimpl page or the same page's sidebar)

**Primary ERP rule:** Use the **implied ERP** (forward-looking, updated monthly) as the primary ERP input. The historical ERP (1928–present geometric average) is provided for reference but is NOT the primary ERP for the valuation. This is consistent with Damodaran's own practice.

### 2. Fetch riskfree rate

**Riskfree rate = 10-year US Treasury bond yield + sovereign default spread (if domicile sovereign is not Aaa-rated).**

```bash
# Get the current 10-year US Treasury yield (from any financial data source — WebSearch is fine)
# Cross-reference with the Fed's H.15 release if possible
```

**For non-Aaa domiciles (e.g., China, India, Brazil, Turkey):**
- Look up the sovereign's Moody's rating from `ratings.html`
- Find the corresponding default spread from `ctryprem.html`
- Riskfree rate = US 10yr + sovereign default spread
- Example: China (A1) → default spread ~0.69% → riskfree = 4.25% + 0.69% = 4.94%

**This is a CRITICAL adjustment.** Companies domiciled in non-Aaa-rated sovereigns
have a higher riskfree rate. Using the US 10-year without adjustment systematically
undervalues the cost of capital for non-Aaa companies. See Damodaran's July 2025
methodology note on this topic.

### 3. Fetch country risk premiums

```bash
# WebFetch ctryprem.html
# Extract: country name, Moody's rating, default spread, equity risk premium, country risk premium
```

**How country risk premiums are applied (by /build-assumptions, not here):**
- CRP is an ADDITIONAL premium on top of the base ERP
- CRP is applied to companies with significant operations in higher-risk countries
- If a US company derives 60% of revenue from China, a portion of China's CRP is blended into the cost of equity
- The CRP application methodology is in `/build-assumptions` — this sub-skill only fetches the data

**This sub-skill fetches CRP for ALL countries** (not just the domicile), so
`/build-assumptions` can compute revenue-weighted CRP baskets.

### 4. Fetch industry betas

```bash
# WebFetch Betas.html
# Extract: industry name, beta, unlevered beta, D/E ratio, number of firms
```

**Betas are INDUSTRY-AVERAGE betas, bottom-up.** Damodaran's betas are computed as
the average of unlevered betas across firms in each industry, then re-levered at
the industry-average D/E. They are more stable and defensible than single-company
regression betas.

`/build-assumptions` will:
1. Identify the target company's industry (or industries, for multi-segment)
2. Look up the unlevered beta for each industry
3. Re-lever at the company's ACTUAL D/E ratio (not the industry average)
4. Apply any company-specific risk adjustments

### 5. Fetch industry cost of capital

```bash
# WebFetch wacc.html
# Extract: industry name, cost of equity, cost of capital
```

**Used for sanity-checking and glide-path construction:**
- Company's initial cost of capital should be roughly in line with its industry
- The terminal cost of capital should glide toward the market average
- Industry CoC provides the anchor for both

### 6. Evaluate trust-deficit signals

**What is a trust-deficit signal?** (Damodaran concept)
A reduction in trust in institutions (central bank independence, sovereign credit,
currency stability, governance) that is NOT yet priced into sovereign credit ratings.
When active, it warrants an additional premium on cost of capital (25–100 bps).

**Signal checklist:**

| Signal | Indicator | Threshold | Data source |
|--------|-----------|-----------|------------|
| **Sovereign downgrade** | Moody's rating outlook changed to negative in last 6 months | Recent outlook downgrade | Moodys.com / Damodaran ratings page |
| **USD trend weakening** | DXY down >10% in 12 months OR below 5-year moving average by >5% | Sustained weakness | DXY index |
| **Gold price surge** | Gold up >30% in 12 months against USD, above real rate-implied level | >30% YoY | Gold spot price |
| **CB independence erosion** | Legislative action limiting Fed independence, presidential pressure, or senior resignations | Documented event | News search |
| **Governance/institutional risk** | Constitutional crisis, contested election, government shutdown threat, debt ceiling brinkmanship | Documented event | News search |

**If any signal is active:**
- Note it in the output under `trust_deficit_signals`
- `/build-assumptions` will evaluate whether to apply a trust-deficit premium (25–100 bps)
- The premium, if applied, must be separately named and justified — never silently folded
  into the ERP

### 7. Output damodaran_data.json

Write the complete JSON file to disk. The path is determined by the orchestrator
but typically: `TICKER_damodaran_data.json` or a shared `damodaran_data.json`
that can be reused across same-day valuations.

## Versioning and staleness

| Data | Acceptable age | Action if stale |
|------|---------------|-----------------|
| Implied ERP | < 2 months | Fetch latest (monthly) — the most critical freshness requirement |
| Riskfree rate | < 1 week | Fetch latest — Treasury yields move daily |
| Country risk premiums | < 7 months | Fetch latest (semi-annual Jan/Jul update) |
| Industry betas | < 13 months | Fetch latest (annual update, typically Jan) |
| Industry WACC | < 13 months | Fetch latest (annual update, typically Jan) |
| Sovereign default spread | < 7 months | Fetch latest (updated with CRP) |

**If any data is stale beyond the acceptable age:** flag it in the output with
`"_stale": true` and the age. `/build-assumptions` will note the staleness in the
assumptions narrative.

## Output

- `damodaran_data.json` — complete cost-of-capital data package
- The output feeds `/build-assumptions` (Step 5) directly

## Integration notes

- **Invoked first in Mode A Phase 0** — before `/classify-archetype`
- **Data freshness is critical** — the valuation date is pinned by the data dates
- **No judgment in this sub-skill** — fetch accurately, date everything, let the
  downstream skills interpret
- **For Mode C refreshes:** re-run this sub-skill to check if ERP, riskfree rate,
  or CRP have moved meaningfully since the prior valuation date
- **The trust-deficit evaluation is descriptive** — this sub-skill reports what it
  sees; `/build-assumptions` decides whether to apply a premium

## Adversarial Review Gate

### Review criteria
- [ ] **All data fields fetched:** Implied ERP, riskfree rate, CRP (all countries),
  industry betas, industry WACC. Missing a data class → REVISE.
- [ ] **Every number dated:** ERP date, riskfree rate date, CRP vintage, beta vintage,
  WACC vintage all explicitly stated. Undated number → REVISE.
- [ ] **Source URLs recorded:** Every data class has its source URL in the output.
  Missing URL → REVISE.
- [ ] **Data recency check:** Reviewer checks each data class against acceptable age
  table. Stale data flagged prominently. Using stale data silently → REVISE.
- [ ] **Riskfree rate adjustment:** If the sovereign is not Aaa-rated, the riskfree
  rate includes the sovereign default spread per Damodaran methodology. Missing
  adjustment → REVISE (CRITICAL — this systematically undervalues cost of capital).
- [ ] **Implied ERP used as primary:** Implied ERP (not historical) is the primary
  ERP with the correct date. Using historical as primary → REVISE.
- [ ] **Trust-deficit signals evaluated:** All 5 signals checked with dated evidence.
  Missing signal evaluation → REVISE.
- [ ] **CRP fetched for all countries:** Not just the domicile — all countries.
  Only domicile CRP → REVISE (downstream can't compute revenue-weighted baskets).
- [ ] **JSON validity:** Output is valid JSON. Validate with `python -c "import json; json.load(open('file'))"`.
- [ ] **No hardcoded numbers:** All numbers trace to the fetched pages, not to
  embedded constants. Hardcoded ERP/CRP/riskfree → REVISE (CRITICAL).

### Common failure modes
- **Stale ERP used without flagging** — most common. Reviewer: check the ERP date
  against the current month. If >2 months old, REVISE.
- **Historical ERP used as primary** — the implied ERP page has both; grabbing the
  wrong row. Historical ERP is for reference only.
- **Riskfree rate unadjusted for sovereign default spread** — using US 10yr for a
  Chinese company. This is the most common CRITICAL error in non-US valuations.
- **CRP fetched only for domicile** — downstream can't build revenue-weighted baskets.
- **Trust-deficit signals skipped entirely** — the checklist exists; evaluate it.
- **Numbers without source URLs** — downstream has no way to verify.
- **Data from the wrong Damodaran page** — e.g., using old data files instead of the
  current monthly update.

### Verdict thresholds
- **PASS:** All data fetched, dated, sourced, recency checked, riskfree adjusted,
  trust-deficit evaluated, JSON valid.
- **REVISE:** Missing a data class, undated number, stale data unflagged, CRP
  incomplete, riskfree unadjusted, trust-deficit skipped.
- **BLOCK:** Hardcoded numbers (not from Damodaran pages), riskfree fundamentally
  wrong (e.g., using 3-month bill instead of 10-year), or no data fetched at all.

### Self-check (run before submitting to review)
- [ ] Implied ERP is current (monthly) and used as primary, not historical
- [ ] Riskfree rate is dated within 1 week
- [ ] If sovereign is not Aaa: sovereign default spread applied to riskfree rate
- [ ] CRP fetched for ALL countries, not just domicile
- [ ] Industry beta and WACC data present with vintage dates
- [ ] All 5 trust-deficit signals evaluated with dated evidence
- [ ] Every number has: value, date, source URL
- [ ] JSON is valid
- [ ] No hardcoded constants — all numbers are fetched
