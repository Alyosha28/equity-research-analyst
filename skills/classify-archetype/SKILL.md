---
name: equity-research-analyst/classify-archetype
description: >
  Classify a company into its valuation archetype (growth/mature, financials, cyclical,
  young, mature/declining, holding-co) and select the correct engine and playbook.
  First step of Mode A — determines everything downstream.
license: MIT
---

# Classify Archetype

**Pipeline position:** STEP 1 of Mode A. Runs first — its output determines the
engine, playbook, and driver set for every downstream step.

## Input
- Company name / ticker
- Brief description of business (if available)
- Sector/industry

## What you produce

A classification verdict with rationale:

```
Archetype: [one of 6]
Engine: [which Python script]
Playbook: [which reference playbook]
Confidence: HIGH / MEDIUM / CHECK
If CHECK: what additional info would resolve ambiguity
```

## The six archetypes

| Archetype | Defining trait | Engine | Playbook |
|-----------|---------------|--------|----------|
| **Default** (growth/mature operating co) | Earns operating margin on goods/services | `dcf_valuation.py` | methodology-damodaran.md |
| **Financials** | Balance sheet IS the product; earns spread/underwriting | `financial_valuation.py` | playbook-financials.md |
| **Cyclical** | Commodity/cyclical price-taker; margins cycle with macro | `dcf_valuation.py` (normalized) | playbook-cyclical.md |
| **Young** | Currently lossmaking / pre-scale; high failure risk | `dcf_valuation.py` + failure branch | playbook-young.md |
| **Mature/Declining** | Flat-to-declining, returning cash, low reinvestment | `dcf_valuation.py` (low/neg growth) | playbook-mature.md |
| **Holding-co** | Operating co + large investment portfolio | `sotp.py` | holding-company-sotp.md |

## Classification algorithm

Ask in order — the first "yes" is the answer:

1. **Does the company earn primarily a spread or underwriting result on its own balance sheet?**
   - YES → **Financials**. (Banks, insurers, specialty lenders, BDCs, mortgage REITs.)
   - TRAP: card networks, exchanges, rating agencies, asset managers, pure-fee fintechs
     are NOT financials — they earn fees on others' money. Use Default.

2. **Is the company currently unprofitable / pre-revenue / pre-scale, with a material chance of failure?**
   - YES → **Young**. (Biotech pre-approval, early SaaS burning cash, pre-revenue deep tech.)

3. **Is the company's revenue dominated by a commodity whose price it cannot control?**
   - YES → **Cyclical**. (Miners, oil & gas producers, chemical commodity, steel, shipping.)

4. **Is the company flat-to-declining, paying out most earnings, with minimal reinvestment?**
   - YES → **Mature/Declining**. (Tobacco, legacy media, declining retail.)

5. **Does the company hold a large, separable investment portfolio alongside an operating business?**
   - YES → **Holding-co**. (Tencent, SoftBank, Berkshire, conglomerates.)

6. **None of the above** → **Default**. (NVIDIA, Apple, Starbucks, most companies.)

## Output format

```json
{
  "archetype": "default",
  "engine": "scripts/dcf_valuation.py",
  "playbook": "references/methodology-damodaran.md",
  "rationale": "Company earns operating margins on goods/services — standard FCFF frame.",
  "confidence": "HIGH",
  "traps_avoided": [],
  "downstream_consequences": {
    "drivers": ["revenue_growth", "target_margin", "sales_to_capital", "cost_of_capital"],
    "required_playbooks": ["methodology-damodaran.md", "analyst-playbook.md"],
    "special_checks": []
  }
}
```

## Edge cases

- **Diversified financials** with large asset management arms: classify by dominant
  earnings driver. >50% from spread/underwriting → Financials. >50% from fees → Default.
- **Commodity-like tech** (DRAM): if pricing power is cyclical → consider Cyclical.
- **Platform companies** (Uber, Airbnb): Default — they earn take-rates, not spreads.

## Self-check
- [ ] The "trap" test for financials is explicitly applied
- [ ] The archetype is decisive, not "maybe X or Y"
- [ ] Downstream consequences (engine + drivers) are stated
