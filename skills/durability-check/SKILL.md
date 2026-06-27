---
name: equity-research-analyst/durability-check
description: >
  Assess the durability of a company's competitive advantage: ROIC-WACC spread,
  Competitive Advantage Period (CAP), RONIC fade, and moat component decomposition.
  Underwrites the terminal value assumptions. Step 7 of Mode A.
license: MIT
---

# Durability Check

**Pipeline position:** STEP 7 of Mode A. Runs after valuation engine execution.
Its output underwrites the terminal value — the most consequential part of any DCF.

## Input
- Company analysis from step 3 (moat components, financial history)
- Valuation results from step 6 (terminal value %, terminal assumptions)
- Industry analysis from step 2 (leader rotation history — moat durability evidence)

## What you produce

A **durability assessment** that answers: *can this company sustain excess returns,
and for how long?*

### Required elements

1. **ROIC-WACC spread**
   - Current R&D-adjusted ROIC vs WACC
   - Historical ROIC trend (5–10 years)
   - Is value being created or destroyed on the margin?
   - If ROIC < WACC: growth destroys value — flag this prominently

2. **Competitive Advantage Period (CAP)**
   - How many years can the ROIC-WACC spread persist?
   - Justified by decomposing the moat into named, testable components
   - Each component scored on: strength, durability, and vulnerability
   - CAP = the weighted horizon over which the composite moat holds

3. **Moat component decomposition**

   For each moat component, score and defend:

   | Component | Type | Strength (1-5) | Durability (years) | Threat | Monitorable indicator |
   |-----------|------|---------------|---------------------|--------|----------------------|
   | Network effects | Demand-side | 4 | 10+ | Platform shift | User growth / churn |
   | Switching costs | Lock-in | 5 | 8 | Interoperability | Gross retention rate |
   | IP/Patents | Legal | 3 | 5 | Patent cliff | Expiry calendar |
   | Scale economies | Supply-side | 4 | 7 | Competitor scale | Unit cost trend |
   | Regulatory barrier | Legal | 5 | 15 | Deregulation | Policy tracker |
   | Brand/Data | Intangible | 3 | 5 | Brand erosion | NPS / pricing power |

4. **RONIC fade**
   - Return on NEW invested capital over time
   - Starts at current ROIC, fades toward (but stays above) WACC
   - Fade speed tied to CAP: sharper fade after CAP ends
   - Terminal ROC = the perpetual return assumed → must be ≤ current ROIC
     and defended as sustainable

5. **Terminal value sensitivity**
   - How much does value change if CAP is 5 years shorter/longer?
   - How much does value change if terminal ROC moves ±2pp?
   - Report the sensitivity — the reader must see where the bet is

### Output format

```markdown
## Durability Assessment: [TICKER]

### Value creation check
- R&D-adjusted ROIC: X% vs WACC: Y% → **Spread: +Zpp** ✅ / ❌
- Historical ROIC trend: [chart/prose]
- Verdict: [creating / destroying] value on the margin

### Competitive Advantage Period
- **CAP estimate: X years**
- Basis: composite moat × industry leader-rotation cadence

### Moat decomposition
[Table as above with prose justification for each]

### RONIC fade
- Current ROIC: X% → Y5: Y% → Terminal ROC: Z%
- Fade rationale: [prose]

### Terminal sensitivity
| Scenario | CAP | Terminal ROC | Value/Share | Δ |
|----------|-----|-------------|-------------|---|
| Base     | X   | Y%          | $Z          | - |
| Longer   | X+5 | Y%          | $Z'         | +A% |
| Shorter  | X-5 | Y%          | $Z''        | -B% |
| Higher ROC | X | Y+2%       | $Z'''       | +C% |
| Lower ROC  | X | Y-2%       | $Z''''      | -D% |
```

## Integration notes
- CAP directly determines `terminal_roc` in the engine
- Moat decomposition is used in `/write-report` for the durability section
- Terminal sensitivity feeds the "what would change this view" section
- For Financials: durability is about underwriting discipline + regulatory moat,
  not ROIC-WACC spread on operating assets
- For Cyclicals: durability is about low-cost position, not pricing power

## Rules of thumb
- CAP > 15 years is extraordinary — requires exceptional evidence
- Terminal ROC > 20% requires a truly unassailable moat
- If CAP < 5 years, the terminal value collapses — the near-term cash flows ARE
  the story
- Company with ROIC < WACC: growth destroys value; the bull case must be about
  margin/ROIC improvement, not growth

## Self-check
- [ ] ROIC is R&D-adjusted (not reported GAAP)
- [ ] Each moat component has a named threat and a monitorable indicator
- [ ] CAP is justified, not asserted
- [ ] Terminal sensitivity shows the bet
- [ ] If terminal value > 80% of total, flagged prominently
