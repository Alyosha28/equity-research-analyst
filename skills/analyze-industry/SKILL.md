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
   - Aggregate industry margins over 10+ years — where are they in the cycle?
   - What drives margin cycles (capacity adds, demand shocks, regulation)?
   - Are margins currently above/below/at mid-cycle?

3. **Market structure**
   - Concentration: top-3/top-5/top-10 revenue share and trend
   - Barriers to entry (capital, IP, regulation, network effects, scale)
   - Buyer/supplier power dynamics

4. **Leader rotation table** (non-negotiable — the Damodaran signature)
   - Who led in 2015 / 2020 / today by revenue?
   - Who gained/lost share and why?
   - What does the rotation pattern say about moat durability?

5. **Valuation context**
   - Historical industry multiples (EV/Revenue, EV/EBITDA, P/E) over 10+ years
   - Current vs. historical — stretched, compressed, or normal?
   - Where does the target company's multiple sit vs the industry range?

### Output format

Produce a structured analysis document (~800–1500 words of prose-ready content
organized under clear headings). Every claim must reference data — use WebSearch
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
- Use WebSearch for current industry data
- Use `scripts/fetch_financials.py` for the target company's own history
- Cite sources and dates for every quantitative claim

## Integration notes
- This output feeds `/analyze-company` (company positioning within the industry)
- This output feeds `/analyze-theme` (TAM sizing, competitive dynamics)
- This output feeds `/build-assumptions` (industry-average margins, cost of capital)
- Keep it reusable — the same industry analysis can serve multiple company valuations

## Self-check
- [ ] Revenue/margin data spans 10+ years, not just 2-3
- [ ] Leader rotation table is populated with real companies and real shifts
- [ ] Industry multiples are shown historically, not just "current"
- [ ] Every number has a source or is marked as an estimate
- [ ] The lifecycle stage is argued from data, not asserted
