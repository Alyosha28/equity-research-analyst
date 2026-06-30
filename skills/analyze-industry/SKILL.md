---
name: equity-research-analyst/analyze-industry
description: >
  Analyze the industry a company operates in: lifecycle stage, profitability cycles,
  market structure, winner/loser rotation over 10+ years. Produces the macro context
  for the valuation. Step 2 of Mode A.
license: MIT
---

# Analyze Industry

**Pipeline position:** STEP 2 of Mode A. Runs after archetype classification.
Provides the field-of-play context that the company and theme analyses build on.

## Input
- Company name / ticker / industry
- Archetype from step 1
- Any existing industry knowledge in context

## What you produce

An **industry analysis** in structured but prose-ready form, with these required
elements (each backed by data, not assertion):

### Required elements

1. **Lifecycle stage**
   - Is the industry growing, maturing, or declining?
   - What's the aggregate revenue curve over the last 10+ years?
   - What's the revenue growth rate trend (accelerating / decelerating / flat)?

2. **Profitability cycle**
   - Aggregate industry margins over 10+ years 鈥?where are they in the cycle?
   - What drives margin cycles (capacity adds, demand shocks, regulation)?
   - Are margins currently above/below/at mid-cycle?

3. **Market structure**
   - Concentration: top-3/top-5/top-10 revenue share and trend
   - Barriers to entry (capital, IP, regulation, network effects, scale)
   - Buyer/supplier power dynamics

4. **Leader rotation table** (non-negotiable 鈥?the Damodaran signature)
   - Who led in 2015 / 2020 / today by revenue?
   - Who gained/lost share and why?
   - What does the rotation pattern say about moat durability?

5. **Valuation context**
   - Historical industry multiples (EV/Revenue, EV/EBITDA, P/E) over 10+ years
   - Current vs. historical 鈥?stretched, compressed, or normal?
   - Where does the target company's multiple sit vs the industry range?

### Output format

Produce a structured analysis document (~800鈥?500 words of prose-ready content
organized under clear headings). Every claim must reference data 鈥?use web search
if needed to pull industry data.

```markdown
## Industry: [name]

### Lifecycle & growth
[Prose with aggregate revenue data, growth trends, lifecycle stage]

### Profitability
[Prose with margin history, cycle position, structural vs cyclical drivers]

### Market structure
[Prose with concentration data, barriers, power dynamics]

### Leader rotation
| Year | #1 | #2 | #3 | #4 | #5 |
|------|----|----|----|----|----|
| 2015 |    |    |    |    |    |
| 2020 |    |    |    |    |    |
| Today|    |    |    |    |    |

[Prose: what changed and why]

### Valuation history
[Prose with historical multiples, current positioning]
```

## Data sources
- Use web search for current industry data
- Use `scripts/fetch_financials.py` for the target company's own history
- Cite sources and dates for every quantitative claim

## Integration notes
- This output feeds `/analyze-company` (company positioning within the industry)
- This output feeds `/analyze-theme` (TAM sizing, competitive dynamics)
- This output feeds `/build-assumptions` (industry-average margins, cost of capital)
- Keep it reusable 鈥?the same industry analysis can serve multiple company valuations

## Adversarial Review Gate

### Review criteria
- [ ] **Data depth:** Revenue/margin data spans 10+ years, not just 2-3. Reviewer:
  count the years 鈥?if <7 data points, REVISE.
- [ ] **Leader rotation table:** Populated with real companies and real shifts.
  Empty or generic table 鈫?REVISE.
- [ ] **Sourcing:** Every quantitative claim has a source or is marked as estimate.
  Unsourced round numbers 鈫?REVISE.
- [ ] **Lifecycle evidence:** The lifecycle stage is argued FROM data, not asserted
  without evidence. "Mature industry" with no data 鈫?REVISE.
- [ ] **Multiples history:** Industry multiples shown historically (10+ year range),
  not just "current P/E is X." Missing historical context 鈫?REVISE.
- [ ] **Consistency with archetype:** Industry analysis must be consistent with
  the locked archetype. Cyclical archetype without margin cycle data 鈫?REVISE.

### Common failure modes
- Industry analysis that reads like a Wikipedia summary (no quantitative depth)
- Leader rotation table with placeholder company names
- "Industry is mature/growing" asserted without revenue curve data
- Missing valuation context (no historical multiples)

### Verdict thresholds
- **PASS:** All 6 criteria met; data is sourced and spans 10+ years.
- **REVISE:** Missing depth on 1-2 criteria; specific gaps identified.
- **BLOCK:** No quantitative data, fabricated numbers, or completely generic.
  (Rare 鈥?typically a REVISE, not a BLOCK.)

### Self-check (run before submitting to review)
- [ ] Revenue/margin data spans 10+ years, not just 2-3
- [ ] Leader rotation table is populated with real companies and real shifts
- [ ] Industry multiples are shown historically, not just "current"
- [ ] Every number has a source or is marked as an estimate
- [ ] The lifecycle stage is argued from data, not asserted
