---
name: equity-research-analyst/analyze-theme
description: >
  Analyze the thematic driver behind a company's growth: TAM sizing by segment,
  market share trajectory, competitive landscape mapping, and the ecosystem value
  chain. Produces the growth story that feeds revenue assumptions. Step 4 of Mode A.
license: MIT
---

# Analyze Theme / Driver

**Pipeline position:** STEP 4 of Mode A. Can run in parallel with step 2 (industry).
Consumes step 3 (company) to locate the firm in the value chain.

## Input
- Company analysis from step 3
- Industry analysis from step 2
- Archetype from step 1

## What you produce

A **thematic analysis** that sizes the opportunity and maps the competitive field.

### Required elements

1. **The big swing factor**
   - What is the one or two drivers that will determine this company's fate over
     the next 5–10 years?
   - Is the change *revolutionary* (creates new TAM) or *incremental* (shifts share)?
   - Why now? What catalyzed this theme?

2. **Ecosystem / value chain map**
   - Where does the company sit? (upstream / midstream / downstream / platform)
   - Who are the suppliers, complements, customers, and substitutes?
   - Who captures the surplus if the theme plays out?

3. **Segment TAM × market share build** (non-negotiable — Damodaran requirement)
   - For each segment: TAM today → TAM in year 5 → TAM in year 10
   - For each segment: company share today → defensible share year 10
   - TAM sizing basis: third-party research (cite), bottoms-up units×ASP, or
     customer-capex bridge
   - **Two independent revenue paths**: (a) top-down TAM × share AND (b) bottom-up
     units × ASP capped by supply/capacity ceiling. Where they differ = information.

4. **Competitive landscape**
   - Who competes on which battlefield?
   - How strong is each threat? (incumbents, new entrants, substitutes, customer
     in-sourcing, supplier forward-integration)
   - The structural advantage that keeps share from eroding

5. **Growth trajectory**
   - Segment-by-segment growth rates over the forecast horizon
   - Growth declines from current toward the riskfree rate by year 10
   - Sanity check: does the absolute TAM × share revenue pass the "big market
     delusion" test? (Sum all credible players' implied revenues — do they exceed
     a plausible total market?)

### Output format

```markdown
## Theme: [name]

### The swing factor
[Prose: what drives this company's fate over the next decade]

### Value chain
[Prose + simple chain: upstream → company → downstream, with surplus dynamics]

### TAM × share build
| Segment | TAM today | TAM Y5 | TAM Y10 | Share today | Share Y10 | Revenue Y10 |
|---------|-----------|--------|---------|-------------|-----------|-------------|
| ...     |           |        |         |             |           |             |

**Top-down path:** Σ(TAM × share) = $X B
**Bottom-up path:** units × ASP = $Y B (ceiling: capacity constraint Z)
**Gap:** $|X-Y| B → [interpret what this means]

### Competitive landscape
| Competitor | Battlefield | Capability | Threat level | Our response |
|------------|-------------|------------|-------------|--------------|
| ...        |             |            |             |              |

### Growth trajectory
[Prose: how growth glides from current rate toward riskfree, with segment detail]
**"Big Market Delusion" check:** all credible players' implied Y10 revenues sum
to $X B vs plausible TAM of $Y B → [PASS / WARN: gap of Z%]
```

## Data sources
- WebSearch for TAM estimates (Gartner, IDC, McKinsey, industry associations)
- For capex-bridge: hyperscaler/enterprise capex guidance from earnings calls
- Supply ceiling: capacity data from industry publications (SemiAnalysis-style)
- Cite every TAM figure with source and date

## Integration notes
- This is the direct input to `/build-assumptions` revenue growth driver
- The competitive map feeds the CAP/moat durability in `/durability-check`
- The "Big Market Delusion" check is a required gate output

## Self-check
- [ ] Revenue is built bottom-up by segment, not one blended growth rate
- [ ] Two independent revenue paths are attempted (top-down + bottom-up)
- [ ] TAM sources are cited with dates
- [ ] Competitive landscape is specific (named competitors, named battlefields)
- [ ] "Big Market Delusion" check is run
- [ ] Growth declines to ≤ riskfree rate by terminal year
