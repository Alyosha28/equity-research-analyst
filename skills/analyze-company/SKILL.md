---
name: equity-research-analyst/analyze-company
description: >
  Deep-dive company analysis: business model, moat, 10-year financial trajectory,
  near-death drawdowns, structural risks. Produces the company narrative that the
  valuation story is built on. Step 3 of Mode A.
license: MIT
---

# Analyze Company

**Pipeline position:** STEP 3 of Mode A. Runs after industry analysis.
Produces the company-specific evidence that anchors the numbers.

## Input
- Company name / ticker
- Industry analysis from step 2
- Archetype from step 1

## What you produce

A **company analysis** (~1000–2000 words of prose-ready content) covering:

### Required elements

1. **Business model — how it actually makes money**
   - Revenue composition by segment (with approximate %s)
   - Who pays, what they pay for, and why they pay
   - The economics: gross margin structure, fixed vs variable costs
   - Customer concentration (top-3 customers as % of revenue)

2. **Moat and competitive position**
   - What structural advantage does the company hold?
   - Decompose into named, testable components (network effects, switching costs,
     IP/patents, scale economies, regulatory barrier, brand, data advantage)
   - For each: how strong (1-5) and what could erode it?

3. **10-year financial trajectory** (non-negotiable — Damodaran depth requirement)
   - Revenue, operating profit (reported + R&D-adjusted), FCF, historical P/E,
     share count — each as a prose walk through the decade
   - Include the **near-death drawdowns**: stock falling >50%, the business root
     cause, and how the company recovered (or didn't)

4. **Structural risks built into the model**
   - Not generic "competition risk" — risks specific to *this* business model
   - E.g., fabless → TSMC/Taiwan dependence; platform → regulatory reclassification;
     single-product → concentration
   - For each: mechanism, probability, impact on value drivers

5. **Capital allocation track record**
   - How has management deployed capital? (buybacks, M&A, organic reinvestment, dividends)
   - Has buyback been value-accretive (below intrinsic) or destructive (above)?
   - Dilution rate from SBC over the decade

### Output format

```markdown
## Company: [name] ([ticker])

### Business model
[Prose walk through segments, customers, economics]

### Moat decomposition
| Component | Strength (1-5) | Threat vector | Monitorable indicator |
|-----------|---------------|---------------|----------------------|
| ...       |               |               |                      |

### Financial trajectory (2015–2025)
[Prose walk through revenue, profit, FCF, margins, share count by year.
Include the drawdowns as named episodes with root cause + recovery narrative.]

### Structural risks
| Risk | Mechanism | Probability | Impact | Leading indicator |
|------|-----------|-------------|--------|-------------------|
| ...  |           |             |        |                   |

### Capital allocation
[Prose on management's capital deployment record + SBC dilution trend]
```

## Data sources
- Use `scripts/fetch_financials.py TICKER` to pull a skeleton
- Use WebSearch for historical stock prices (drawdowns), segment data, peer comps
- For Chinese companies: Wind MCP if available, otherwise public filings
- Cite every number's source and date

## Integration notes
- Feeds `/analyze-theme`: where the company sits in the value chain
- Feeds `/build-assumptions`: historical margins, sales-to-capital, risk inputs
- Feeds `/durability-check`: moat components → CAP estimate
- The drawdowns directly inform the bear case in `/write-report`

## Self-check
- [ ] Revenue is decomposed by segment, not just a single top-line number
- [ ] The moat is decomposed into named, testable components (not "strong brand")
- [ ] 10-year financial trajectory includes at least one major drawdown
- [ ] Structural risks are company-specific, not generic
- [ ] SBC dilution rate is explicitly stated
