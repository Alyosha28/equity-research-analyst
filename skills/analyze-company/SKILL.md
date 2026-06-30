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

A **company analysis** (~1000鈥?000 words of prose-ready content) covering:

### Required elements

1. **Business model 鈥?how it actually makes money**
   - Revenue composition by segment (with approximate %s)
   - Who pays, what they pay for, and why they pay
   - The economics: gross margin structure, fixed vs variable costs
   - Customer concentration (top-3 customers as % of revenue)

2. **Moat and competitive position**
   - What structural advantage does the company hold?
   - Decompose into named, testable components (network effects, switching costs,
     IP/patents, scale economies, regulatory barrier, brand, data advantage)
   - For each: how strong (1-5) and what could erode it?

3. **10-year financial trajectory** (non-negotiable 鈥?Damodaran depth requirement)
   - Revenue, operating profit (reported + R&D-adjusted), FCF, historical P/E,
     share count 鈥?each as a prose walk through the decade
   - Include the **near-death drawdowns**: stock falling >50%, the business root
     cause, and how the company recovered (or didn't)

4. **Structural risks built into the model**
   - Not generic "competition risk" 鈥?risks specific to *this* business model
   - E.g., fabless 鈫?TSMC/Taiwan dependence; platform 鈫?regulatory reclassification;
     single-product 鈫?concentration
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

### Financial trajectory (2015鈥?025)
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
- Use web search for historical stock prices (drawdowns), segment data, peer comps
- For Chinese companies: Wind MCP if available, otherwise public filings
- Cite every number's source and date

## Integration notes
- Feeds `/analyze-theme`: where the company sits in the value chain
- Feeds `/build-assumptions`: historical margins, sales-to-capital, risk inputs
- Feeds `/durability-check`: moat components 鈫?CAP estimate
- The drawdowns directly inform the bear case in `/write-report`

## Adversarial Review Gate

### Review criteria
- [ ] **Segment decomposition:** Revenue decomposed by segment with approximate %s.
  Single top-line number without segments 鈫?REVISE.
- [ ] **Moat specificity:** Moat decomposed into named, testable components with
  strength scores. "Strong brand" without mechanism 鈫?REVISE.
- [ ] **Drawdowns present:** At least one major historical drawdown (>50% decline)
  documented with business root cause and recovery narrative. Missing 鈫?REVISE.
- [ ] **Risk specificity:** Structural risks are company-specific (e.g., "fabless
  鈫?TSMC dependence"), not generic ("competition risk"). Generic risks 鈫?REVISE.
- [ ] **SBC quantification:** SBC dilution rate explicitly stated over 5+ years.
  "SBC is a cost" without the number 鈫?REVISE.
- [ ] **Data sourcing:** Financial data is sourced with dates. Reviewer: spot-check
  one number against known filings.

### Common failure modes
- Moat described as "strong competitive position" without decomposition
- Drawdowns missing entirely (most common 鈥?fix by searching historical price)
- Risks that apply to any company ("macro risk," "competition")
- SBC mentioned qualitatively but not quantified

### Verdict thresholds
- **PASS:** All criteria met; moat decomposed; drawdowns documented; SBC quantified.
- **REVISE:** 1-2 missing elements with specific gaps. Most common: add drawdowns.
- **BLOCK:** Fabricated financials, completely wrong business model, or company
  confused with a different entity.

### Self-check (run before submitting to review)
- [ ] Revenue is decomposed by segment, not just a single top-line number
- [ ] The moat is decomposed into named, testable components (not "strong brand")
- [ ] 10-year financial trajectory includes at least one major drawdown
- [ ] Structural risks are company-specific, not generic
- [ ] SBC dilution rate is explicitly stated
